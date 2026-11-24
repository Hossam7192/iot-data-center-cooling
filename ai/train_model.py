
import sqlite3
from pathlib import Path

import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error

# Database
DB_PATH = Path(__file__).parent / "sensor_data.db"

# Prediction settings
FUTURE_MINUTES = 5
FUTURE_STEPS = 60  # Approximately 5 minutes at 5-second intervals

# Load historical data
with sqlite3.connect(DB_PATH) as connection:
    df = pd.read_sql_query("""
        SELECT timestamp, temperature, humidity, fan_status
        FROM sensor_readings
        ORDER BY timestamp, id
    """, connection)

print(f"Loaded {len(df)} readings")

df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
df["temperature"] = pd.to_numeric(df["temperature"], errors="coerce")
df["humidity"] = pd.to_numeric(df["humidity"], errors="coerce")

df = df.dropna(subset=[
    "timestamp", "temperature", "humidity"
]).copy()

df = df.sort_values("timestamp").drop_duplicates(
    subset="timestamp", keep="last"
).reset_index(drop=True)

# Convert fan status into a number
df["fan_on"] = (df["fan_status"] == "ON").astype(int)

# Check that data is approximately 5 seconds apart
intervals = df["timestamp"].diff().dt.total_seconds()
regular = intervals.between(3, 7)

# Split data into continuous recording sessions
df["session"] = (~regular).cumsum()

# Historical temperature features
df["temp_30s_ago"] = df.groupby("session")["temperature"].shift(6)
df["temp_60s_ago"] = df.groupby("session")["temperature"].shift(12)

# Temperature trend
df["trend_30s"] = df["temperature"] - df["temp_30s_ago"]
df["trend_60s"] = df["temperature"] - df["temp_60s_ago"]

# Average temperature over the last minute
df["temp_avg_60s"] = (
    df.groupby("session")["temperature"]
    .transform(lambda s: s.rolling(12, min_periods=12).mean())
)

# Future temperature within the same session
df["future_temperature"] = (
    df.groupby("session")["temperature"].shift(-FUTURE_STEPS)
)

df["future_timestamp"] = (
    df.groupby("session")["timestamp"].shift(-FUTURE_STEPS)
)

# Keep targets approximately 5 minutes ahead
future_seconds = (
    df["future_timestamp"] - df["timestamp"]
).dt.total_seconds()

df = df[future_seconds.between(270, 330)].copy()

features = [
    "temperature",
    "humidity",
    "fan_on",
    "temp_30s_ago",
    "temp_60s_ago",
    "trend_30s",
    "trend_60s",
    "temp_avg_60s"
]

df = df.dropna(subset=features + ["future_temperature"])

if len(df) < 300:
    print("Not enough usable data yet. Continue collecting.")
    raise SystemExit

# Chronological train/test split
split_index = int(len(df) * 0.8)

# Leave a 5-minute gap to prevent target overlap
train_df = df.iloc[:max(0, split_index - FUTURE_STEPS)]
test_df = df.iloc[split_index:]

if len(train_df) < 100 or len(test_df) < 30:
    print("Not enough training/testing samples.")
    raise SystemExit

X_train = train_df[features]
y_train = train_df["future_temperature"]

X_test = test_df[features]
y_test = test_df["future_temperature"]

# Train AI model
model = RandomForestRegressor(
    n_estimators=100,
    min_samples_leaf=5,
    random_state=42,
    n_jobs=-1
)

model.fit(X_train, y_train)

# Evaluate AI and baseline
predictions = model.predict(X_test)
baseline = X_test["temperature"]

ai_error = mean_absolute_error(y_test, predictions)
baseline_error = mean_absolute_error(y_test, baseline)

print("\n--- MODEL V2 RESULTS ---")
print(f"Training samples: {len(X_train)}")
print(f"Testing samples: {len(X_test)}")
print(f"AI prediction error: {ai_error:.3f} °C")
print(f"Baseline error: {baseline_error:.3f} °C")

if ai_error < baseline_error:
    print("AI outperformed the baseline!")
else:
    print("Baseline still performed better.")

print("\nActual vs predicted:")
for actual, predicted in zip(y_test.iloc[:10], predictions[:10]):
    print(f"Actual: {actual:.2f} °C | Predicted: {predicted:.2f} °C")
