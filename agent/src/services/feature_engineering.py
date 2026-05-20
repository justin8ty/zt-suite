"""Feature engineering for traffic batches."""

from datetime import datetime, timezone

from src.models.features import TrafficFeatureVector
from src.models.traffic import TrafficRecord


_MIN_EPHEMERAL_PORT = 49152
_MAX_PORT = 65535


def build_features(
    records: list[TrafficRecord],
    *,
    agent_id: str,
    batch_id: str,
) -> TrafficFeatureVector:
    """Build one feature vector from a flushed traffic batch."""
    if not records:
        now = datetime.now(timezone.utc)
        return TrafficFeatureVector(
            agent_id=agent_id,
            batch_id=batch_id,
            window_start=now,
            window_end=now,
            duration_seconds=0.0,
            packet_count=0,
            byte_count=0,
            packets_per_minute=0.0,
            bytes_per_minute=0.0,
            unique_dst_ip_count=0,
            unique_dst_port_count=0,
            average_packet_size=0.0,
            tcp_packet_count=0,
            udp_packet_count=0,
            syn_ratio=0.0,
            ack_ratio=0.0,
            fin_ratio=0.0,
            rst_ratio=0.0,
            psh_ratio=0.0,
            urg_ratio=0.0,
            well_known_port_ratio=0.0,
            ephemeral_port_ratio=0.0,
        )

    timestamps = [record.timestamp for record in records]
    window_start = min(timestamps)
    window_end = max(timestamps)
    duration_seconds = max((window_end - window_start).total_seconds(), 1.0)

    packet_count = len(records)
    byte_count = sum(record.packet_size for record in records)
    tcp_records = [record for record in records if record.protocol == "TCP"]
    udp_packet_count = packet_count - len(tcp_records)

    dst_ports = [record.dst_port for record in records]
    well_known_count = sum(1 for port in dst_ports if 0 <= port <= 1023)
    ephemeral_count = sum(1 for port in dst_ports if _MIN_EPHEMERAL_PORT <= port <= _MAX_PORT)

    return TrafficFeatureVector(
        agent_id=agent_id,
        batch_id=batch_id,
        window_start=window_start,
        window_end=window_end,
        duration_seconds=duration_seconds,
        packet_count=packet_count,
        byte_count=byte_count,
        packets_per_minute=packet_count / duration_seconds * 60,
        bytes_per_minute=byte_count / duration_seconds * 60,
        unique_dst_ip_count=len({record.dst_ip for record in records}),
        unique_dst_port_count=len(set(dst_ports)),
        average_packet_size=byte_count / packet_count,
        tcp_packet_count=len(tcp_records),
        udp_packet_count=udp_packet_count,
        syn_ratio=_tcp_flag_ratio(tcp_records, "syn"),
        ack_ratio=_tcp_flag_ratio(tcp_records, "ack"),
        fin_ratio=_tcp_flag_ratio(tcp_records, "fin"),
        rst_ratio=_tcp_flag_ratio(tcp_records, "rst"),
        psh_ratio=_tcp_flag_ratio(tcp_records, "psh"),
        urg_ratio=_tcp_flag_ratio(tcp_records, "urg"),
        well_known_port_ratio=well_known_count / packet_count,
        ephemeral_port_ratio=ephemeral_count / packet_count,
    )


def _tcp_flag_ratio(records: list[TrafficRecord], flag_name: str) -> float:
    if not records:
        return 0.0

    flag_count = 0
    for record in records:
        if record.tcp_flags is not None and getattr(record.tcp_flags, flag_name):
            flag_count += 1

    return flag_count / len(records)
