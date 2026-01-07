"""Network traffic capture collector using Scapy."""

import ipaddress
from collections.abc import Callable
from datetime import datetime, timezone
from threading import Event, Thread
from typing import Final

from scapy.layers.inet import IP, TCP, UDP
from scapy.layers.inet6 import IPv6
from scapy.packet import Packet
from scapy.sendrecv import sniff

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

    def __init__(self) -> None:
        """Initialize the traffic collector."""
        self._stop_event = Event()
        self._thread: Thread | None = None

    @property
    def is_running(self) -> bool:
        """Check if the collector is currently capturing."""
        return self._thread is not None and self._thread.is_alive()

    def _parse_packet(self, packet: Packet) -> TrafficRecord | None:
        """Parse a captured packet and extract metadata.

        Returns None if packet should be skipped (excluded network,
        fragmented, missing required layers, etc.)
        """
        # Skip fragmented packets (non-first fragments lack port info)
        if _is_fragmented(packet):
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
            return None

        # Check for excluded networks
        if _is_excluded_ip(src_ip) or _is_excluded_ip(dst_ip):
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
            return None

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

        # BPF filter: only TCP and UDP traffic
        # Additional filtering (localhost, multicast) done in Python
        sniff(
            iface=interface,
            filter="tcp or udp",
            prn=packet_handler,
            stop_filter=lambda _: self._stop_event.is_set(),
            store=False,  # Don't accumulate packets in memory
        )

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
