# 🌱 Smart Irrigation System

A full-stack IoT-based smart irrigation system that automates water management using real-time soil moisture data. The system integrates ESP32 hardware, a Django backend, and a modern React frontend to deliver monitoring, control, and automation capabilities.

---

## 🚀 Overview

This project enables intelligent irrigation by:

* Continuously monitoring soil moisture using sensors
* Automatically controlling a water pump based on thresholds
* Allowing manual control via a web/mobile dashboard
* Supporting both auto mode and manual override
* Maintaining historical data for analytics and insights

The system is designed to be scalable and production-ready, with proper authentication, device management, and API design.

---

## 🏗️ Architecture

```
[ Soil Sensor ]
       ↓
[ ESP32 Device ]  →  REST API  →  [ Django Backend ]
       ↓                                ↓
   Relay Control                  Database (SQLite/Postgres)
                                        ↓
                               [ React Frontend ]
```

---

## ⚙️ Tech Stack

### Backend

* Django + Django REST Framework
* JWT Authentication (user)
* API Key Authentication (device)
* SQLite / PostgreSQL

### Frontend

* React (Vite)
* Tailwind CSS
* Capacitor (for mobile support)

### Hardware

* ESP32 (WiFi-enabled microcontroller)
* Soil Moisture Sensor
* Relay Module (Pump control)
* Optional Arduino relay bridge

---

## 📦 Features

### 🌿 Core Functionality

* Real-time soil moisture monitoring
* Pump ON/OFF control
* Auto irrigation based on thresholds
* Manual override via dashboard

### 🔐 Authentication

* JWT-based user authentication
* API key-based device authentication

### 📊 Data & Insights

* Historical moisture readings
* Pump action logs
* Current device status snapshot

### ⚡ Automation

* Auto mode:

  * Pump ON when moisture < 30%
  * Pump OFF when moisture > 60%

---

## 📁 Project Structure

```
iotfarming/
│
├── backend/               # Django backend
│   ├── dashboard/         # Core app (models, APIs)
│   ├── backend/           # Settings & config
│
├── frontend/              # React + Tailwind app
│   ├── src/
│   ├── android/           # Capacitor mobile build
│
├── esp32/                 # ESP32 firmware
├── aurdino/               # Arduino relay controller
│
└── combine_code_files.py  # Utility script
```

---

## 🔌 API Overview

### Authentication

* POST /api/token/ → Get JWT token
* POST /api/token/refresh/

### User APIs

* GET /api/me/
* POST /api/update/ → Toggle pump
* POST /api/auto/ → Enable/disable auto mode

### Device APIs (ESP32)

* POST /api/readings/ → Send moisture data
* GET /api/status/esp/ → Fetch pump + auto state

### Admin APIs

* POST /api/users/ → Create user + device
* POST /api/devices/ → Add device

---

## 🧠 System Logic

### Auto Mode

* Runs server-side decision making
* Uses moisture thresholds:

  * < 30% → Pump ON
  * > 60% → Pump OFF

### Manual Mode

* User controls pump via dashboard
* Commands stored and synced with device

---

## 🔧 Setup Instructions

### 1. Clone the Repository

```bash
git clone <your-repo-url>
cd iotfarming
```

---

### 2. Backend Setup

```bash
cd backend

pip install -r requirements.txt

# Create .env file
DJANGO_SECRET_KEY=your_secret
TIME_ZONE=Asia/Kolkata
ALLOWED_HOSTS=*

python manage.py migrate
python manage.py createsuperuser

# Optional: seed data
python manage.py seed --fresh

python manage.py runserver
```

---

### 3. Frontend Setup

```bash
cd frontend

npm install
npm run dev
```

---

### 4. ESP32 Setup

* Update credentials in esp32.cpp:

  * WiFi SSID & Password
  * API Base URL
  * Device API Key

* Flash code using Arduino IDE / PlatformIO

---

## 🔐 Security Notes

* Device communication is secured via API keys
* User authentication uses JWT tokens
* CORS enabled for frontend integration

---

## 📈 Future Improvements

* Multi-device support per user
* WebSocket-based real-time updates
* Advanced irrigation prediction using ML
* Mobile app optimization
* Offline sync support

---

## 🧪 Testing & Development

* Use Django admin for quick inspection
* Seed command generates test data
* API testing via Postman / curl

---

## 🤝 Contributing

Contributions are welcome. Please open an issue or submit a pull request with clear context and reasoning.

---

## 📄 License

This project is open-source and available under the MIT License.

---

## 👨‍💻 Author

Built with a focus on real-world IoT + software integration, combining embedded systems with scalable backend architecture.
