import argparse
import os
from datetime import date, timedelta
import pandas as pd
import numpy as np

CSV_NAME = "device_metrics.csv"

# Daily schema columns
COLUMNS = [
    "date",          # ISO date string
    "device_id",     # simple integer id
    "temperature_c", # average temperature reading for the day
    "humidity_pct",  # average humidity
    "battery_pct",   # end-of-day battery percentage
    "error_count",   # number of error events simulated
    "status"         # derived status (OK, WARN, ERROR, LOW_BATTERY)
]

STATUSES = ["OK", "WARN", "ERROR", "LOW_BATTERY"]

rng = np.random.default_rng()

def _derive_status(battery: float, errors: int) -> str:
    if battery < 15:
        return "LOW_BATTERY"
    if errors >= 3:
        return "ERROR"
    if errors >= 1:
        return "WARN"
    return "OK"

def generate_initial_history(days: int, devices: int) -> pd.DataFrame:
    today = date.today()
    records = []
    # Start each device with a random battery between 60-100
    starting_battery = rng.integers(60, 101, size=devices)

    for d in range(days, 0, -1):
        current_day = today - timedelta(days=d)
        for dev in range(1, devices + 1):
            # Simulate gradual battery drain
            drain = rng.uniform(0.5, 2.5)
            starting_battery[dev-1] = max(0, starting_battery[dev-1] - drain)
            battery = starting_battery[dev-1]
            temp = rng.normal(25, 3)
            humidity = rng.normal(45, 5)
            errors = rng.poisson(0.4)
            status = _derive_status(battery, errors)
            records.append({
                "date": current_day.isoformat(),
                "device_id": dev,
                "temperature_c": round(temp, 2),
                "humidity_pct": round(humidity, 2),
                "battery_pct": round(battery, 1),
                "error_count": int(errors),
                "status": status
            })
    return pd.DataFrame(records)

def append_today(csv_path: str, devices: int):
    today_str = date.today().isoformat()
    if os.path.exists(csv_path):
        df = pd.read_csv(csv_path)
        # For each device, find last battery to continue draining realistically
        last_battery = df.sort_values(["device_id", "date"]).groupby("device_id").tail(1).set_index("device_id")["battery_pct"]
    else:
        df = pd.DataFrame(columns=COLUMNS)
        last_battery = pd.Series({i: rng.integers(70, 101) for i in range(1, devices + 1)})

    new_rows = []
    for dev in range(1, devices + 1):
        prev_batt = last_battery.get(dev, rng.integers(65, 101))
        drain = rng.uniform(0.8, 3.0)
        battery = max(0, prev_batt - drain)
        temp = rng.normal(25, 3)
        humidity = rng.normal(45, 5)
        errors = rng.poisson(0.5)
        status = _derive_status(battery, errors)
        new_rows.append({
            "date": today_str,
            "device_id": dev,
            "temperature_c": round(temp, 2),
            "humidity_pct": round(humidity, 2),
            "battery_pct": round(battery, 1),
            "error_count": int(errors),
            "status": status
        })

    new_df = pd.DataFrame(new_rows)

    # Prevent duplicate day rows per device (idempotent)
    df = df[~((df["date"] == today_str))]
    full = pd.concat([df, new_df], ignore_index=True).sort_values(["device_id", "date"]) 
    full.to_csv(csv_path, index=False)
    print(f"Appended {len(new_rows)} rows for {today_str} to {csv_path}")


def ensure_csv(csv_path: str, days: int, devices: int):
    if os.path.exists(csv_path):
        print(f"Found existing {csv_path}")
        return
    print(f"Generating initial history: days={days}, devices={devices}")
    hist = generate_initial_history(days=days, devices=devices)
    hist.to_csv(csv_path, index=False)
    print(f"Created {csv_path} with {len(hist)} rows")


def main():
    parser = argparse.ArgumentParser(description="Device metrics CSV simulator")
    parser.add_argument("--devices", type=int, default=5, help="Number of devices")
    parser.add_argument("--history-days", type=int, default=14, help="Initial backfill days if file missing")
    parser.add_argument("--csv", type=str, default=CSV_NAME, help="CSV filename")
    parser.add_argument("--append-today", action="store_true", help="Append today's data and exit")
    args = parser.parse_args()

    csv_path = args.csv
    ensure_csv(csv_path, args.history_days, args.devices)
    if args.append_today:
        append_today(csv_path, args.devices)

if __name__ == "__main__":
    main()
