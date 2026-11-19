
import sqlite3
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error

# 1. Load sensor data
db_path = Path(__file__).parent / "sensor_data.db"

with sqlite3.connect(db_path) as connection:
    df = pd.read_sql_query("""
        SELECT timestamp, temperature, humidity, fan_status
        FROM sensor_readings
        ORDER BY timestamp, id
    """, connection)

df["timestamp"] = pd.to_datetime(df["timestamp"])
df = df.dropna().sort_values("timestamp")
df = df.drop_duplicates(subset=["timestamp"]).reset_index(drop=True)

# 2. Separate recording sessions
# Start a new session if the gap is over 10 seconds
gaps = df["timestamp"].diff().dt.total_seconds()
df["session"] = (gaps.isna() | (gaps > 10) | (gaps <= 0)).cumsum()

df["fan_on"] = (df["fan_status"] == "ON").astype(int)

# 3. Create historical features within each session
group = df.groupby("session")

df["temp_30s_ago"] = group["temperature"].shift(6)
df["temp_60s_ago"] = group["temperature"].shift(12)
df["humidity_60s_ago"] = group["humidity"].shift(12)

df["temp_trend_30s"] = (
    df["temperature"] - df["temp_30s_ago"]
)
df["temp_trend_60s"] = (
    df["temperature"] - df["temp_60s_ago"]
)

df["temp_avg_60s"] = (
    group["temperature"]
    .transform(lambda x: x.rolling(12).mean())
)

# 4. Find the temperature approximately 5 minutes later
# 60 readings x approximately 5 seconds = 300 seconds
df["future_temp"] = group["temperature"].shift(-60)
df["future_time"] = group["timestamp"].shift(-60)

future_seconds = (
    df["future_time"] - df["timestamp"]
).dt.total_seconds()

# Keep predictions whose target is 4.5–5.5 minutes later
df = df[future_seconds.between(270, 330)].copy()

features = [
    "temperature",
    "humidity",
    "fan_on",
    "temp_30s_ago",
    "temp_60s_ago",
    "humidity_60s_ago",
    "temp_trend_30s",
    "temp_trend_60s",
    "temp_avg_60s",
]

df = df.dropna(subset=features + ["future_temp"])

if len(df) < 200:
    raise SystemExit(
        f"Only {len(df)} usable readings. Collect more data."
    )

# 5. Split chronologically (80% training, 20% testing)
split = int(len(df) * 0.8)

# Leave a gap to reduce overlap between training and test
train = df.iloc[:max(0, split - 60)]
test = df.iloc[split:]

if len(train) < 100 or len(test) < 30:
    raise SystemExit("Not enough data for training and testing.")

X_train = train[features]
y_train = train["future_temp"]

X_test = test[features]
y_test = test["future_temp"]

# 6. Train the model
model = RandomForestRegressor(
    n_estimators=200,
    min_samples_leaf=3,
    random_state=42,
    n_jobs=-1,
)

model.fit(X_train, y_train)

# 7. Compare AI with the simple baseline
predictions = model.predict(X_test)
baseline_predictions = test["temperature"].to_numpy()

ai_mae = mean_absolute_error(y_test, predictions)
baseline_mae = mean_absolute_error(
    y_test, baseline_predictions
)

print("\n=== AI MODEL V3 RESULTS ===")
print(f"Recording sessions: {df['session'].nunique()}")
print(f"Usable readings: {len(df)}")
print(f"Training samples: {len(train)}")
print(f"Testing samples: {len(test)}")
print(f"AI MAE: {ai_mae:.3f} °C")
print(f"Baseline MAE: {baseline_mae:.3f} °C")

if ai_mae < baseline_mae:
    print("AI outperformed the baseline!")
else:
    print("Baseline performed better. More improvements needed.")

# 8. Show feature importance
print("\nFeature importance:")
for name, importance in sorted(
    zip(features, model.feature_importances_),
    key=lambda item: item[1],
    reverse=True,
):
    print(f"{name}: {importance:.3f}")
