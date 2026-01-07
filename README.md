# Zero-Trust Security Suite (ZT Suite)

A software-only zero-trust security platform for SME environments.

## Prerequisites

### Windows (for packet capture)

Install [Npcap](https://npcap.com/) - required for Scapy packet capture on Windows

### Linux

No additional dependencies required. Packet capture requires root privileges or `CAP_NET_RAW` capability.

Compatibility:

sudo uv venv compatibility issue.

```
~/.local/bin/uv run python -c "from src.config import settings; print(f'Output mode: {settings.output_mode}'); print(f'Output file: {settings.output_file}')"
sudo ~/.local/bin/uv run python -m src.main
```

## Project Structure

See [AGENTS.md](./AGENTS.md) for detailed project structure and development guidelines.

See [PRD.md](./PRD.md) for product requirements.

See [CHECKLIST.md](./CHECKLIST.md) for implementation progress.
