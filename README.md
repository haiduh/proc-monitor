# proc-monitor

Lightweight Linux system monitor that reads directly from `/proc` — no external dependencies.

## Features
- CPU usage (aggregate, sampled every 3 seconds)
- Memory usage (total, available, % used)
- Top 10 processes by CPU usage
- Spike alerts for CPU and memory thresholds

## Requirements
- Linux (or WSL)
- Python 3.x

## Usage
python3 main.py
