
import sqlite3
from pathlib import Path
from datetime import datetime
import matplotlib.pyplot as plt

# Find our SQLite database
db_path = Path(__file__).parent / "sensor_data.db"

# Retrieve sensor readings
with sqlite3.connect(db_path) as connection:
    rows = connection.execute("""
        SELECT timestamp, temperature
        FROM sensor_readings
        ORDER BY timestamp, id
    """).fetchall()

if not rows:
    print("No sensor data available.")
    raise SystemExit

# Convert readings into chart values
times = [datetime.fromisoformat(row[0]) for row in rows]
temperatures = [row[1] for row in rows]

# Start a new session when the gap exceeds 10 seconds
sessions = []
session_times = [times[0]]
session_temps = [temperatures[0]]

for i in range(1, len(times)):
    gap = (times[i] - times[i - 1]).total_seconds()

    if gap > 10:
        sessions.append((session_times, session_temps))
        session_times = []
        session_temps = []

    session_times.append(times[i])
    session_temps.append(temperatures[i])

sessions.append((session_times, session_temps))

# Create temperature chart
plt.figure(figsize=(11, 5))

for i, (session_times, session_temps) in enumerate(sessions):
    plt.plot(
        session_times,
        session_temps,
        label="Temperature" if i == 0 else None
    )

# Cooling thresholds
plt.axhline(26, linestyle="--", label="Fan ON at 26°C")
plt.axhline(24, linestyle="--", label="Fan OFF at 24°C")

plt.title("IoT Data Center Cooling - Temperature History")
plt.xlabel("Time")
plt.ylabel("Temperature (°C)")
plt.legend()
plt.grid(True)
plt.tight_layout()

print(f"Total readings: {len(rows)}")
print(f"Recording sessions: {len(sessions)}")

plt.show()
