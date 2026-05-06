"""Endpoint posture collector."""

from __future__ import annotations

import platform
import shutil
import socket
import subprocess
import time
from collections.abc import Callable
from datetime import datetime, timezone
from logging import Logger

import psutil

from src.config import settings
from src.models.posture import NetworkInterface, PostureReport, SecurityStatus
from src.services.identity import get_agent_id


class PostureCollector:
    """Collects best-effort endpoint posture information."""

    def __init__(self, logger: Logger | None = None) -> None:
        self._logger = logger

    def collect(self) -> PostureReport:
        """Collect and return a validated posture report."""
        boot_timestamp = psutil.boot_time()
        boot_time = datetime.fromtimestamp(boot_timestamp, tz=timezone.utc)
        now = datetime.now(timezone.utc)

        return PostureReport(
            agent_id=get_agent_id(),
            hostname=socket.gethostname(),
            os_name=platform.system(),
            os_version=_os_version(),
            architecture=platform.machine(),
            uptime_seconds=max(0, int(time.time() - boot_timestamp)),
            boot_time=boot_time,
            collected_at=now,
            agent_version=settings.agent_version,
            network_interfaces=self._collect_network_interfaces(),
            security=self._collect_security_status(),
        )

    def _collect_network_interfaces(self) -> list[NetworkInterface]:
        addrs = psutil.net_if_addrs()
        stats = psutil.net_if_stats()
        interfaces: list[NetworkInterface] = []

        for name, addresses in addrs.items():
            ip_addresses: list[str] = []
            mac_address: str | None = None

            for addr in addresses:
                family_name = getattr(addr.family, "name", str(addr.family))
                if family_name in {"AF_INET", "AF_INET6"}:
                    ip_addresses.append(addr.address)
                elif family_name in {"AF_LINK", "AF_PACKET"}:
                    mac_address = addr.address

            interface_stats = stats.get(name)
            interfaces.append(
                NetworkInterface(
                    name=name,
                    ip_addresses=ip_addresses,
                    mac_address=mac_address,
                    is_up=interface_stats.isup if interface_stats else False,
                )
            )

        return interfaces

    def _collect_security_status(self) -> SecurityStatus:
        os_name = platform.system().lower()

        if os_name == "windows":
            return SecurityStatus(
                firewall_enabled=self._safe_check("windows_firewall", _windows_firewall_enabled),
                antivirus_present=self._safe_check("windows_antivirus", _windows_antivirus_present),
                disk_encryption_enabled=self._safe_check(
                    "windows_disk_encryption", _windows_disk_encryption_enabled
                ),
                updates_available=None,
            )

        if os_name == "linux":
            return SecurityStatus(
                firewall_enabled=self._safe_check("linux_firewall", _linux_firewall_enabled),
                antivirus_present=self._safe_check("linux_antivirus", _linux_antivirus_present),
                disk_encryption_enabled=self._safe_check(
                    "linux_disk_encryption", _linux_disk_encryption_enabled
                ),
                updates_available=None,
            )

        return SecurityStatus()

    def _safe_check(self, check_name: str, check: CallableCheck) -> bool | None:
        try:
            return check()
        except Exception as exc:  # noqa: BLE001 - posture checks are best-effort.
            if self._logger:
                self._logger.warning("Posture check unavailable: %s (%s)", check_name, exc)
            return None


CallableCheck = Callable[[], bool | None]


def _os_version() -> str:
    parts = [platform.release(), platform.version()]
    return " ".join(part for part in parts if part).strip()


def _run_command(command: list[str], timeout: int = 5) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        capture_output=True,
        text=True,
        timeout=timeout,
        check=False,
    )


def _run_powershell(command: str, timeout: int = 8) -> subprocess.CompletedProcess[str]:
    powershell = shutil.which("powershell") or shutil.which("pwsh")
    if powershell is None:
        raise RuntimeError("PowerShell unavailable")
    return _run_command(
        [powershell, "-NoProfile", "-NonInteractive", "-Command", command],
        timeout=timeout,
    )


def _windows_firewall_enabled() -> bool | None:
    result = _run_powershell(
        "(Get-NetFirewallProfile | Select-Object -ExpandProperty Enabled) -join ','"
    )
    if result.returncode != 0:
        return None
    values = [value.strip().lower() for value in result.stdout.split(",") if value.strip()]
    if not values:
        return None
    return all(value == "true" for value in values)


def _windows_antivirus_present() -> bool | None:
    result = _run_powershell(
        "Get-CimInstance -Namespace root/SecurityCenter2 -ClassName AntiVirusProduct "
        "| Select-Object -First 1 -ExpandProperty displayName"
    )
    if result.returncode != 0:
        return None
    return bool(result.stdout.strip())


def _windows_disk_encryption_enabled() -> bool | None:
    manage_bde = shutil.which("manage-bde")
    if manage_bde is None:
        return None
    result = _run_command([manage_bde, "-status"], timeout=10)
    if result.returncode != 0:
        return None
    output = result.stdout.lower()
    if "protection status" not in output:
        return None
    return "protection on" in output


def _linux_firewall_enabled() -> bool | None:
    ufw = shutil.which("ufw")
    if ufw is not None:
        result = _run_command([ufw, "status"])
        output = result.stdout.lower()
        if "status: active" in output:
            return True
        if "status: inactive" in output:
            return False

    firewall_cmd = shutil.which("firewall-cmd")
    if firewall_cmd is not None:
        result = _run_command([firewall_cmd, "--state"])
        output = result.stdout.strip().lower()
        if output == "running":
            return True
        if output in {"not running", "failed"}:
            return False

    return None


def _linux_antivirus_present() -> bool | None:
    process_names = {proc.info.get("name", "").lower() for proc in psutil.process_iter(["name"])}
    known_processes = {"clamd", "freshclam", "clamscan", "savd"}
    if process_names & known_processes:
        return True

    known_binaries = ("clamd", "clamscan", "freshclam")
    if any(shutil.which(binary) for binary in known_binaries):
        return True

    return False


def _linux_disk_encryption_enabled() -> bool | None:
    lsblk = shutil.which("lsblk")
    if lsblk is None:
        return None
    result = _run_command([lsblk, "-o", "TYPE", "-nr"])
    if result.returncode != 0:
        return None
    types = {line.strip().lower() for line in result.stdout.splitlines() if line.strip()}
    return "crypt" in types
