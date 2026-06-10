"""CICFlowMeter integration."""

from __future__ import annotations

from logging import Logger
from pathlib import Path

import pandas as pd
from cicflowmeter.flow_session import FlowSession
from scapy.sendrecv import AsyncSniffer

from src.config import settings


class CicFlowMeterError(RuntimeError):
    """Raised when CICFlowMeter cannot convert a PCAP to flow rows."""


def pcap_to_flows(
    pcap_path: Path,
    csv_path: Path,
    *,
    logger: Logger | None = None,
) -> pd.DataFrame:
    """Run CICFlowMeter against a PCAP file and return the generated flow rows.

    The packaged CLI currently mispasses positional arguments into create_sniffer,
    so the agent uses the Python API with keyword arguments instead.
    """
    csv_path.parent.mkdir(parents=True, exist_ok=True)

    if logger:
        logger.info("Running CICFlowMeter API: pcap=%s csv=%s", pcap_path, csv_path)

    try:
        session = FlowSession(
            output_mode="csv",
            output=str(csv_path),
            fields=None,
            verbose=settings.cicflowmeter_verbose,
        )
        sniffer = AsyncSniffer(
            offline=str(pcap_path),
            prn=session.process,
            store=False,
        )
        sniffer.start()
        sniffer.join(timeout=settings.cicflowmeter_timeout)
        if sniffer.running:
            sniffer.stop()
            raise CicFlowMeterError(
                f"CICFlowMeter timed out after {settings.cicflowmeter_timeout}s"
            )
        if hasattr(session, "_gc_stop"):
            session._gc_stop.set()
            session._gc_thread.join(timeout=2.0)
        session.flush_flows()
    except Exception as exc:
        if isinstance(exc, CicFlowMeterError):
            raise
        raise CicFlowMeterError(f"CICFlowMeter failed: {exc}") from exc

    if not csv_path.exists() or csv_path.stat().st_size == 0:
        return pd.DataFrame()

    return pd.read_csv(csv_path)
