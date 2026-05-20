"""Network traffic capture collector using Scapy."""

import ipaddress
import logging
from collections.abc import Callable
from datetime import datetime, timezone
from threading import Event, Thread
from typing import Final

from scapy.layers.inet import IP, TCP, UDP
from scapy.layers.inet6 import IPv6
from scapy.all import get_if_list
from scapy.packet import Packet
from scapy.sendrecv import sniff

from src.config import settings
from src.models.traffic import TCPFlags, TrafficRecord

# Networks to exclude from capture
# These generate noise not useful for endpoint anomaly detection
_EXCLUDED_NETWORKS: Final[list[ipaddress.IPv4Network | ipaddress.IPv6Network]] = [
    # IPv4
    ipaddress.ip_network("127.0.0.0/8"),  # Loopback
    ipaddress.ip_network("169.254.0.0/16"),  # Link-local (APIPA)
    ipaddress.ip_network("224.0.0.0/4"),  # Multicast
    ipaddress.ip_network("255.255.255.255/32"),  # Broadcast
    # IPv6
    ipaddress.ip_network("::1/128"),  # Loopback
    ipaddress.ip_network("fe80::/10"),  # Link-local
    ipaddress.ip_network("ff00::/8"),  # Multicast
]


def _is_excluded_ip(ip: str) -> bool:
    """Check if an IP address should be excluded from capture."""
    try:
        addr = ipaddress.ip_address(ip)
        return any(addr in network for network in _EXCLUDED_NETWORKS)
    except ValueError:
        # Invalid IP address format - exclude it
        return True


def _is_fragmented(packet: Packet) -> bool:
    """Check if packet is a non-first IP fragment (lacks transport headers)."""
    if packet.haslayer(IP):
        ip_layer = packet[IP]
        # frag field contains fragment offset (in 8-byte units)
        # If offset > 0, this is not the first fragment
        return ip_layer.frag > 0
    if packet.haslayer(IPv6):
        # IPv6 fragmentation is handled via extension headers
        # For simplicity, we don't handle IPv6 fragments specially
        # The fragment header would need to be parsed
        return False
    return False


def _extract_tcp_flags(tcp_layer: TCP) -> TCPFlags:
    """Extract TCP flags from packet."""
    flags = tcp_layer.flags
    return TCPFlags(
        syn=bool(flags & 0x02),
        ack=bool(flags & 0x10),
        fin=bool(flags & 0x01),
        rst=bool(flags & 0x04),
        psh=bool(flags & 0x08),
        urg=bool(flags & 0x20),
    )


def list_capture_interfaces() -> list[str]:
    """Return Scapy capture interface names."""
    return list(get_if_list())


class TrafficCollector:
    """Captures network traffic and extracts metadata for anomaly detection.

    Captures TCP and UDP traffic, excluding:
    - Localhost traffic (127.0.0.0/8, ::1)
    - Link-local traffic (169.254.0.0/16, fe80::/10)
    - Broadcast and multicast traffic
    - Fragmented packets (except first fragment)

    Requires root/administrator privileges to capture packets.

    Usage:
        collector = TrafficCollector()

        def handle_record(record: TrafficRecord) -> None:
            print(record.model_dump_json())

        collector.start(callback=handle_record)
        # ... capture runs in background ...
        collector.stop()
    """

    def __init__(self, logger: logging.Logger | None = None) -> None:
        """Initialize the traffic collector."""
        self._stop_event = Event()
        self._thread: Thread | None = None
        self._logger = logger
        self._seen_packets = 0
        self._emitted_records = 0
        self._skipped_no_ip = 0
        self._skipped_excluded_ip = 0
        self._skipped_target_ip = 0
        self._skipped_no_transport = 0
        self._skipped_fragmented = 0

    @property
    def is_running(self) -> bool:
        """Check if the collector is currently capturing."""
        return self._thread is not None and self._thread.is_alive()

    def stats(self) -> dict[str, int]:
        """Return current capture counters for diagnostics."""
        return {
            "seen_packets": self._seen_packets,
            "emitted_records": self._emitted_records,
            "skipped_no_ip": self._skipped_no_ip,
            "skipped_excluded_ip": self._skipped_excluded_ip,
            "skipped_target_ip": self._skipped_target_ip,
            "skipped_no_transport": self._skipped_no_transport,
            "skipped_fragmented": self._skipped_fragmented,
        }

    def _parse_packet(self, packet: Packet) -> TrafficRecord | None:
        """Parse a captured packet and extract metadata.

        Returns None if packet should be skipped (excluded network,
        fragmented, missing required layers, etc.)
        """
        self._seen_packets += 1

        # Skip fragmented packets (non-first fragments lack port info)
        if _is_fragmented(packet):
            self._skipped_fragmented += 1
            return None

        # Extract IP layer (IPv4 or IPv6)
        if packet.haslayer(IP):
            ip_layer = packet[IP]
            src_ip = ip_layer.src
            dst_ip = ip_layer.dst
        elif packet.haslayer(IPv6):
            ip_layer = packet[IPv6]
            src_ip = ip_layer.src
            dst_ip = ip_layer.dst
        else:
            # No IP layer - skip
            self._skipped_no_ip += 1
            return None

        # Check for excluded networks
        if _is_excluded_ip(src_ip) or _is_excluded_ip(dst_ip):
            self._skipped_excluded_ip += 1
            return None

        # Filter by target IP if configured (e.g., only host-VM traffic)
        if settings.target_ip:
            if src_ip != settings.target_ip and dst_ip != settings.target_ip:
                self._skipped_target_ip += 1
                return None

        # Extract transport layer (TCP or UDP)
        if packet.haslayer(TCP):
            transport_layer = packet[TCP]
            protocol = "TCP"
            tcp_flags = _extract_tcp_flags(transport_layer)
        elif packet.haslayer(UDP):
            transport_layer = packet[UDP]
            protocol = "UDP"
            tcp_flags = None
        else:
            # No TCP/UDP layer - skip
            self._skipped_no_transport += 1
            return None

        self._emitted_records += 1
        return TrafficRecord(
            timestamp=datetime.now(timezone.utc),
            src_ip=src_ip,
            dst_ip=dst_ip,
            src_port=transport_layer.sport,
            dst_port=transport_layer.dport,
            protocol=protocol,
            packet_size=len(packet),
            tcp_flags=tcp_flags,
        )

    def _capture_loop(
        self,
        callback: Callable[[TrafficRecord], None],
        interface: str | None,
    ) -> None:
        """Main capture loop running in separate thread."""

        def packet_handler(packet: Packet) -> None:
            record = self._parse_packet(packet)
            if record is not None:
                callback(record)

        if self._logger:
            self._logger.info(
                "Scapy sniff starting: interface=%s, bpf_filter=%s, target_ip=%s",
                interface or "all interfaces",
                "tcp or udp",
                settings.target_ip or "none",
            )

        # BPF filter: only TCP and UDP traffic
        # Additional filtering (localhost, multicast) done in Python
        try:
            sniff(
                iface=interface,
                filter="tcp or udp",
                prn=packet_handler,
                stop_filter=lambda _: self._stop_event.is_set(),
                store=False,  # Don't accumulate packets in memory
            )
        except Exception:
            if self._logger:
                self._logger.exception(
                    "Scapy sniff failed. Check Admin/root privileges, Npcap/libpcap, "
                    "and ZT_AGENT_INTERFACE."
                )
            self._stop_event.set()

    def start(
        self,
        callback: Callable[[TrafficRecord], None],
        interface: str | None = None,
    ) -> None:
        """Start capturing network traffic.

        Args:
            callback: Function called for each captured TrafficRecord.
            interface: Network interface to capture on. None = all interfaces.

        Raises:
            RuntimeError: If collector is already running.
            PermissionError: If lacking privileges for packet capture.
        """
        if self.is_running:
            raise RuntimeError("Traffic collector is already running")

        if self._logger:
            available_interfaces = list_capture_interfaces()
            self._logger.info(
                "Traffic collector configured: interface=%s, target_ip=%s",
                interface or "all interfaces",
                settings.target_ip or "none",
            )
            self._logger.info(
                "Available Scapy interfaces: %s",
                ", ".join(available_interfaces) if available_interfaces else "none",
            )
            if interface and interface not in available_interfaces:
                self._logger.warning(
                    "Configured interface not found in Scapy interface list: %s",
                    interface,
                )

        self._stop_event.clear()
        self._thread = Thread(
            target=self._capture_loop,
            args=(callback, interface),
            daemon=True,
            name="traffic-collector",
        )
        self._thread.start()

    def stop(self, timeout: float = 5.0) -> None:
        """Stop capturing network traffic.

        Args:
            timeout: Maximum seconds to wait for capture thread to stop.
        """
        self._stop_event.set()
        if self._thread is not None:
            self._thread.join(timeout=timeout)
            self._thread = None

        if self._logger:
            self._logger.info(
                "Traffic collector stats: seen_packets=%s, emitted_records=%s, "
                "skipped_no_ip=%s, skipped_excluded_ip=%s, skipped_target_ip=%s, "
                "skipped_no_transport=%s, skipped_fragmented=%s",
                self._seen_packets,
                self._emitted_records,
                self._skipped_no_ip,
                self._skipped_excluded_ip,
                self._skipped_target_ip,
                self._skipped_no_transport,
                self._skipped_fragmented,
            )
