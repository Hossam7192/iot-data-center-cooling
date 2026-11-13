
import sqlite3
from pathlib import Path

# Locate the database
db_path = Path(__file__).parent / "sensor_data.db"

# Connect to SQLite
connection = sqlite3.connect(db_path)
cursor = connection.cursor()

# Count saved readings
cursor.execute("SELECT COUNT(*) FROM sensor_readings")
total = cursor.fetchone()[0]

print(f"Total saved readings: {total}")

# Show the latest 10 readings
cursor.execute("""
    SELECT timestamp, temperature, humidity, fan_status
    FROM sensor_readings
    ORDER BY id DESC
    LIMIT 10
""")

print("\nLatest sensor readings:")

for row in cursor.fetchall():
    print(row)

connection.close()
