# iot-data-center-cooling
IoT-based temperature monitoring and automatic cooling prototype for data center environments.
# IoT Data Center Cooling Monitoring System

A small-scale IoT prototype for monitoring temperature and controlling cooling in a data center environment.

## Project Goal

The goal of this project is to build a system that can monitor temperature and humidity and automatically control a cooling fan when the temperature becomes too high.

## Planned System

Temperature & Humidity Sensor
        ↓
      ESP32
        ↓
 Temperature Check
        ↓
    Fan Control
        ↓
    Cooling Fan

## Main Components

- ESP32
- DHT22 temperature and humidity sensor
- 5V DC fan
- MOSFET module
- Breadboard
- Jumper wires

## MVP

The first working version should be able to:

1. Read temperature and humidity.
2. Send the readings to the ESP32.
3. Check the temperature against a defined limit.
4. Automatically turn the cooling fan on or off.
5. Display the current readings for testing.

## Possible Future Development

If the MVP is completed successfully, the project may be extended with:

- Wi-Fi communication
- Data storage
- Monitoring dashboard
- Additional sensors
- Airflow monitoring

## Team

- Team Leader: Hossam Ragab
- Team Members: Md Mohiuddin Mollah
- Team Members: leslie foncham mbunda
## Status

🚧 Project setup
## Final AI Experiment Results

The Random Forest Regression model predicts temperature
approximately five minutes ahead using historical sensor data.

### Latest Results - November 24, 2026

| Metric | Result |
|---|---|
| Recording sessions | 6 |
| Usable readings | 1764 |
| Training samples | 1351 |
| Testing samples | 353 |
| AI MAE | 0.582°C |
| Baseline MAE | 0.245°C |

The baseline outperformed the AI model.
Further data collection and model improvements are needed.

The automatic cooling system remains functional and operates
independently of the AI model.

The AI component is an experimental proof of concept.
