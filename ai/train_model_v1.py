
import sqlite3
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error

# 1. Database location
DB_PATH = Path(__file__).parent / "sensor_data.db"

# 2. Load sensor readings
with sqlite3.connect(DB_PATH) as connection:
    df = pd.read_sql_query("""
        SELECT timestamp, temperature, humidity, fan_status
        FROM sensor_readings
        ORDER BY timestamp, id
    """, connection)

print(f"Loaded {len(df)} readings")

# 3. Check whether enough data is available
if len(df) < 500:
    print("Not enough data yet. Collect at least 500 readings.")
    raise SystemExit

# 4. Prepare data
df["timestamp"] = pd.to_datetime(df["timestamp"])
df["fan_on"] = (df["fan_status"] == "ON").astype(int)

# Remove invalid readings
df = df.dropna(subset=["timestamp", "temperature", "humidity"])

# 5. Create historical features
df["temp_previous_1"] = df["temperature"].shift(1)
df["temp_previous_6"] = df["temperature"].shift(6)
df["temp_previous_12"] = df["temperature"].shift(12)

# 6. Predict temperature approximately 5 minutes ahead
# ESP32 publishes approximately every 5 seconds
FUTURE_STEPS = 60

df["future_temperature"] = df["temperature"].shift(-FUTURE_STEPS)

# Remove rows with missing values
df = df.dropna().copy()

if len(df) < 200:
    print("Not enough usable training samples yet.")
    raise SystemExit

# 7. Select input features
features = [
    "temperature",
    "humidity",
    "fan_on",
    "temp_previous_1",
    "temp_previous_6",
    "temp_previous_12"
]

X = df[features]
y = df["future_temperature"]

# 8. Split data chronologically
split_index = int(len(df) * 0.8)

X_train = X.iloc[:split_index]
X_test = X.iloc[split_index:]

y_train = y.iloc[:split_index]
y_test = y.iloc[split_index:]

# 9. Train Random Forest model
model = RandomForestRegressor(
    n_estimators=100,
    random_state=42,
    n_jobs=-1
)

model.fit(X_train, y_train)

# 10. Make predictions
predictions = model.predict(X_test)

# 11. Compare with a simple baseline
baseline_predictions = X_test["temperature"]

ai_error = mean_absolute_error(y_test, predictions)
baseline_error = mean_absolute_error(
    y_test,
    baseline_predictions
)

print("\n--- MODEL RESULTS ---")
print(f"Training samples: {len(X_train)}")
print(f"Testing samples: {len(X_test)}")
print(f"AI prediction error: {ai_error:.3f} °C")
print(f"Baseline error: {baseline_error:.3f} °C")

if ai_error < baseline_error:
    print("AI performed better than the baseline!")
else:
    print("Baseline performed as well or better.")

# 12. Display example predictions
print("\nActual vs predicted temperatures:")

for actual, predicted in zip(
    y_test.iloc[:10],
    predictions[:10]
):
    print(
        f"Actual: {actual:.2f} °C | "
        f"Predicted: {predicted:.2f} °C"
    )
