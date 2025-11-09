#include <WiFi.h>
#include <HTTPClient.h>
#include <ArduinoJson.h>

// ------------------- CONFIG -------------------
const char* ssid = "YOGESH";
const char* password = "11223344";

const char* BASE_URL = "https://iotagri.pythonanywhere.com/api";
const char* DEVICE_ID = "device_001";
const char* API_KEY = "abc12345devicekey";  // Must match Django Device.api_key

#define SOIL_SENSOR_PIN 34
#define RELAY_PIN 27
#define LED_BUILTIN 2 // Onboard blue LED

unsigned long lastUpdate = 0;
int updateInterval = 15000;  // 15 seconds
bool pumpState = false;      // Track current pump state to prevent chatter

// ------------------- HELPER FUNCTIONS -------------------
void blinkLED(int times, int delayMs = 200) {
  for (int i = 0; i < times; i++) {
    digitalWrite(LED_BUILTIN, HIGH);
    delay(delayMs);
    digitalWrite(LED_BUILTIN, LOW);
    delay(delayMs);
  }
}

void updatePumpStatusToServer(bool state) {
  if (WiFi.status() == WL_CONNECTED) {
    HTTPClient http;
    String url = String(BASE_URL) + "/pump-status/";

    http.begin(url);
    http.addHeader("Content-Type", "application/json");
    http.addHeader("X-API-KEY", API_KEY);

    StaticJsonDocument<100> doc;
    doc["device_id"] = DEVICE_ID;
    doc["pump_on"] = state;

    String body;
    serializeJson(doc, body);

    int code = http.POST(body);
    Serial.printf("🔄 Pump status sync -> HTTP %d\n", code);
    http.end();
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

  Serial.println("🌐 Connecting to WiFi...");
  WiFi.begin(ssid, password);

  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }

  Serial.println("\n✅ Connected to WiFi");
  blinkLED(3, 200);
}

// ------------------- FUNCTIONS -------------------

// Send soil moisture reading to Django
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
    Serial.printf("📤 Sent Reading -> HTTP %d | Moisture: %.2f%%\n", httpCode, moisture_percent);

    if (httpCode == 201) {
      blinkLED(2, 200);
      http.end();
      return true;
    } else {
      blinkLED(5, 200);
      Serial.println("❌ Failed to store reading");
    }

    http.end();
  } else {
    blinkLED(3, 200);
    Serial.println("📡 WiFi disconnected");
  }
  return false;
}

// Fetch status & act on pump control
void fetchPumpCommand() {
  if (WiFi.status() == WL_CONNECTED) {
    HTTPClient http;
    String url = String(BASE_URL) + "/status/esp/";

    http.begin(url);
    http.addHeader("X-API-KEY", API_KEY);

    int httpCode = http.GET();
    Serial.printf("📥 Fetch Command -> HTTP %d\n", httpCode);

    if (httpCode == 200) {
      String payload = http.getString();
      Serial.println("Response: " + payload);

      StaticJsonDocument<512> doc;
      DeserializationError err = deserializeJson(doc, payload);
      blinkLED(5, 200);
      if (!err) {
        float soil_moisture = doc["soil_moisture"];
        bool motor_status = doc["motor_status"];
        bool is_auto_mode = doc["is_auto_mode"];

        Serial.printf("🌱 Moisture: %.2f | Auto: %d | Motor: %d\n",
                      soil_moisture, is_auto_mode, motor_status);

        float dry_threshold = 40.0;
        float wet_threshold = 70.0;

        if (is_auto_mode) {
          blinkLED(2, 200);
          // --- Auto Mode (with hysteresis) ---
          if (soil_moisture < dry_threshold && !pumpState) {
            digitalWrite(RELAY_PIN, HIGH);
            digitalWrite(LED_BUILTIN, HIGH);
            pumpState = true;
            //updatePumpStatusToServer(true);
            Serial.println("💧 Auto Mode: Pump ON (soil too dry)");
          } else if (soil_moisture > wet_threshold && pumpState) {
            digitalWrite(RELAY_PIN, LOW);
            digitalWrite(LED_BUILTIN, LOW);
            pumpState = false;
            //updatePumpStatusToServer(false);
            Serial.println("🛑 Auto Mode: Pump OFF (soil wet enough)");
          } else {
            Serial.println("⚖️ Auto Mode: No change (stable moisture)");
          }
        } else {
          // --- Manual Mode ---
          blinkLED(4, 200);
          if (motor_status && !pumpState) {
            digitalWrite(RELAY_PIN, HIGH);
            digitalWrite(LED_BUILTIN, HIGH);
            pumpState = true;
            //updatePumpStatusToServer(true);
            blinkLED(3, 150);
            Serial.println("💧 Manual Mode: Pump ON (by command)");
          } else if (!motor_status && pumpState) {
            digitalWrite(RELAY_PIN, LOW);
            digitalWrite(LED_BUILTIN, LOW);
            pumpState = false;
            //updatePumpStatusToServer(false);
            blinkLED(2, 150);
            Serial.println("🛑 Manual Mode: Pump OFF (by command)");
          } else {
            Serial.println("⚖️ Manual Mode: No change");
          }
        }
      } else {
        Serial.println("❌ JSON Parse Error");
      }
    } else {
      Serial.println("❌ Failed to fetch status");
      blinkLED(3, 200);
    }

    http.end();
  } else {
    blinkLED(3, 200);
    Serial.println("📡 WiFi disconnected");
  }
}

// ------------------- LOOP -------------------
void loop() {
  unsigned long now = millis();
  if (now - lastUpdate > updateInterval) {
    bool sent = sendSoilReading();
    if (sent) {
      fetchPumpCommand();
    }
    lastUpdate = now;
  }
}
