import csv
import random
from datetime import date, timedelta

LINES = {"Line A": 12.0, "Line B": 20.0, "Line C": 8.0}  # ideal units/min: moulding, packing, assembly
SHIFTS = {"Day": 0.92, "Night": 0.85}  # typical speed vs ideal
PLANNED_MIN = 480
REASONS = {"Machine Failure": 5, "Material Shortage": 3, "Changeover": 4}
FIELDS = ["date", "line", "shift", "planned_time_min", "downtime_min",
          "downtime_reason", "ideal_rate", "total_output", "defects"]


def generate(path, days=30, seed=42):
    rng = random.Random(seed)
    today = date.today()
    rows = []
    for d in range(days, 0, -1):
        day = today - timedelta(days=d)
        for line, rate in LINES.items():
            for shift, speed in SHIFTS.items():
                down, reason = 0, ""
                if rng.random() < 0.7:
                    reason = rng.choices(list(REASONS), list(REASONS.values()))[0]
                    down = rng.randint(10, 120 if reason == "Machine Failure" else 60)
                run = PLANNED_MIN - down
                output = int(run * rate * rng.gauss(speed, 0.04))
                scrap_p = rng.uniform(0.01, 0.03) * (1.8 if line == "Line B" and shift == "Night" else 1)
                defects = sum(rng.random() < scrap_p for _ in range(output))
                rows.append([day.isoformat(), line, shift, PLANNED_MIN, down, reason, rate, output, defects])
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(FIELDS)
        w.writerows(rows)
    return len(rows)


if __name__ == "__main__":
    print(f"{generate('production_data.csv')} rows -> production_data.csv")
