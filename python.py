import argparse
import csv
import json
import random
import time
import uuid
from datetime import datetime, timezone
 
# ----------------------------------------------------------------------
# Commodity profiles: each commodity has a realistic operating range for
# temperature (Celsius) and humidity (%), plus a home GPS region so routes
# look geographically sensible instead of pure noise.
# ----------------------------------------------------------------------
COMMODITY_PROFILES = {
    "Frozen Seafood":   {"temp_range": (-22, -18), "humidity_range": (85, 95)},
    "Fresh Produce":    {"temp_range": (2, 8),      "humidity_range": (85, 95)},
    "Dairy":            {"temp_range": (1, 4),      "humidity_range": (70, 85)},
    "Pharmaceuticals":  {"temp_range": (2, 8),      "humidity_range": (30, 60)},
    "Electronics":      {"temp_range": (10, 35),    "humidity_range": (10, 40)},
    "Dry Goods":        {"temp_range": (15, 30),    "humidity_range": (20, 50)},
    "Meat":             {"temp_range": (-2, 4),     "humidity_range": (80, 90)},
    "Flowers":          {"temp_range": (1, 5),      "humidity_range": (85, 95)},
}
 
# Rough shipping-lane bounding boxes (lat_min, lat_max, lon_min, lon_max)
# used so simulated GPS points cluster along plausible trade routes.
SHIPPING_LANES = [
    (1.0, 35.0, 45.0, 120.0),     # South/East Asia
    (30.0, 55.0, -10.0, 40.0),    # Europe
    (25.0, 50.0, -125.0, -70.0),  # USA
    (-35.0, -5.0, -75.0, -35.0),  # South America
]
 
 
class Container:
    """Represents a single container with a persistent ID, commodity type,
    and a slowly-drifting GPS position (so consecutive readings look like
    real movement rather than teleporting)."""
 
    def __init__(self, container_id=None, commodity=None):
        self.container_id = container_id or self._generate_container_id()
        self.commodity = commodity or random.choice(list(COMMODITY_PROFILES.keys()))
        lane = random.choice(SHIPPING_LANES)
        self.lat = round(random.uniform(lane[0], lane[1]), 6)
        self.lon = round(random.uniform(lane[2], lane[3]), 6)
        # small random walk deltas so the container appears "in transit"
        self._dlat = random.uniform(-0.01, 0.01)
        self._dlon = random.uniform(-0.01, 0.01)
 
    @staticmethod
    def _generate_container_id():
        # ISO 6346-style: 4 letters (owner code + category) + 7 digits
        letters = "".join(random.choices("ABCDEFGHIJKLMNOPQRSTUVWXYZ", k=4))
        digits = "".join(random.choices("0123456789", k=7))
        return f"{letters}{digits}"
 
    def move(self):
        self.lat = round(max(-90, min(90, self.lat + self._dlat + random.uniform(-0.002, 0.002))), 6)
        self.lon = round(max(-180, min(180, self.lon + self._dlon + random.uniform(-0.002, 0.002))), 6)
 
    def read_sensor(self):
        profile = COMMODITY_PROFILES[self.commodity]
        t_lo, t_hi = profile["temp_range"]
        h_lo, h_hi = profile["humidity_range"]
 
        # Occasionally inject a mild anomaly (sensor fault / door-open event)
        anomaly = random.random() < 0.03
        temperature = round(random.uniform(t_lo, t_hi) + (random.uniform(3, 6) if anomaly else 0), 2)
        humidity = round(random.uniform(h_lo, h_hi), 2)
 
        self.move()
 
        return {
            "timestamp": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "container_id": self.container_id,
            "commodity_type": self.commodity,
            "temperature_c": temperature,
            "humidity_pct": humidity,
            "gps_lat": self.lat,
            "gps_lon": self.lon,
            "reading_id": str(uuid.uuid4()),
            "anomaly": anomaly,
        }
 
 
def generate_containers(n):
    return [Container() for _ in range(n)]
 
 
def write_csv(rows, path):
    fieldnames = list(rows[0].keys())
    with open(path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
 
 
def write_json(rows, path):
    with open(path, "w") as f:
        json.dump(rows, f, indent=2)
 
 
def main():
    parser = argparse.ArgumentParser(description="Simulate IoT cargo sensor telemetry.")
    parser.add_argument("--containers", type=int, default=5, help="Number of containers to simulate")
    parser.add_argument("--count", type=int, default=100, help="Total number of readings to generate (batch mode)")
    parser.add_argument("--output", choices=["csv", "json", "stdout"], default="csv", help="Output format")
    parser.add_argument("--outfile", default=None, help="Output file path (default: sensor_data.<ext>)")
    parser.add_argument("--stream", action="store_true", help="Stream readings continuously instead of a fixed batch")
    parser.add_argument("--interval", type=float, default=1.0, help="Seconds between readings in stream mode")
    parser.add_argument("--seed", type=int, default=None, help="Random seed for reproducible output")
    args = parser.parse_args()
 
    if args.seed is not None:
        random.seed(args.seed)
 
    fleet = generate_containers(args.containers)
 
    if args.stream:
        print("Streaming sensor data (Ctrl+C to stop)...\n")
        try:
            while True:
                container = random.choice(fleet)
                reading = container.read_sensor()
                print(json.dumps(reading))
                time.sleep(args.interval)
        except KeyboardInterrupt:
            print("\nStream stopped.")
        return
 
    rows = []
    for i in range(args.count):
        container = random.choice(fleet)
        rows.append(container.read_sensor())
 
    if args.output == "stdout":
        for row in rows:
            print(json.dumps(row))
    elif args.output == "csv":
        path = args.outfile or "sensor_data.csv"
        write_csv(rows, path)
        print(f"Wrote {len(rows)} readings to {path}")
    elif args.output == "json":
        path = args.outfile or "sensor_data.json"
        write_json(rows, path)
        print(f"Wrote {len(rows)} readings to {path}")
 
 
if __name__ == "__main__":
    main()
 
