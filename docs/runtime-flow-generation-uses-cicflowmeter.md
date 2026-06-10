# Runtime network-flow generation uses CICFlowMeter instead of reimplementing CIC-style features in the agent

## Context

ZT Suite has two different network-monitoring representations today:

- `/ids` trains and evaluates models on CICFlowMeter-style flow rows with fields such as `flow_duration`, `tot_fwd_pkts`, `tot_bwd_pkts`, packet-length statistics, IAT statistics, TCP flag counts, active/idle statistics, and subflow statistics.
- `/agent` currently captures packets with Scapy and reduces each batch into a smaller custom feature vector such as packet count, byte count, unique destination counts, TCP flag ratios, and port ratios.

This mismatch means a model trained in `/ids` cannot be deployed reliably in `/agent`: the runtime input distribution is not the same as the training input distribution. Even if `/agent` reimplemented the missing CIC-style fields with Scapy, small differences in flow direction, timeout behavior, IAT calculations, active/idle windows, header/window extraction, and CICFlowMeter-specific quirks could create model drift.

## Decision

Runtime ML inference for network anomaly detection will use CICFlowMeter-generated flow rows as the model input source. The agent will treat CICFlowMeter as the canonical flow-feature generator rather than attempting to reproduce CICFlowMeter semantics manually with Scapy.

The intended runtime shape is:

```text
packet capture window
  -> PCAP file
  -> CICFlowMeter
  -> CIC-style flow CSV rows
  -> model/scaler inference from /ids-compatible logic
  -> window aggregation and alert generation
  -> backend reporting/dashboard display
```

Scapy may still be used for lightweight packet capture, diagnostics, or existing dashboard metadata if useful, but it is not the canonical source for ML model features. For model-backed detection, the agent must score the same kind of flow rows used during training and evaluation.

This keeps the project defensible: the training pipeline and deployment pipeline share the same feature-generation contract. The detection latency becomes near-real-time batch latency, based on the PCAP rotation/CICFlowMeter interval, rather than packet-by-packet inference. That tradeoff is acceptable for this prototype because the current agent already uses batch-oriented traffic processing.

## Invariants

- The CICFlowMeter implementation and version used for runtime flow generation must match the implementation/version used to generate training and evaluation data as closely as possible.
- ML-backed runtime inference must consume CICFlowMeter-style flow rows, not the current custom packet-batch feature vector.
- The model artifact, scaler artifact, feature column list, column normalization, and preprocessing rules must remain compatible between `/ids` and `/agent`.
- Runtime flow rows must preserve the metadata needed for alerting and investigation, including source/destination IPs, ports, protocol, timestamp, prediction score, and prediction label.
- Any fallback detector must be explicitly marked as fallback/heuristic in alerts and logs; it must not be presented as model-backed detection.
- Packet capture windows must be bounded by configured rotation/flush intervals so inference latency is predictable.
- Raw packet payloads remain out of scope; the system processes packet metadata/PCAP-derived flow features for security monitoring.

## Consequences of not following this decision

- Trained `/ids` models may appear to run in `/agent` but produce unreliable predictions because runtime features differ from training features.
- Detection metrics from experiments will not represent deployed behavior.
- Manual Scapy feature extraction may silently diverge from CICFlowMeter behavior, especially for bidirectional flow assignment, IAT statistics, active/idle statistics, subflow fields, and TCP window/header fields.
- Future model tuning will become ambiguous because failures could come from either model quality or feature-generation mismatch.
- Alerts shown in the dashboard may be difficult to justify during evaluation because the model input contract is inconsistent.

## File references

- `PRD.md` — product requirement describing edge-based traffic monitoring, anomaly detection, and the current model/runtime gap.
- `README.md` — project-level runtime and development commands.
- `agent/src/collectors/traffic.py` — current Scapy packet capture implementation.
- `agent/src/services/feature_engineering.py` — current custom packet-batch feature engineering that does not match CICFlowMeter training rows.
- `agent/src/ml/inference.py` — current local anomaly detector and heuristic fallback path.
- `agent/src/models/traffic.py` — current packet-level traffic record schema.
- `ids/src/config.py` — canonical feature columns and column normalization map for trained IDS models.
- `ids/src/inference.py` — deployment-safe model/scaler inference wrapper for flow rows.
- `ids/src/preprocessing.py` — inference-time cleaning rules that must remain aligned with training.
- `ids/src/aggregation.py` — scored-flow aggregation and alert logic.
- `ids/README.md` — current CICFlowMeter-based attack simulation and inference workflow.
