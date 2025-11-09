// ------------------------------------
//  Arduino Relay Controller
//  Listens to ESP32 on pin 7
//  Controls Relay on pin 8
// ------------------------------------

#define SIGNAL_PIN 7   // Input signal from ESP32 (GPIO 27)
#define RELAY_PIN 8    // Relay control pin

void setup() {
  Serial.begin(9600);

  pinMode(SIGNAL_PIN, INPUT);
  pinMode(RELAY_PIN, OUTPUT);

  digitalWrite(RELAY_PIN, LOW); // Start with relay OFF
  Serial.println("✅ Arduino ready - Waiting for signal from ESP32...");
}

void loop() {
  int espSignal = digitalRead(SIGNAL_PIN); // Read signal from ESP32

  if (espSignal == HIGH) {
    digitalWrite(RELAY_PIN, HIGH);   // Turn ON relay
    Serial.println("💧 Pump ON (signal HIGH)");
  } else {
    digitalWrite(RELAY_PIN, LOW);    // Turn OFF relay
    Serial.println("🛑 Pump OFF (signal LOW)");
  }

  delay(500); // Read every 0.5 seconds
}
