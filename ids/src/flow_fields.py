from __future__ import annotations

from dataclasses import dataclass

import pandas as pd


@dataclass(frozen=True)
class NormalizedFlowColumns:
    event_ts: str = "event_ts"
    src_ip: str = "src_ip"
    dst_ip: str = "dst_ip"
    src_port: str = "src_port"
    dst_port: str = "dst_port"
    protocol: str = "protocol"


NORM = NormalizedFlowColumns()


def _first_existing(df: pd.DataFrame, *candidates: str) -> str | None:
    for c in candidates:
        if c in df.columns:
            return c
    return None


def attach_event_ts_utc(
    df: pd.DataFrame,
    timestamp_col: str = "timestamp",
    out_col: str = NORM.event_ts,
) -> pd.DataFrame:
    """Parse timestamp like '2026-01-25 18:09:28' as UTC.

    Creates/overwrites `out_col`.
    """

    out = df.copy()
    if timestamp_col not in out.columns:
        out[out_col] = pd.NaT
        return out

    out[out_col] = pd.to_datetime(
        out[timestamp_col],
        format="%Y-%m-%d %H:%M:%S",
        utc=True,
        errors="coerce",
    )
    return out


def resolve_port_column(df: pd.DataFrame) -> str | None:
    """Find dst port column regardless of inference/training naming."""

    return _first_existing(df, "dst_port", "Dst Port")


def resolve_protocol_column(df: pd.DataFrame) -> str | None:
    return _first_existing(df, "protocol", "Protocol")


def require_columns(df: pd.DataFrame, cols: list[str]) -> None:
    missing = [c for c in cols if c not in df.columns]
    if missing:
        raise RuntimeError(f"Missing required columns: {missing}")
