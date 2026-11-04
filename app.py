"""
EchoSign — Flask Backend
Serves the product page and handles:
  - /api/connect        : verify ESP32 COM port
  - /api/detect         : receive sensor data, run inference
  - /api/echo-loop      : update confidence map (Echo Loop)
  - /api/acci           : context injection (ACCI)
  - /api/translate      : translate gesture label to target language
"""

from flask import Flask, render_template, request, jsonify
import json, os, time, random
import numpy as np

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'echosign-secret')

# ── Load scaler params ─────────────────────────────────────────
BASE = os.path.dirname(__file__)
with open(os.path.join(BASE, 'models', 'scaler_params.json')) as f:
    SCALER = json.load(f)

MEAN   = np.array(SCALER['mean'],  dtype=np.float32)
SCALE  = np.array(SCALER['scale'], dtype=np.float32)
LABELS = SCALER['labels']          # ['HELLO','HELP','NO','WATER','YES']
FEATURE_COLS = SCALER['feature_cols']

# ── In-memory confidence map per session (Echo Loop) ──────────
# In production: persist to DB per user
confidence_map = {label: 1.0 for label in LABELS}
conversation_count = 0

# ── Translation dict (simulated — replace with real API) ───────
TRANSLATIONS = {
    'HELLO': {'en':'Hello',  'es':'Hola',   'hi':'नमस्ते', 'zh':'你好'},
    'HELP':  {'en':'Help',   'es':'Ayuda',  'hi':'मदद',    'zh':'帮助'},
    'NO':    {'en':'No',     'es':'No',     'hi':'नहीं',   'zh':'不'},
    'WATER': {'en':'Water',  'es':'Agua',   'hi':'पानी',   'zh':'水'},
    'YES':   {'en':'Yes',    'es':'Sí',     'hi':'हाँ',    'zh':'是'},
}

def normalize(X: np.ndarray) -> np.ndarray:
    """Normalize feature array using stored scaler params."""
    return (X - MEAN) / SCALE

def softmax(x):
    e = np.exp(x - np.max(x))
    return e / e.sum()

def mock_inference(sensor_data: list, context_candidates: list = None) -> dict:
    """
    Simulates DCNN inference.
    In production: load sign_dcnn_model.keras and run model.predict()
    Also applies ACCI filtering if candidates provided.
    """
    # Simulate feature extraction from raw sensor reading
    features = np.array(sensor_data[:8], dtype=np.float32)
    norm_features = normalize(features)

    # Simulate logits (replace with real model.predict)
    rng = np.random.default_rng(int(abs(norm_features.sum() * 1000)) % 99999)
    logits = rng.normal(0, 1, len(LABELS)).astype(np.float32)

    # ACCI: boost candidates from context
    if context_candidates:
        for i, label in enumerate(LABELS):
            if label in context_candidates:
                logits[i] += 2.5   # strong boost for context matches

    # Echo Loop: apply personal confidence map
    for i, label in enumerate(LABELS):
        logits[i] *= confidence_map[label]

    probs = softmax(logits)
    pred_idx = int(np.argmax(probs))
    pred_label = LABELS[pred_idx]
    confidence = float(probs[pred_idx])

    return {
        'label': pred_label,
        'confidence': round(confidence * 100, 1),
        'all_probs': {l: round(float(p)*100,1) for l,p in zip(LABELS, probs)},
        'acci_active': bool(context_candidates),
        'echo_loop_applied': True,
    }

# ── Routes ─────────────────────────────────────────────────────
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/dashboard')
def dashboard():
    return render_template('dashboard.html')

@app.route('/api/status')
def api_status():
    return jsonify({'status': 'ok', 'labels': LABELS, 'version': '1.0.0'})

@app.route('/api/detect', methods=['POST'])
def api_detect():
    """
    Receive 11D sensor vector + context, return prediction.
    Body: { sensor: [f0..f4, ax,ay,az,gx,gy,gz], context: [...], language: 'en' }
    """
    body   = request.get_json(force=True)
    sensor = body.get('sensor', [0.0]*11)
    lang   = body.get('language', 'en')
    ctx    = body.get('context', [])

    result = mock_inference(sensor, ctx if ctx else None)
    label  = result['label']

    # Translate
    result['spoken'] = TRANSLATIONS.get(label, {}).get(lang, label)
    result['language'] = lang
    result['timestamp'] = int(time.time() * 1000)
    return jsonify(result)

@app.route('/api/echo-loop', methods=['POST'])
def api_echo_loop():
    """
    Echo Loop: receive confirmation feedback, update confidence map.
    Body: { gesture: 'YES', confirmed: true, similarity: 0.87 }
    """
    global conversation_count
    body      = request.get_json(force=True)
    gesture   = body.get('gesture', '')
    confirmed = body.get('confirmed', False)
    similarity= float(body.get('similarity', 0.0))

    if gesture in confidence_map:
        if confirmed and similarity > 0.75:
            confidence_map[gesture] = min(2.0, confidence_map[gesture] + 0.1)
        elif similarity < 0.40:
            confidence_map[gesture] = max(0.5, confidence_map[gesture] - 0.05)
        conversation_count += 1

    # Compute accuracy estimate based on conversation count
    acc = min(97, 42 + conversation_count * 3.2)

    return jsonify({
        'updated': True,
        'gesture': gesture,
        'new_confidence': round(confidence_map.get(gesture, 1.0), 3),
        'conversation_count': conversation_count,
        'estimated_accuracy': round(acc, 1),
        'confidence_map': {k: round(v,3) for k,v in confidence_map.items()},
    })

@app.route('/api/acci', methods=['POST'])
def api_acci():
    """
    ACCI: receive partner speech transcript, return narrowed gesture candidates.
    Body: { transcript: "Are you okay? Do you need something?" }
    Simulates LLM context extraction.
    """
    body       = request.get_json(force=True)
    transcript = body.get('transcript', '').lower()

    # Rule-based simulation (replace with Groq/LLM call)
    candidates = []
    keyword_map = {
        'HELLO': ['hello','hi','hey','greet','name','meet'],
        'HELP':  ['help','assist','support','hurt','pain','problem'],
        'NO':    ['no','not','refuse','disagree','stop','dont'],
        'WATER': ['water','drink','thirsty','liquid','hydrat'],
        'YES':   ['yes','okay','sure','agree','correct','right','good'],
    }
    for label, keywords in keyword_map.items():
        if any(kw in transcript for kw in keywords):
            candidates.append(label)

    if not candidates:
        candidates = LABELS  # fallback: all labels

    search_space = f"{len(LABELS)*132} → {len(candidates)*3}"
    return jsonify({
        'candidates': candidates,
        'search_space_reduction': search_space,
        'transcript': transcript[:100],
        'acci_active': len(candidates) < len(LABELS),
    })

@app.route('/api/translate', methods=['POST'])
def api_translate():
    """Translate a gesture label to target language."""
    body    = request.get_json(force=True)
    label   = body.get('label', '').upper()
    lang    = body.get('language', 'en')
    spoken  = TRANSLATIONS.get(label, {}).get(lang, label)
    return jsonify({'label': label, 'language': lang, 'spoken': spoken})

@app.route('/api/reset-loop', methods=['POST'])
def api_reset_loop():
    """Reset Echo Loop confidence map."""
    global confidence_map, conversation_count
    confidence_map = {label: 1.0 for label in LABELS}
    conversation_count = 0
    return jsonify({'reset': True})

if __name__ == '__main__':
    debug_mode = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'
    app.run(debug=debug_mode, host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
