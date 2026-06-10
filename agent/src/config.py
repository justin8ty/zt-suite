"""Agent configuration settings."""

from typing import Any, Literal

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Configuration for the traffic capture agent.

    Settings are loaded from environment variables or a .env file.
    Environment variables are prefixed with ZT_AGENT_ (e.g., ZT_AGENT_INTERFACE).
    """

    model_config = SettingsConfigDict(
        env_prefix="ZT_AGENT_",
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # Network capture settings
    traffic_mode: Literal["flow", "packet"] = "flow"
    """Network monitoring mode.

    flow = CICFlowMeter-backed IDS path; packet = legacy Scapy packet batches.
    """

    interface: str | None = None
    """Network interface to capture on. None = all interfaces."""

    target_ip: str | None = None
    """Filter traffic to/from this IP only (e.g., host IP). None = capture all traffic."""

    # Logging settings
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "INFO"
    """Logging level for agent logs (output to stderr)."""

    # Output settings
    output_mode: Literal["stdout", "file", "none"] = "file"
    """Where to output captured traffic records."""

    output_file: str = "./traffic.jsonl"
    """File path for traffic records when output_mode=file."""

    batch_interval: int = 60
    """Interval in seconds to batch traffic records before output."""

    batch_size_soft_limit: int = 50_000
    """Record count that triggers an emergency traffic batch flush."""

    batch_size_hard_limit: int = 100_000
    """Maximum queued traffic records before new records are dropped."""

    # Agent identity and posture settings
    agent_id: str | None = None
    """Stable agent ID. If unset, generated and persisted locally."""

    agent_version: str = "0.1.0"
    """Agent version included in posture reports."""

    agent_state_dir: str = "./data"
    """Directory for local agent state such as generated agent ID."""

    posture_enabled: bool = True
    """Whether periodic endpoint posture collection is enabled."""

    posture_interval: int = 300
    """Interval in seconds between posture reports."""

    posture_output_file: str = "./posture.jsonl"
    """File path for posture reports when output_mode=file."""

    feature_output_file: str = "./features.jsonl"
    """File path for engineered traffic features when output_mode=file."""

    anomaly_enabled: bool = True
    """Whether local anomaly detection is enabled."""

    anomaly_model_path: str = "./src/ml/anomaly_model.joblib"
    """Path to legacy packet-batch anomaly model artifact."""

    anomaly_threshold: float = 0.7
    """Score threshold for generating local alerts."""

    flow_model_path: str = "../ids/models/mlp.joblib"
    """Path to CICFlowMeter-compatible IDS model artifact used in flow mode."""

    flow_scaler_path: str = "../ids/models/scaler.joblib"
    """Path to scaler artifact paired with the flow IDS model."""

    flow_prediction_threshold: float = 0.35
    """Malicious score threshold for flow-model alerts."""

    flow_window_interval: int = 60
    """Seconds of traffic captured per PCAP window before CICFlowMeter conversion."""

    flow_work_dir: str = "./data/flow-windows"
    """Directory for transient PCAP and CICFlowMeter CSV files."""

    flow_keep_artifacts: bool = False
    """Whether to keep per-window PCAP/CSV artifacts after processing."""

    cicflowmeter_command: str = "cicflowmeter"
    """CICFlowMeter CLI command or absolute executable path."""

    cicflowmeter_timeout: int = 120
    """Maximum seconds allowed for one CICFlowMeter PCAP conversion."""

    cicflowmeter_verbose: bool = False
    """Whether to pass -v to CICFlowMeter."""

    alert_output_file: str = "./alerts.jsonl"
    """File path for local alerts when output_mode=file."""

    heuristic_unique_dst_port_threshold: int = 30
    """Heuristic alert signal for port scan/fan-out behavior."""

    heuristic_syn_ratio_threshold: float = 0.6
    """Heuristic alert signal for SYN-heavy traffic."""

    heuristic_packets_per_minute_threshold: float = 1000.0
    """Heuristic alert signal for high traffic volume."""

    capture_stats_interval: int = 30
    """Interval in seconds between traffic capture diagnostic logs."""

    reporting_enabled: bool = False
    """Whether to report posture, traffic, and alerts to the backend API."""

    backend_url: str = "http://localhost:8000"
    """Base URL for the backend API."""

    agent_token: str | None = None
    """Device-scoped agent token for backend API calls."""

    device_id: int | None = None
    """Backend device ID this agent token is scoped to."""

    api_timeout: float = 10.0
    """Backend API request timeout in seconds."""

    @field_validator(
        "interface",
        "target_ip",
        "agent_id",
        "agent_token",
        "device_id",
        mode="before",
    )
    @classmethod
    def empty_string_to_none(cls, value: Any) -> Any:
        """Treat blank .env optional values as unset."""
        if value == "":
            return None
        return value


# Global settings instance - loaded once at module import
settings = Settings()
