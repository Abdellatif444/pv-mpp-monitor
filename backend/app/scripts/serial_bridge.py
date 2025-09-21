"""
Optional serial bridge script to read from a COM port (Proteus/ESP32) and push samples to the API.

Usage (local):
    python serial_bridge.py --port COM3 --baud 115200 --api http://localhost:8000 --token devtoken

Expected incoming lines (examples):
    V:20.2V I:0.10A P:2.1W
or JSON:
    {"V":20.2, "I":0.10, "P":2.1}

The script will parse and POST to /api/samples (JSON), or forward raw text to /api/import/text.
"""
import argparse
import json
import sys
import time
from typing import Optional

try:
    import serial  # pyserial
except Exception:
    serial = None

import requests


def post_samples(api: str, token: str, payload):
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    r = requests.post(f"{api}/api/samples", headers=headers, json=payload, timeout=5)
    r.raise_for_status()


def post_text(api: str, token: str, text: str):
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "text/plain"}
    r = requests.post(f"{api}/api/import/text", headers=headers, data=text.encode("utf-8"), timeout=5)
    r.raise_for_status()


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--port", required=True, help="Serial port, e.g., COM3")
    p.add_argument("--baud", type=int, default=115200)
    p.add_argument("--api", default="http://localhost:8000")
    p.add_argument("--token", required=True)
    args = p.parse_args()

    if serial is None:
        print("pyserial not installed. Install with: pip install pyserial", file=sys.stderr)
        sys.exit(2)

    ser = serial.Serial(args.port, args.baud, timeout=1)
    print(f"Reading from {args.port} at {args.baud} baud. Forwarding to {args.api}")

    try:
        while True:
            line = ser.readline().decode("utf-8", errors="ignore").strip()
            if not line:
                continue
            # Try JSON first
            try:
                obj = json.loads(line)
                if isinstance(obj, dict) or isinstance(obj, list):
                    post_samples(args.api, args.token, obj)
                    continue
            except Exception:
                pass
            # Fallback to raw text
            try:
                post_text(args.api, args.token, line)
            except Exception as e:
                print(f"Error posting: {e}")
    except KeyboardInterrupt:
        print("Exiting...")
    finally:
        try:
            ser.close()
        except Exception:
            pass


if __name__ == "__main__":
    main()
