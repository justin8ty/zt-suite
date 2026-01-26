from __future__ import annotations

import hashlib
import json
import math
from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

import pandas as pd

from .flow_fields import (
    NORM,
    attach_event_ts_utc,
    resolve_port_column,
    resolve_protocol_column,
)


@dataclass(frozen=True)
class AggregationConfig:
    window_secs: int = 60
    allowed_lateness_secs: int = 10
    group_bys: tuple[str, ...] = ("src_ip", "src_ip,dst_port")

    theta_flow: float = 0.25
    theta_ratio: float = 0.20
    min_flows: int = 50

    fanout_unique_dst_port: int = 30
    fanout_min_flows_per_sec: float = 0.5
    syn_min: int = 100
    rst_syn_ratio_min: float = 0.6


def _to_utc_dt(ts: pd.Timestamp) -> datetime:
    # `ts` is timezone-aware (UTC) by construction.
    return ts.to_pydatetime()


def _window_start(ts: pd.Timestamp, window_secs: int) -> pd.Timestamp:
    # Floor to window boundary.
    epoch = ts.value // 10**9
    start = (epoch // window_secs) * window_secs
    return pd.Timestamp(start, unit="s", tz="UTC")


def _group_key(
    group_by: str, row: pd.Series, dst_port_col: str | None
) -> tuple[str, dict[str, object]]:
    parts: list[str] = []
    fields: dict[str, object] = {
        "src_ip": pd.NA,
        "dst_ip": pd.NA,
        "dst_port": pd.NA,
        "protocol": pd.NA,
    }

    def add(name: str, value: object) -> None:
        parts.append(f"{name}={value}")

    if group_by == "src_ip":
        v = row.get("src_ip")
        fields["src_ip"] = v
        add("src_ip", v)
    elif group_by == "dst_ip":
        v = row.get("dst_ip")
        fields["dst_ip"] = v
        add("dst_ip", v)
    elif group_by == "src_ip,dst_ip":
        s = row.get("src_ip")
        d = row.get("dst_ip")
        fields["src_ip"] = s
        fields["dst_ip"] = d
        add("src_ip", s)
        add("dst_ip", d)
    elif group_by == "src_ip,dst_port":
        s = row.get("src_ip")
        dp = row.get(dst_port_col) if dst_port_col else pd.NA
        fields["src_ip"] = s
        fields["dst_port"] = dp
        add("src_ip", s)
        add("dst_port", dp)
    else:
        raise RuntimeError(f"Unsupported group_by: {group_by}")

    return "|".join(parts), fields


def _entropy_from_counter(counter: Counter[int]) -> float:
    total = sum(counter.values())
    if total <= 0:
        return 0.0
    ent = 0.0
    for c in counter.values():
        p = c / total
        ent -= p * math.log(p, 2)
    return float(ent)


def _safe_int(v: object) -> int:
    try:
        if pd.isna(v):
            return 0
    except Exception:
        pass
    try:
        return int(v)
    except Exception:
        return 0


def _safe_float(v: object) -> float:
    try:
        if pd.isna(v):
            return 0.0
    except Exception:
        pass
    try:
        return float(v)
    except Exception:
        return 0.0


class _WindowState:
    __slots__ = (
        "window_start",
        "window_end",
        "group_by",
        "group_key",
        "src_ip",
        "dst_ip",
        "dst_port",
        "protocol",
        "total_flows",
        "weak_anom_flows",
        "sum_score",
        "max_score",
        "bytes_total",
        "pkts_total",
        "unique_dst_ip",
        "unique_dst_port",
        "dst_port_counter",
        "syn_total",
        "rst_total",
        "first_seen_ts",
        "last_seen_ts",
        "late_dropped",
    )

    def __init__(
        self,
        window_start: pd.Timestamp,
        window_end: pd.Timestamp,
        group_by: str,
        group_key: str,
        fields: dict[str, object],
    ) -> None:
        self.window_start = window_start
        self.window_end = window_end
        self.group_by = group_by
        self.group_key = group_key
        self.src_ip = fields.get("src_ip", pd.NA)
        self.dst_ip = fields.get("dst_ip", pd.NA)
        self.dst_port = fields.get("dst_port", pd.NA)
        self.protocol = fields.get("protocol", pd.NA)

        self.total_flows = 0
        self.weak_anom_flows = 0
        self.sum_score = 0.0
        self.max_score = 0.0
        self.bytes_total = 0.0
        self.pkts_total = 0.0
        self.unique_dst_ip: set[str] = set()
        self.unique_dst_port: set[int] = set()
        self.dst_port_counter: Counter[int] = Counter()
        self.syn_total = 0
        self.rst_total = 0
        self.first_seen_ts: pd.Timestamp | None = None
        self.last_seen_ts: pd.Timestamp | None = None
        self.late_dropped = 0


class AggregationEngine:
    def __init__(self, cfg: AggregationConfig) -> None:
        self.cfg = cfg
        self._states: dict[tuple[pd.Timestamp, str, str], _WindowState] = {}
        self._max_event_ts: pd.Timestamp | None = None

    def update(
        self, row: pd.Series, dst_port_col: str | None, protocol_col: str | None
    ) -> None:
        ts = row.get(NORM.event_ts)
        if not isinstance(ts, pd.Timestamp) or pd.isna(ts):
            return

        if self._max_event_ts is None or ts > self._max_event_ts:
            self._max_event_ts = ts

        # Lateness check (relative to watermark)
        watermark = self._max_event_ts
        allowed = pd.Timedelta(seconds=self.cfg.allowed_lateness_secs)

        ws = _window_start(ts, self.cfg.window_secs)
        we = ws + pd.Timedelta(seconds=self.cfg.window_secs)
        if ts < (watermark - allowed) and we <= (watermark - allowed):
            # Too late for an already finalizable window.
            return

        for group_by in self.cfg.group_bys:
            group_key, fields = _group_key(group_by, row, dst_port_col)
            if protocol_col is not None:
                fields["protocol"] = row.get(protocol_col)
            key = (ws, group_by, group_key)
            st = self._states.get(key)
            if st is None:
                st = _WindowState(ws, we, group_by, group_key, fields)
                self._states[key] = st

            st.total_flows += 1

            score = _safe_float(row.get("malicious_score"))
            st.sum_score += score
            if score > st.max_score:
                st.max_score = score
            if score >= self.cfg.theta_flow:
                st.weak_anom_flows += 1

            # Bytes/packets totals (prefer explicit totals)
            bytes_total = _safe_float(row.get("totlen_fwd_pkts")) + _safe_float(
                row.get("totlen_bwd_pkts")
            )
            pkts_total = _safe_float(row.get("tot_fwd_pkts")) + _safe_float(
                row.get("tot_bwd_pkts")
            )
            st.bytes_total += bytes_total
            st.pkts_total += pkts_total

            dip = row.get("dst_ip")
            if isinstance(dip, str) and dip:
                st.unique_dst_ip.add(dip)

            if dst_port_col is not None:
                dp = _safe_int(row.get(dst_port_col))
                if dp > 0:
                    st.unique_dst_port.add(dp)
                    st.dst_port_counter[dp] += 1

            st.syn_total += _safe_int(row.get("syn_flag_cnt"))
            st.rst_total += _safe_int(row.get("rst_flag_cnt"))

            if st.first_seen_ts is None or ts < st.first_seen_ts:
                st.first_seen_ts = ts
            if st.last_seen_ts is None or ts > st.last_seen_ts:
                st.last_seen_ts = ts

    def flush_ready(self) -> tuple[list[dict[str, object]], list[dict[str, object]]]:
        if self._max_event_ts is None:
            return [], []

        watermark = self._max_event_ts
        allowed = pd.Timedelta(seconds=self.cfg.allowed_lateness_secs)
        cutoff = watermark - allowed

        windows_out: list[dict[str, object]] = []
        alerts_out: list[dict[str, object]] = []

        # Finalize windows whose end is older than cutoff.
        keys_to_finalize = [
            k for k, st in self._states.items() if st.window_end <= cutoff
        ]
        for key in keys_to_finalize:
            st = self._states.pop(key)
            win_row = window_state_to_row(st, self.cfg)
            windows_out.append(win_row)
            alerts_out.extend(alerts_for_window(win_row, st))

        return windows_out, alerts_out

    def flush_all(self) -> tuple[list[dict[str, object]], list[dict[str, object]]]:
        windows_out: list[dict[str, object]] = []
        alerts_out: list[dict[str, object]] = []
        for st in list(self._states.values()):
            win_row = window_state_to_row(st, self.cfg)
            windows_out.append(win_row)
            alerts_out.extend(alerts_for_window(win_row, st))
        self._states.clear()
        return windows_out, alerts_out


def window_state_to_row(st: _WindowState, cfg: AggregationConfig) -> dict[str, object]:
    total = st.total_flows
    weak = st.weak_anom_flows
    mean_score = (st.sum_score / total) if total else 0.0

    flows_per_sec = total / cfg.window_secs
    bytes_per_sec = st.bytes_total / cfg.window_secs
    pkts_per_sec = st.pkts_total / cfg.window_secs

    entropy_dst_port = _entropy_from_counter(st.dst_port_counter)
    rst_syn_ratio = st.rst_total / max(st.syn_total, 1)

    return {
        "window_start": st.window_start,
        "window_end": st.window_end,
        "window_secs": cfg.window_secs,
        "group_by": st.group_by,
        "group_key": st.group_key,
        "src_ip": st.src_ip,
        "dst_ip": st.dst_ip,
        "dst_port": st.dst_port,
        "protocol": st.protocol,
        "total_flows": int(total),
        "weak_anom_flows": int(weak),
        "weak_anom_ratio": float(weak / total) if total else 0.0,
        "mean_score": float(mean_score),
        "max_score": float(st.max_score),
        "bytes_total": float(st.bytes_total),
        "bytes_per_sec": float(bytes_per_sec),
        "pkts_total": float(st.pkts_total),
        "pkts_per_sec": float(pkts_per_sec),
        "flows_per_sec": float(flows_per_sec),
        "unique_dst_ip": int(len(st.unique_dst_ip)),
        "unique_dst_port": int(len(st.unique_dst_port)),
        "entropy_dst_port": float(entropy_dst_port),
        "syn_total": int(st.syn_total),
        "rst_total": int(st.rst_total),
        "rst_syn_ratio": float(rst_syn_ratio),
        "first_seen_ts": st.first_seen_ts,
        "last_seen_ts": st.last_seen_ts,
        "late_dropped": int(st.late_dropped),
        "theta_flow": float(cfg.theta_flow),
        "theta_ratio": float(cfg.theta_ratio),
        "min_flows": int(cfg.min_flows),
    }


def _alert_id(
    window_start: pd.Timestamp, group_by: str, group_key: str, rule_ids: list[str]
) -> str:
    raw = f"{window_start.isoformat()}|{group_by}|{group_key}|{','.join(sorted(rule_ids))}".encode(
        "utf-8"
    )
    return hashlib.sha1(raw).hexdigest()


def alerts_for_window(
    win_row: dict[str, object], st: _WindowState
) -> list[dict[str, object]]:
    cfg_theta_ratio = float(win_row.get("theta_ratio", 0.2))
    cfg_min_flows = int(win_row.get("min_flows", 50))
    total = int(win_row.get("total_flows", 0))
    ratio = float(win_row.get("weak_anom_ratio", 0.0))

    flows_per_sec = float(win_row.get("flows_per_sec", 0.0))
    unique_dst_port = int(win_row.get("unique_dst_port", 0))
    syn_total = int(win_row.get("syn_total", 0))
    rst_syn_ratio = float(win_row.get("rst_syn_ratio", 0.0))

    rule_ids: list[str] = []
    reasons: list[str] = []

    if total >= cfg_min_flows and ratio >= cfg_theta_ratio:
        rule_ids.append("campaign_ratio")
        reasons.append(f"weak_anom_ratio={ratio:.3f} over {total} flows")

    # Fan-out heuristic: many dst ports in short time.
    fanout_ports = 30
    fanout_min_fps = 0.5
    if unique_dst_port >= fanout_ports and flows_per_sec >= fanout_min_fps:
        rule_ids.append("fanout_ports")
        reasons.append(f"unique_dst_port={unique_dst_port} at {flows_per_sec:.2f} fps")

    # SYN/RST instability heuristic.
    if syn_total >= 100 and rst_syn_ratio >= 0.6:
        rule_ids.append("syn_rst_instability")
        reasons.append(f"syn_total={syn_total}, rst_syn_ratio={rst_syn_ratio:.2f}")

    if not rule_ids:
        return []

    top_ports = [
        {"dst_port": int(p), "count": int(c)}
        for p, c in st.dst_port_counter.most_common(5)
    ]
    # dst_ip counts are not tracked as a Counter right now; approximate via empty list.
    top_ips: list[dict[str, object]] = []

    # Severity/confidence: simple mapping, can be replaced later.
    severity = min(5, 1 + len(rule_ids))
    confidence = min(1.0, 0.55 + 0.15 * len(rule_ids))

    window_start = win_row["window_start"]
    alert_id = _alert_id(
        window_start, str(win_row["group_by"]), str(win_row["group_key"]), rule_ids
    )

    alert_ts = win_row.get("window_end")
    return [
        {
            "alert_id": alert_id,
            "alert_ts": alert_ts,
            **{
                k: win_row.get(k)
                for k in (
                    "window_start",
                    "window_end",
                    "window_secs",
                    "group_by",
                    "group_key",
                    "src_ip",
                    "dst_ip",
                    "dst_port",
                    "protocol",
                    "total_flows",
                    "weak_anom_flows",
                    "weak_anom_ratio",
                    "mean_score",
                    "max_score",
                    "flows_per_sec",
                    "bytes_per_sec",
                    "pkts_per_sec",
                    "unique_dst_ip",
                    "unique_dst_port",
                    "entropy_dst_port",
                    "syn_total",
                    "rst_total",
                    "rst_syn_ratio",
                    "theta_flow",
                    "theta_ratio",
                    "min_flows",
                )
            },
            "severity": int(severity),
            "confidence": float(confidence),
            "rule_ids": json.dumps(rule_ids, separators=(",", ":")),
            "reason": "; ".join(reasons),
            "top_dst_ports": json.dumps(top_ports, separators=(",", ":")),
            "top_dst_ips": json.dumps(top_ips, separators=(",", ":")),
        }
    ]


def aggregate_scored_flows(
    df_scored: pd.DataFrame,
    cfg: AggregationConfig,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Batch aggregation helper for CSV inference output."""

    df = attach_event_ts_utc(
        df_scored, timestamp_col="timestamp", out_col=NORM.event_ts
    )
    df = df.dropna(subset=[NORM.event_ts]).copy()
    if len(df) == 0:
        return pd.DataFrame(), pd.DataFrame()

    dst_port_col = resolve_port_column(df)
    protocol_col = resolve_protocol_column(df)

    engine = AggregationEngine(cfg)
    # Sort for deterministic batch behavior and correct window flushing.
    df = df.sort_values(NORM.event_ts)

    windows_accum: list[dict[str, object]] = []
    alerts_accum: list[dict[str, object]] = []
    for _, row in df.iterrows():
        engine.update(row, dst_port_col=dst_port_col, protocol_col=protocol_col)
        w, a = engine.flush_ready()
        windows_accum.extend(w)
        alerts_accum.extend(a)

    w, a = engine.flush_all()
    windows_accum.extend(w)
    alerts_accum.extend(a)

    return pd.DataFrame(windows_accum), pd.DataFrame(alerts_accum)
