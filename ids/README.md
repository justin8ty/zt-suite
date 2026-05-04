# IDS (Flow-Based Binary Classification)

Minimal training + inference utilities for flow-based intrusion detection (Benign vs Malicious) using trained binary classification models on labeled flow data.

## Run (from `ids/`)

### Install dependencies

```bash
uv sync
```

### Train models

```bash
uv run python train.py
```

### Inference

```bash
uv run python -m src.infer --model models/xgb.joblib --input data/flows/example.csv
```

By default, results are saved to `data/flows-results/<input>-<model>.csv` and the scaler is inferred from the model name.

## Attack Simulation Setup

### Defender VM (Ubuntu Server)

#### CICFlowMeter setup

```bash
git clone https://github.com/hieulw/cicflowmeter
cd cicflowmeter
uv sync
source .venv/bin/activate
```

#### Services setup

```bash
sudo apt install -y vsftpd openssh-server apache2
sudo systemctl enable --now vsftpd ssh apache2
```

#### Packet capture preparation for attack

```bash
ip addr
sudo tcpdump -i ens33 -w example.pcap
```

#### After attack

```bash
uv run cicflowmeter -f example.pcap -c example.csv
mv example.csv /mnt/hgfs/Shared
```

### Attacker VM (Kali)

#### Wordlists

```bash
wordlists -h
```

#### DoS

```bash
sudo hping3 -S -p 80 --flood 192.168.88.134
```

#### FTP

```bash
hydra -L fasttrack.txt -P fasttrack.txt ssh://192.168.88.134 -t 16 -W 1
```

#### SSH

```bash
sudo patator ssh_login host=192.168.88.134 user=FILE0 password=FILE1 0=fasttrack.txt 1=fasttrack.txt -x ignore:mesg='Authentication failed' -t 20
```
