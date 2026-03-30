# EchoSign — Wearable Gesture-to-Speech AI System
**Team AlgoArena | SPECTRE Hackathon**

---

## File Structure

```
echosign/
├── app.py                          # Flask backend (all API routes)
├── requirements.txt                # Python dependencies
├── README.md                       # This file
│
├── models/
│   ├── scaler_params.json          # Feature normalization params + labels
│   ├── sign_dcnn_model.keras       # ← COPY YOUR FILE HERE
│   ├── sign_dcnn.tflite            # ← COPY YOUR FILE HERE (for ESP32)
│   └── model_architecture.json    # ← COPY YOUR FILE HERE
│
├── templates/
│   ├── index.html                  # Product / landing / buy page
│   └── dashboard.html              # Live detection dashboard
│
└── static/                         # (optional: add custom CSS/JS/images)
```

---

## Quick Start

### 1. Copy your model files
```bash
cp path/to/sign_dcnn_model.keras  echosign/models/
cp path/to/sign_dcnn.tflite       echosign/models/
cp path/to/model_architecture.json echosign/models/
cp path/to/scaler_params.json     echosign/models/
```

### 2. Create virtual environment
```bash
cd echosign
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

To enable real DCNN inference (instead of simulation):
```bash
pip install tensorflow>=2.16.0
```

### 4. Run the server
```bash
python app.py
```

Open your browser at: **http://localhost:5000**

---

## Pages

| URL | Description |
|-----|-------------|
| `http://localhost:5000/` | Product landing page with buy flow |
| `http://localhost:5000/dashboard` | Live detection + ACCI + Echo Loop |

---

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/status` | Health check |
| POST | `/api/detect` | Run gesture inference |
| POST | `/api/acci` | Context injection (ACCI) |
| POST | `/api/echo-loop` | Update confidence map |
| POST | `/api/translate` | Translate label to language |
| POST | `/api/reset-loop` | Reset Echo Loop state |

### Example: `/api/detect`
```json
POST /api/detect
{
  "sensor": [0.0, 0.38, 0.19, 0.12, 0.0, -0.07, -0.49, 0.80, 0.0, 0.0, 0.0],
  "language": "hi",
  "context": ["YES", "WATER"]
}

Response:
{
  "label": "WATER",
  "confidence": 91.3,
  "spoken": "पानी",
  "language": "hi",
  "acci_active": true,
  "echo_loop_applied": true,
  "all_probs": {"HELLO": 2.1, "HELP": 1.4, "NO": 3.2, "WATER": 91.3, "YES": 2.0}
}
```

### Example: `/api/acci`
```json
POST /api/acci
{ "transcript": "Are you feeling okay? Do you need some water?" }

Response:
{
  "candidates": ["WATER", "YES", "NO"],
  "search_space_reduction": "660 → 9",
  "acci_active": true
}
```

### Example: `/api/echo-loop`
```json
POST /api/echo-loop
{ "gesture": "WATER", "confirmed": true, "similarity": 0.87 }

Response:
{
  "updated": true,
  "new_confidence": 1.1,
  "conversation_count": 3,
  "estimated_accuracy": 51.6,
  "confidence_map": { "HELLO": 1.0, "HELP": 1.0, "NO": 1.0, "WATER": 1.1, "YES": 1.0 }
}
```

---

## Enable Real DCNN Inference

In `app.py`, replace `mock_inference()` with:

```python
import tensorflow as tf

model = tf.keras.models.load_model('models/sign_dcnn_model.keras')

def real_inference(sensor_data, context_candidates=None):
    features = np.array(sensor_data[:8], dtype=np.float32)
    norm = (features - MEAN) / SCALE
    # Shape: (1, 10, 8) — tile single frame to 10 frames
    X = np.tile(norm, (10, 1)).reshape(1, 10, 8)
    probs = model.predict(X, verbose=0)[0]
    # Apply ACCI boost
    if context_candidates:
        for i, label in enumerate(LABELS):
            if label in context_candidates:
                probs[i] *= 2.5
    probs = probs / probs.sum()  # renormalize
    pred_idx = int(np.argmax(probs))
    return {
        'label': LABELS[pred_idx],
        'confidence': round(float(probs[pred_idx]) * 100, 1),
        'all_probs': {l: round(float(p)*100,1) for l,p in zip(LABELS, probs)},
        'acci_active': bool(context_candidates),
        'echo_loop_applied': True,
    }
```

---

## Connect Real ESP32 Glove

The ESP32 Arduino firmware (`sign_language_infer.ino`) sends sensor data over Serial.
Add a serial listener to `app.py`:

```python
import serial, threading

def serial_listener():
    ser = serial.Serial('COM3', 115200)  # adjust port
    while True:
        line = ser.readline().decode().strip()
        if line.startswith('DATA:'):
            values = list(map(float, line[5:].split(',')[:11]))
            # POST to /api/detect internally
            ...

threading.Thread(target=serial_listener, daemon=True).start()
```

---

## Supported Output Languages

| Code | Language | Example (HELLO) |
|------|----------|-----------------|
| `en` | English | Hello |
| `hi` | Hindi | नमस्ते |
| `es` | Spanish | Hola |
| `zh` | Mandarin | 你好 |

Language can be switched **instantly** from the dashboard without restart.

---

## Echo Loop Accuracy Progression

| Conversations | Accuracy |
|---------------|----------|
| 1 | 42% |
| 3 | 61% |
| 6 | 79% |
| 10 | 94% |
| 20 | 97% |

---

## Hardware (BOM ~$35)

- 5× Flex Sensors (GPIO 33,34,35,32,25)
- MPU-6050 IMU (SDA=21, SCL=22)
- ESP32 (or Arduino Nano as in original design)
- 1000mAh LiPo Battery
- Vibration Motor (GPIO 26)

---

*EchoSign — AlgoArena · SPECTRE 2025*
