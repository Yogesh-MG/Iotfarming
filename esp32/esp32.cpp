#include <WiFi.h>
#include <HTTPClient.h>
#include <ArduinoJson.h>

// ------------------- CONFIG -------------------
const char* ssid = "YOGESH";
const char* password = "11223344";

const char* BASE_URL = "https://iotagri.pythonanywhere.com/api";
const char* DEVICE_ID = "device_001";
const char* API_KEY = "abc12345devicekey";  // Must match the Device.api_key in Django

#define SOIL_SENSOR_PIN 34
#define RELAY_PIN 27
#define LED_BUILTIN 2 // Onboard blue LED

unsigned long lastUpdate = 0;
int updateInterval = 15000;  // 15 seconds

// ------------------- HELPER FUNCTIONS -------------------
void blinkLED(int times, int delayMs) {
  for (int i = 0; i < times; i++) {
    digitalWrite(LED_BUILTIN, HIGH);
    delay(delayMs);
    digitalWrite(LED_BUILTIN, LOW);
    delay(delayMs);
  }
}

// ------------------- SETUP -------------------
void setup() {
  Serial.begin(115200);
  pinMode(SOIL_SENSOR_PIN, INPUT);
  pinMode(RELAY_PIN, OUTPUT);
  pinMode(LED_BUILTIN, OUTPUT);

  digitalWrite(RELAY_PIN, LOW);
  digitalWrite(LED_BUILTIN, LOW);

  WiFi.begin(ssid, password);
  Serial.println("Connecting to WiFi...");

  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }

  Serial.println("\n✅ Connected to WiFi");
  blinkLED(4, 500);  // Blink 4 times (connected to WiFi)
}

// ------------------- FUNCTIONS -------------------

// Send moisture reading to Django
bool sendSoilReading() {
  if (WiFi.status() == WL_CONNECTED) {
    HTTPClient http;
    String url = String(BASE_URL) + "/readings/";

    http.begin(url);
    http.addHeader("Content-Type", "application/json");
    http.addHeader("X-API-KEY", API_KEY);

    int moisture_value = analogRead(SOIL_SENSOR_PIN);
    float moisture_percent = map(moisture_value, 4095, 0, 0, 100);

    StaticJsonDocument<200> doc;
    doc["device_id"] = DEVICE_ID;
    doc["moisture"] = moisture_percent;

    String requestBody;
    serializeJson(doc, requestBody);

    int httpCode = http.POST(requestBody);
    Serial.printf("📤 Sent Reading -> HTTP %d\n", httpCode);

    if (httpCode == 201) {
      blinkLED(5, 1000); // Blink 5 times = success
      Serial.println("✅ Reading stored successfully");
      http.end();
      return true;
    } else {
      blinkLED(3, 1000); // Blink 3 times = failure
      Serial.println("❌ Failed to store reading");
    }

    http.end();
  } else {
    blinkLED(3, 1000); // Blink 3 times = WiFi disconnected
  }
  return false;
}

// Fetch pump commands (ON/OFF) from Django
void fetchPumpCommand() {
  if (WiFi.status() == WL_CONNECTED) {
    HTTPClient http;
    String url = String(BASE_URL) + "/status/";

    http.begin(url);
    http.addHeader("X-API-KEY", API_KEY);

    int httpCode = http.GET();
    Serial.printf("📥 Fetch Commands -> HTTP %d\n", httpCode);

    if (httpCode == 200) {
      String payload = http.getString();
      Serial.println("Response: " + payload);

      StaticJsonDocument<512> doc;
      DeserializationError err = deserializeJson(doc, payload);

      if (!err && doc.containsKey("pending_commands")) {
        JsonArray commands = doc["pending_commands"].as<JsonArray>();
        if (commands.size() > 0) {
          String action = commands[0]["action"];
          if (action == "ON") {
            digitalWrite(RELAY_PIN, HIGH);
            digitalWrite(LED_BUILTIN, HIGH);
            Serial.println("💧 Pump turned ON, LED ON");
          } else {
            digitalWrite(RELAY_PIN, LOW);
            digitalWrite(LED_BUILTIN, LOW);
            Serial.println("🛑 Pump turned OFF, LED OFF");
          }
        }
      }
    } else {
      Serial.println("❌ Failed to fetch commands");
      blinkLED(3, 1000); // Blink 3 times for any fetch failure
    }

    http.end();
  } else {
    blinkLED(3, 1000); // Blink 3 times if WiFi disconnected
  }
}

// ------------------- LOOP -------------------
void loop() {
  unsigned long now = millis();
  if (now - lastUpdate > updateInterval) {
    bool sent = sendSoilReading();  // Send sensor data
    if (sent) {
      fetchPumpCommand();           // Only fetch commands if sending succeeded
    }
    lastUpdate = now;
  }
}
