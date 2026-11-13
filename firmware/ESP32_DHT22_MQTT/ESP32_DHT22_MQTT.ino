
#include <WiFi.h>
#include <PubSubClient.h>
#include <DHT.h>

// 1. Wi-Fi settings
#include "wifi_config.h"

// 2. MQTT settings
const char* mqtt_server = "broker.emqx.io";
const int mqtt_port = 1883;

const char* temperature_topic =
  "hossam7192/datacenter/temperature";

const char* humidity_topic =
  "hossam7192/datacenter/humidity";

const char* fan_topic =
  "hossam7192/datacenter/fan/status";

// 3. Hardware settings
#define DHTPIN 4
#define DHTTYPE DHT22

#define FAN_PIN 5
#define FAN_PWM_FREQ 25000
#define FAN_PWM_RESOLUTION 8

// 4. Temperature thresholds
const float FAN_ON_TEMP = 26.0;
const float FAN_OFF_TEMP = 24.0;

// 5. Objects and variables
DHT dht(DHTPIN, DHTTYPE);

WiFiClient espClient;
PubSubClient client(espClient);

bool fanState = false;
bool pwmReady = false;

unsigned long lastReading = 0;
unsigned long lastWiFiAttempt = 0;
unsigned long lastMQTTAttempt = 0;

const unsigned long READING_INTERVAL = 5000;
const unsigned long RECONNECT_INTERVAL = 5000;

// Connect to Wi-Fi without blocking sensor readings
void maintainWiFi() {
  if (WiFi.status() == WL_CONNECTED) {
    return;
  }

  if (millis() - lastWiFiAttempt >= RECONNECT_INTERVAL) {
    lastWiFiAttempt = millis();

    Serial.println("Connecting to Wi-Fi...");
    WiFi.reconnect();
  }
}

// Connect to MQTT without blocking fan control
void maintainMQTT() {
  if (WiFi.status() != WL_CONNECTED) {
    return;
  }

  if (client.connected()) {
    client.loop();
    return;
  }

  if (millis() - lastMQTTAttempt >= RECONNECT_INTERVAL) {
    lastMQTTAttempt = millis();

    Serial.println("Connecting to MQTT...");

    String clientId = "ESP32S3-" +
                      String((uint32_t)ESP.getEfuseMac(), HEX);

    if (client.connect(clientId.c_str())) {
      Serial.println("MQTT connected!");
    } else {
      Serial.print("MQTT connection failed. State: ");
      Serial.println(client.state());
    }
  }
}

// Apply conventional active-HIGH PWM signal
// TEST ONLY: fan control wire must remain disconnected
void updateFanOutput() {
  if (!pwmReady) {
    return;
  }

  if (fanState) {
    ledcWrite(FAN_PIN, 255);
    Serial.println("FAN ON (command)");
  } else {
    ledcWrite(FAN_PIN, 0);
    Serial.println("FAN OFF (command)");
  }
}

void setup() {
  Serial.begin(115200);
  delay(1000);

  // Start DHT22 sensor
  dht.begin();

  // Configure GPIO 5 PWM output
  pwmReady = ledcAttach(
    FAN_PIN,
    FAN_PWM_FREQ,
    FAN_PWM_RESOLUTION
  );

  if (pwmReady) {
    // Initially output LOW
    ledcWrite(FAN_PIN, 0);
    Serial.println("PWM initialized.");
  } else {
    Serial.println("ERROR: PWM initialization failed!");
  }

  // Start Wi-Fi connection
  WiFi.mode(WIFI_STA);
  WiFi.begin(ssid, password);
  lastWiFiAttempt = millis();

  // Configure MQTT
  client.setServer(mqtt_server, mqtt_port);
  client.setSocketTimeout(1);

  Serial.println("System started.");
}

void loop() {
  // Maintain network connections
  maintainWiFi();
  maintainMQTT();

  // Read sensors every 5 seconds
  if (millis() - lastReading >= READING_INTERVAL) {
    lastReading = millis();

    float temperature = dht.readTemperature();
    float humidity = dht.readHumidity();

    // Check sensor readings
    if (isnan(temperature) || isnan(humidity)) {
      Serial.println("ERROR: Failed to read DHT22!");
      return;
    }

    // Automatic fan control with hysteresis
    if (temperature >= FAN_ON_TEMP) {
      fanState = true;
    } else if (temperature <= FAN_OFF_TEMP) {
      fanState = false;
    }

    // Update GPIO 5 test signal
    updateFanOutput();

    // Display sensor readings
    Serial.print("Temperature: ");
    Serial.print(temperature);
    Serial.println(" C");

    Serial.print("Humidity: ");
    Serial.print(humidity);
    Serial.println(" %");

    // Publish data only when MQTT is connected
    if (client.connected()) {
      char tempString[16];
      char humidityString[16];

      dtostrf(temperature, 1, 2, tempString);
      dtostrf(humidity, 1, 2, humidityString);

      bool tempSent =
        client.publish(temperature_topic, tempString);

      bool humiditySent =
        client.publish(humidity_topic, humidityString);

      bool fanSent =
        client.publish(
          fan_topic,
          fanState ? "ON" : "OFF"
        );

      if (tempSent && humiditySent && fanSent) {
        Serial.println("MQTT readings published!");
      } else {
        Serial.println("MQTT publishing failed!");
      }
    } else {
      Serial.println("MQTT offline - local control continues.");
    }

    Serial.println("----------------");
  }
}
