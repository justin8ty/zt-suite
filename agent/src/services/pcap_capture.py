"""PCAP window capture for flow-based monitoring."""

from __future__ import annotations

from logging import Logger
from pathlib import Path

from scapy.all import get_if_list
from scapy.packet import Packet
from scapy.sendrecv import sniff
from scapy.utils import PcapWriter

from src.config import settings


def capture_pcap_window(
    output_path: Path,
    *,
    duration_seconds: int,
    interface: str | None,
    logger: Logger | None = None,
) -> int:
    """Capture one bounded TCP/UDP PCAP window and return packet count."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    packet_count = 0
    bpf_filter = _bpf_filter()

    if logger:
        logger.info(
            "Capturing PCAP window: path=%s duration=%ss interface=%s filter=%s",
            output_path,
            duration_seconds,
            interface or "all interfaces",
            bpf_filter,
        )
        available_interfaces = list(get_if_list())
        logger.info(
            "Available Scapy interfaces: %s",
            ", ".join(available_interfaces) if available_interfaces else "none",
        )
        if interface and interface not in available_interfaces:
            logger.warning("Configured interface not found in Scapy interface list: %s", interface)

    writer = PcapWriter(str(output_path), append=False, sync=True)

    def packet_handler(packet: Packet) -> None:
        nonlocal packet_count
        writer.write(packet)
        packet_count += 1

    try:
        sniff(
            iface=interface,
            filter=bpf_filter,
            prn=packet_handler,
            timeout=duration_seconds,
            store=False,
        )
    finally:
        writer.close()

    return packet_count


def _bpf_filter() -> str:
    base = "tcp or udp"
    if settings.target_ip:
        return f"({base}) and host {settings.target_ip}"
    return base
