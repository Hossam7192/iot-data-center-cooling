
#include <WiFi.h>
#include <PubSubClient.h>
#include <DHT.h>

// 1. Wi-Fi settings
const char* ssid = "YOUR_WIFI_NAME";
const char* password = "YOUR_WIFI_PASSWORD";

// 2. MQTT settings
const char* mqtt_server = "broker.emqx.io";
const int mqtt_port = 1883;

const char* temperature_topic =
  "hossam7192/datacenter/temperature";

const char* humidity_topic =
  "hossam7192/datacenter/humidity";

// 3. DHT22 sensor settings
#define DHTPIN 4
#define DHTTYPE DHT22

DHT dht(DHTPIN, DHTTYPE);

WiFiClient espClient;
PubSubClient client(espClient);

// Connect to the MQTT broker
void connectMQTT() {
  while (!client.connected()) {
    Serial.println("Connecting to MQTT...");

    String clientId = "ESP32S3-" +
                      String((uint32_t)ESP.getEfuseMac(), HEX);

    if (client.connect(clientId.c_str())) {
      Serial.println("MQTT connected!");
    } else {
      Serial.print("MQTT failed. State: ");
      Serial.println(client.state());
      delay(5000);
    }
  }
}

void setup() {
  Serial.begin(115200);
  delay(1000);

  // Start the temperature sensor
  dht.begin();

  // Connect to Wi-Fi
  WiFi.begin(ssid, password);

  Serial.print("Connecting to Wi-Fi");

  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }

  Serial.println();
  Serial.println("Wi-Fi connected!");

  // Configure the MQTT broker
  client.setServer(mqtt_server, mqtt_port);
}

void loop() {
  if (WiFi.status() != WL_CONNECTED) {
    delay(1000);
    return;
  }

  if (!client.connected()) {
    connectMQTT();
  }

  client.loop();

  static unsigned long lastReading = 0;

  if (millis() - lastReading >= 5000) {
    lastReading = millis();

    // Read the DHT22 sensor
    float temperature = dht.readTemperature();
    float humidity = dht.readHumidity();

    // Check that readings are valid
    if (isnan(temperature) || isnan(humidity)) {
      Serial.println("Failed to read DHT22!");
      return;
    }

    // Convert readings to text for MQTT
    char tempString[16];
    char humidityString[16];

    dtostrf(temperature, 1, 2, tempString);
    dtostrf(humidity, 1, 2, humidityString);

    // Publish sensor readings
    bool tempSent =
      client.publish(temperature_topic, tempString);

    bool humiditySent =
      client.publish(humidity_topic, humidityString);

    // Display results
    Serial.print("Temperature: ");
    Serial.print(tempString);
    Serial.println(" C");

    Serial.print("Humidity: ");
    Serial.print(humidityString);
    Serial.println(" %");

    if (tempSent && humiditySent) {
      Serial.println("MQTT readings published!");
    } else {
      Serial.println("MQTT publishing failed!");
    }

    Serial.println("----------------");
  }
}
