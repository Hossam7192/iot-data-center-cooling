
import sqlite3
from datetime import datetime
import paho.mqtt.client as mqtt

# MQTT settings
BROKER = "broker.emqx.io"
PORT = 1883
TOPIC = "hossam7192/datacenter/#"

# Database settings
DB_PATH = "ai/sensor_data.db"

# Connect to SQLite
db = sqlite3.connect(DB_PATH)
cursor = db.cursor()

# Create a table if it does not exist
cursor.execute("""
CREATE TABLE IF NOT EXISTS sensor_readings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT,
    temperature REAL,
    humidity REAL,
    fan_status TEXT
)
""")
db.commit()

# Store the latest received values
latest = {
    "temperature": None,
    "humidity": None,
    "fan_status": None
}

def on_connect(client, userdata, flags, reason_code, properties):
    if reason_code == 0:
        print("Connected to MQTT broker!")
        client.subscribe(TOPIC)
        print("Collecting sensor data...")
    else:
        print(f"Connection failed: {reason_code}")

def on_message(client, userdata, message):
    topic = message.topic
    value = message.payload.decode("utf-8")

    if topic.endswith("/temperature"):
        latest["temperature"] = float(value)

    elif topic.endswith("/humidity"):
        latest["humidity"] = float(value)

    elif topic.endswith("/fan/status"):
        latest["fan_status"] = value

        # Save a complete reading when fan status arrives
        if all(v is not None for v in latest.values()):
            timestamp = datetime.now().isoformat(timespec="seconds")

            cursor.execute("""
                INSERT INTO sensor_readings
                (timestamp, temperature, humidity, fan_status)
                VALUES (?, ?, ?, ?)
            """, (
                timestamp,
                latest["temperature"],
                latest["humidity"],
                latest["fan_status"]
            ))

            db.commit()

            print(
                f"{timestamp} | "
                f"Temp: {latest['temperature']} C | "
                f"Humidity: {latest['humidity']}% | "
                f"Fan: {latest['fan_status']} | SAVED"
            )

            # Wait for fresh readings
            latest["temperature"] = None
            latest["humidity"] = None
            latest["fan_status"] = None

client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
client.on_connect = on_connect
client.on_message = on_message

print("Connecting to MQTT...")

try:
    client.connect(BROKER, PORT, 60)
    client.loop_forever()
except KeyboardInterrupt:
    print("\nStopping data collection...")
finally:
    db.close()
