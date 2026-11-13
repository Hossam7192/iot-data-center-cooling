
import sqlite3
from pathlib import Path
from datetime import datetime
import matplotlib.pyplot as plt

# Find our SQLite database
db_path = Path(__file__).parent / "sensor_data.db"

# Connect and retrieve sensor readings
with sqlite3.connect(db_path) as connection:
    rows = connection.execute("""
        SELECT timestamp, temperature
        FROM sensor_readings
        ORDER BY id
    """).fetchall()

if not rows:
    print("No sensor data available.")
    raise SystemExit

# Convert database readings into chart values
times = [datetime.fromisoformat(row[0]) for row in rows]
temperatures = [row[1] for row in rows]

# Create temperature chart
plt.figure(figsize=(11, 5))
plt.plot(times, temperatures, label="Temperature")

# Cooling thresholds
plt.axhline(26, linestyle="--", label="Fan ON at 26°C")
plt.axhline(24, linestyle="--", label="Fan OFF at 24°C")

plt.title("IoT Data Center Cooling - Temperature History")
plt.xlabel("Time")
plt.ylabel("Temperature (°C)")
plt.legend()
plt.grid(True)
plt.tight_layout()

plt.show()