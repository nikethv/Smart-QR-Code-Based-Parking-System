from flask import Flask, render_template, request, jsonify, redirect
import random
import json
import time
import base64
import io
import re
import os

# Load environment variables from .env file if it exists
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # python-dotenv not installed, continue without it

# Handle optional dependencies gracefully
try:
    import qrcode
    QRCODE_AVAILABLE = True
except ImportError:
    QRCODE_AVAILABLE = False

try:
    from twilio.rest import Client
    TWILIO_AVAILABLE = True
except ImportError:
    TWILIO_AVAILABLE = False
    Client = None

app = Flask(__name__)

# In-memory block/slot storage
blocks = {
    "techpark": {str(i): {"status": "available", "device_info": None, "release_qr": None} for i in range(1,51)},
    "medical": {str(i): {"status": "available", "device_info": None, "release_qr": None} for i in range(1, 51)},
    "mba": {str(i): {"status": "available", "device_info": None, "release_qr": None} for i in range(1, 51)},
    "java": {str(i): {"status": "available", "device_info": None, "release_qr": None} for i in range(1, 51)},
    "fablab": {str(i): {"status": "available", "device_info": None, "release_qr": None} for i in range(1, 51)},
    "dental": {str(i): {"status": "available", "device_info": None, "release_qr": None} for i in range(1, 51)},
}

otps = {}

# Twilio config - Use environment variables for security
ACCOUNT_SID = os.environ.get("TWILIO_ACCOUNT_SID", "your_twilio_account_sid_here")
AUTH_TOKEN = os.environ.get("TWILIO_AUTH_TOKEN", "your_twilio_auth_token_here")
FROM_PHONE_NUMBER = os.environ.get("TWILIO_FROM_PHONE", "+1234567890")

if TWILIO_AVAILABLE and ACCOUNT_SID != "your_twilio_account_sid_here":
    client = Client(ACCOUNT_SID, AUTH_TOKEN)
else:
    client = None

# === Utilities ===
BASE_URL = os.environ.get("BASE_URL", "http://localhost:5000/")

def normalize_phone(phone):
    """Normalize phone number to international format"""
    digits = re.sub(r'\D', '', str(phone))
    if digits.startswith("91") and len(digits) == 12:
        return "+" + digits
    if len(digits) == 10 and digits[0] in "6789":
        return "+91" + digits
    raise ValueError("Invalid phone number format")

def generate_qr(data):
    """Generate QR code for given data"""
    if not QRCODE_AVAILABLE:
        return None
    qr = qrcode.make(str(data))
    buffer = io.BytesIO()
    qr.save(buffer, format="PNG")
    return base64.b64encode(buffer.getvalue()).decode()

def generate_otp():
    """Generate 6-digit OTP"""
    return str(random.randint(100000, 999999))

def get_booking_message(otp):
    """Get booking OTP message"""
    return f"""🌟 Your OTP is: {otp}

You're almost there! Let's make today amazing 🌈✨

– Team Smart Parking 💛"""

def get_release_message(otp):
    """Get release OTP message"""
    return f"""🔓 Your release OTP is: {otp}

Thanks for making space! Keep shining 🌟✨

– Team Smart Parking 💛"""

def send_otp(phone_number, otp, message_text):
    """Send OTP via Twilio SMS"""
    if not TWILIO_AVAILABLE or not client:
        print(f"🔸 TWILIO NOT AVAILABLE - Would send OTP {otp} to {phone_number}")
        return True
    
    try:
        phone_number = normalize_phone(phone_number)
        message = client.messages.create(
            body=message_text,
            from_=FROM_PHONE_NUMBER,
            to=phone_number
        )
        print(f"✅ OTP sent! SID: {message.sid}, Status: {message.status}")
        return True
    except Exception as e:
        print(f"❌ Error sending OTP: {e}")
        return False

def save_booking_info(block, slot, phone_number, device_info):
    """Save booking information to JSON file"""
    try:
        with open("bookings.json", "r") as f:
            bookings = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        bookings = {}

    bookings[f"{block}_{slot}"] = {
        "phone_number": phone_number,
        "device_info": device_info,
        "timestamp": int(time.time())
    }

    with open("bookings.json", "w") as f:
        json.dump(bookings, f, indent=2)

# === Device Fingerprinting Utilities ===

def extract_device_fingerprint(request_data):
    """Extract device fingerprint from request data"""
    if not request_data:
        return {}
        
    fingerprint_data = {
        'fingerprint_hash': request_data.get('fingerprint', ''),
        'user_agent': request_data.get('userAgent', ''),
        'platform': request_data.get('platform', ''),
        'language': request_data.get('language', ''),
        'timezone': request_data.get('timezone', ''),
        'screen_resolution': f"{request_data.get('screen', {}).get('width', 0)}x{request_data.get('screen', {}).get('height', 0)}",
        'color_depth': request_data.get('screen', {}).get('colorDepth', 0),
        'viewport': f"{request_data.get('viewport', {}).get('width', 0)}x{request_data.get('viewport', {}).get('height', 0)}",
        'touch_support': request_data.get('touchSupport', False),
        'webgl_info': request_data.get('webGL', {}),
        'canvas_fingerprint': request_data.get('canvas', ''),
        'audio_fingerprint': request_data.get('audioContext', ''),
        'fonts': request_data.get('fonts', []),
        'plugins': request_data.get('plugins', []),
        'storage_support': {
            'localStorage': request_data.get('localStorage', False),
            'sessionStorage': request_data.get('sessionStorage', False),
            'indexedDB': request_data.get('indexedDB', False)
        },
        'device_memory': request_data.get('deviceMemory', 'unknown'),
        'hardware_concurrency': request_data.get('hardwareConcurrency', 'unknown'),
        'connection_info': request_data.get('connection', {}),
        'battery_info': request_data.get('battery', {}),
        'webrtc_fingerprint': request_data.get('webRTC', ''),
        'media_devices': request_data.get('mediaDevices', []),
        'permissions': request_data.get('permissions', {}),
        'features': {
            'webWorker': request_data.get('webWorker', False),
            'serviceWorker': request_data.get('serviceWorker', False),
            'geolocation': request_data.get('geolocation', False),
            'notification': request_data.get('notification', False)
        }
    }
    return fingerprint_data

def save_device_fingerprint(phone_number, fingerprint_data):
    """Save device fingerprint to file"""
    try:
        with open("device_fingerprints.json", "r") as f:
            fingerprints = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        fingerprints = {}
    
    if phone_number not in fingerprints:
        fingerprints[phone_number] = []
    
    fingerprint_entry = {
        **fingerprint_data,
        'timestamp': int(time.time()),
        'ip_address': request.remote_addr,
        'session_id': f"session_{int(time.time())}_{random.randint(1000, 9999)}"
    }
    
    fingerprints[phone_number].append(fingerprint_entry)
    
    # Keep only last 10 fingerprints per user
    if len(fingerprints[phone_number]) > 10:
        fingerprints[phone_number] = fingerprints[phone_number][-10:]
    
    with open("device_fingerprints.json", "w") as f:
        json.dump(fingerprints, f, indent=2)
    
    return fingerprint_entry

def verify_device_fingerprint(phone_number, current_fingerprint):
    """Verify if device fingerprint matches previous records"""
    try:
        with open("device_fingerprints.json", "r") as f:
            fingerprints = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {
            "is_trusted": False, 
            "confidence": 0, 
            "reason": "No previous records",
            "risk_level": "UNKNOWN"
        }
    
    user_fingerprints = fingerprints.get(phone_number, [])
    if not user_fingerprints:
        return {
            "is_trusted": False, 
            "confidence": 0, 
            "reason": "No previous fingerprints for this user",
            "risk_level": "NEW_USER"
        }
    
    # Calculate similarity score
    current_hash = current_fingerprint.get('fingerprint_hash', '')
    previous_hashes = [fp.get('fingerprint_hash', '') for fp in user_fingerprints]
    
    # Exact match
    if current_hash and current_hash in previous_hashes:
        return {
            "is_trusted": True, 
            "confidence": 100, 
            "reason": "Exact fingerprint match",
            "risk_level": "LOW"
        }
    
    # Similarity check based on key components
    similarity_score = calculate_fingerprint_similarity(current_fingerprint, user_fingerprints[-1])
    
    if similarity_score >= 85:
        return {
            "is_trusted": True, 
            "confidence": similarity_score, 
            "reason": "Very high similarity match",
            "risk_level": "LOW"
        }
    elif similarity_score >= 70:
        return {
            "is_trusted": True, 
            "confidence": similarity_score, 
            "reason": "High similarity match",
            "risk_level": "LOW"
        }
    elif similarity_score >= 50:
        return {
            "is_trusted": True, 
            "confidence": similarity_score, 
            "reason": "Moderate similarity - device may have changed",
            "risk_level": "MEDIUM",
            "warning": "Device configuration appears modified"
        }
    else:
        return {
            "is_trusted": False, 
            "confidence": similarity_score, 
            "reason": "Low similarity - likely different device",
            "risk_level": "HIGH"
        }

def calculate_fingerprint_similarity(current, previous):
    """Calculate similarity percentage between two fingerprints"""
    if not current or not previous:
        return 0
    
    similarity_weights = {
        'user_agent': 25,
        'platform': 20,
        'screen_resolution': 15,
        'timezone': 10,
        'language': 10,
        'hardware_concurrency': 8,
        'device_memory': 7,
        'canvas_fingerprint': 5
    }
    
    total_score = 0
    total_weight = 0
    
    for key, weight in similarity_weights.items():
        current_val = str(current.get(key, ''))
        previous_val = str(previous.get(key, ''))
        
        if current_val and previous_val:
            total_weight += weight
            if current_val == previous_val:
                total_score += weight
            elif key == 'user_agent' and current_val[:50] == previous_val[:50]:
                # Partial match for user agent (version changes)
                total_score += weight * 0.7
    
    return round((total_score / total_weight * 100) if total_weight > 0 else 0, 2)

def get_device_risk_score(fingerprint_data, phone_number):
    """Calculate risk score for the device"""
    risk_score = 0
    risk_factors = []
    
    # Check for missing or suspicious fingerprint components
    if not fingerprint_data.get('fingerprint_hash'):
        risk_score += 30
        risk_factors.append("Missing fingerprint data")
    
    if not fingerprint_data.get('user_agent') or fingerprint_data.get('user_agent') == 'unknown':
        risk_score += 25
        risk_factors.append("Missing or suspicious user agent")
    
    # Check for automation indicators
    user_agent = str(fingerprint_data.get('user_agent', '')).lower()
    automation_keywords = ['headless', 'phantom', 'selenium', 'webdriver', 'bot', 'crawler']
    if any(keyword in user_agent for keyword in automation_keywords):
        risk_score += 40
        risk_factors.append("Possible automation detected in user agent")
    
    # Check WebGL renderer for virtualization
    webgl_info = fingerprint_data.get('webgl_info', {})
    if isinstance(webgl_info, dict):
        renderer = str(webgl_info.get('renderer', '')).lower()
        if any(virt in renderer for virt in ['swiftshader', 'llvmpipe', 'mesa', 'virtualbox', 'vmware']):
            risk_score += 30
            risk_factors.append("Virtual/emulated graphics detected")
    
    # Check plugins
    plugins = fingerprint_data.get('plugins', [])
    if not plugins or len(plugins) == 0:
        risk_score += 15
        risk_factors.append("No browser plugins detected")
    
    # Check for consistent screen/viewport ratio
    screen_res = fingerprint_data.get('screen_resolution', '0x0')
    viewport = fingerprint_data.get('viewport', '0x0')
    try:
        screen_w, screen_h = map(int, str(screen_res).split('x'))
        viewport_w, viewport_h = map(int, str(viewport).split('x'))
        if screen_w > 0 and viewport_w > 0:
            ratio = viewport_w / screen_w
            if ratio > 1.1 or ratio < 0.3:  # Unusual viewport to screen ratio
                risk_score += 20
                risk_factors.append("Unusual screen to viewport ratio")
    except:
        risk_score += 10
        risk_factors.append("Invalid screen dimensions")
    
    # Check device verification history
    verification = verify_device_fingerprint(phone_number, fingerprint_data)
    if not verification['is_trusted']:
        if verification['confidence'] < 30:
            risk_score += 35
            risk_factors.append("Completely unknown device")
        elif verification['confidence'] < 60:
            risk_score += 20
            risk_factors.append("Partially recognized device")
    
    # Check for suspicious feature combinations
    features = fingerprint_data.get('features', {})
    if not features.get('webWorker') and not features.get('serviceWorker'):
        risk_score += 10
        risk_factors.append("Limited browser feature support")
    
    return {
        'risk_score': min(risk_score, 100),
        'risk_level': 'HIGH' if risk_score >= 70 else 'MEDIUM' if risk_score >= 40 else 'LOW',
        'risk_factors': risk_factors,
        'confidence': verification.get('confidence', 0)
    }

def log_security_event(phone_number, event_type, details):
    """Log security events for monitoring"""
    try:
        with open("security_log.json", "r") as f:
            logs = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        logs = []
    
    log_entry = {
        'timestamp': int(time.time()),
        'phone_number': phone_number,
        'event_type': event_type,
        'details': details,
        'ip_address': request.remote_addr,
        'user_agent': request.headers.get('User-Agent', 'Unknown')
    }
    
    logs.append(log_entry)
    
    # Keep only last 1000 log entries
    if len(logs) > 1000:
        logs = logs[-1000:]
    
    with open("security_log.json", "w") as f:
        json.dump(logs, f, indent=2)

# === Hospital Priority System Configuration ===
HOSPITAL_STAFF_IDS = {
    # Emergency Staff (Highest Priority - Level 1)
    "EMRG001": {"name": "Dr. Emergency Chief", "department": "Emergency", "priority": 1},
    "EMRG002": {"name": "Emergency Nurse", "department": "Emergency", "priority": 1},
    "EMRG003": {"name": "Emergency Technician", "department": "Emergency", "priority": 1},
    # Doctors (High Priority - Level 2)
    "DOC001": {"name": "Dr. Cardiology", "department": "Cardiology", "priority": 2},
    "DOC002": {"name": "Dr. Surgery", "department": "Surgery", "priority": 2},
    "DOC003": {"name": "Dr. Pediatrics", "department": "Pediatrics", "priority": 2},
    "DOC004": {"name": "Dr. Neurology", "department": "Neurology", "priority": 2},
    "DOC005": {"name": "Dr. Orthopedics", "department": "Orthopedics", "priority": 2},
    # Nurses & Faculty (Medium Priority - Level 3)
    "NRS001": {"name": "ICU Nurse", "department": "ICU", "priority": 3},
    "NRS002": {"name": "General Nurse", "department": "General", "priority": 3},
    "NRS003": {"name": "Pediatric Nurse", "department": "Pediatrics", "priority": 3},
    "NRS004": {"name": "Surgery Nurse", "department": "Surgery", "priority": 3},
    "MED001": {"name": "Prof. Medicine", "department": "Medical College", "priority": 3},
    "MED002": {"name": "Prof. Anatomy", "department": "Medical College", "priority": 3},
    "MED003": {"name": "Prof. Physiology", "department": "Medical College", "priority": 3},
    "DEN001": {"name": "Dr. Dental Surgery", "department": "Dental College", "priority": 3},
    "DEN002": {"name": "Dr. Orthodontics", "department": "Dental College", "priority": 3},
    "DEN003": {"name": "Dr. Periodontics", "department": "Dental College", "priority": 3},
    # Support Staff (Normal Priority - Level 4)
    "STF001": {"name": "Lab Technician", "department": "Laboratory", "priority": 4},
    "STF002": {"name": "Administrator", "department": "Admin", "priority": 4},
    "STF003": {"name": "Radiology Tech", "department": "Radiology", "priority": 4},
    "STF004": {"name": "Pharmacist", "department": "Pharmacy", "priority": 4},
}

PRIORITY_SLOTS = {
    "medical": [str(i) for i in range(1, 9)],  # Slots 1-8 reserved for priority
    "dental": [str(i) for i in range(1, 6)],   # Slots 1-5 reserved for priority
}

hospital_bookings = {}

# --- Hospital Priority Utilities ---
def is_hospital_staff(staff_id):
    return staff_id in HOSPITAL_STAFF_IDS

def get_staff_priority(staff_id):
    if staff_id in HOSPITAL_STAFF_IDS:
        return HOSPITAL_STAFF_IDS[staff_id]["priority"]
    return 5

def get_staff_info(staff_id):
    staff_data = HOSPITAL_STAFF_IDS.get(staff_id)
    if staff_data:
        return {
            "staff_id": staff_id,
            "name": staff_data["name"],
            "department": staff_data["department"],
            "role": staff_data.get("role", staff_data["name"]),  # Use name as role if no role specified
            "priority": staff_data["priority"]
        }
    return None

def get_available_priority_slots(priority_type):
    available_slots = []
    
    if priority_type == "medical":
        # Check slots in medical block
        if "medical" in blocks:
            for slot in PRIORITY_SLOTS["medical"]:
                if slot in blocks["medical"] and blocks["medical"][slot]["status"] == "available":
                    available_slots.append({"block": "medical", "slot": slot})
    
    elif priority_type == "dental":
        # Check slots in dental block
        if "dental" in blocks:
            for slot in PRIORITY_SLOTS["dental"]:
                if slot in blocks["dental"] and blocks["dental"][slot]["status"] == "available":
                    available_slots.append({"block": "dental", "slot": slot})
    
    return available_slots

def can_book_priority_slot(staff_id, block, slot):
    if not is_hospital_staff(staff_id):
        return False, "Invalid hospital staff ID"
    
    # Check if the slot exists in any of the priority slot lists
    is_priority_slot = False
    
    if block == "medical":  # Medical block
        is_priority_slot = slot in PRIORITY_SLOTS["medical"]
    elif block == "dental":  # Dental block
        is_priority_slot = slot in PRIORITY_SLOTS["dental"]
    
    if is_priority_slot:
        priority = get_staff_priority(staff_id)
        if priority <= 3:  # Allow medical staff up to priority level 3
            return True, f"Priority level {priority} access granted"
        else:
            return False, "Priority level insufficient for priority slots"
    
    # Non-priority slots are available to all hospital staff
    return True, "Non-priority slot available to all hospital staff"

# --- Hospital Priority Routes ---
@app.route("/hospital")
def hospital_index():
    return render_template("priority_index.html")

@app.route("/hospital/verify_staff", methods=["POST"])
def verify_hospital_staff():
    try:
        data = request.get_json()
        staff_id = data.get("staff_id", "").strip().upper()
        if not staff_id:
            return jsonify({"success": False, "message": "Staff ID is required"}), 400
        if is_hospital_staff(staff_id):
            staff_info = get_staff_info(staff_id)
            priority = get_staff_priority(staff_id)
            available_medical = get_available_priority_slots("medical")
            available_dental = get_available_priority_slots("dental")
            return jsonify({
                "success": True,
                "staff_info": staff_info,
                "priority_level": priority,
                "available_priority_slots": {
                    "medical": available_medical,
                    "dental": available_dental
                }
            }), 200
        else:
            return jsonify({"success": False, "message": "Invalid staff ID"}), 401
    except Exception as e:
        print(f"Error verifying staff: {e}")
        return jsonify({"success": False, "message": "Verification failed"}), 500

@app.route("/hospital/priority_book/<block>/<slot>", methods=["POST"])
def priority_book_slot(block, slot):
    try:
        data = request.get_json()
        staff_id = data.get("staff_id", "").strip().upper()
        phone_number = data.get("phone_number", "").strip()
        device_info = data.get("device_info", {})
        if not all([staff_id, phone_number, block, slot]):
            return jsonify({"success": False, "message": "Missing required information"}), 400
        if not is_hospital_staff(staff_id):
            return jsonify({"success": False, "message": "Invalid staff ID"}), 401
        if block not in blocks or slot not in blocks[block]:
            return jsonify({"success": False, "message": "Invalid slot"}), 400
        if blocks[block][slot]["status"] != "available":
            return jsonify({"success": False, "message": "Slot not available"}), 409
        can_book, message = can_book_priority_slot(staff_id, block, slot)
        if not can_book:
            return jsonify({"success": False, "message": message}), 403
        otp = generate_otp()
        otps[f"{block}_{slot}"] = {
            "otp": otp,
            "phone_number": phone_number,
            "device_info": device_info,
            "staff_id": staff_id,
            "priority_booking": True,
            "expiry": time.time() + 300
        }
        staff_info = get_staff_info(staff_id)
        priority_message = f"""🏥 HOSPITAL PRIORITY BOOKING 🏥\n\nHello {staff_info['name']} ({staff_info['department']})\n\nYour priority booking OTP: {otp}\n\nBlock: {block.upper()}\nSlot: {slot}\nPriority Level: {get_staff_priority(staff_id)}\n\n- Team Smart Parking 🚗"""
        if send_otp(phone_number, otp, priority_message):
            return jsonify({"success": True, "message": "Priority OTP sent successfully", "staff_info": staff_info}), 200
        else:
            return jsonify({"success": False, "message": "Failed to send OTP"}), 500
    except Exception as e:
        print(f"Error in priority booking: {e}")
        return jsonify({"success": False, "message": "Priority booking failed"}), 500

@app.route("/hospital/verify_priority_otp", methods=["POST"])
def verify_priority_otp():
    try:
        data = request.get_json()
        block = data.get("block")
        slot = data.get("slot")
        otp_input = data.get("otp", "").strip()
        if not all([block, slot, otp_input]):
            return jsonify({"success": False, "message": "Missing required fields"}), 400
        otp_key = f"{block}_{slot}"
        if otp_key not in otps:
            return jsonify({"success": False, "message": "No OTP found for this slot"}), 400
        otp_data = otps[otp_key]
        if time.time() > otp_data["expiry"]:
            del otps[otp_key]
            return jsonify({"success": False, "message": "OTP expired"}), 400
        if otp_data["otp"] != otp_input:
            return jsonify({"success": False, "message": "Invalid OTP"}), 400
        if blocks[block][slot]["status"] != "available":
            del otps[otp_key]
            return jsonify({"success": False, "message": "Slot no longer available"}), 409
        release_url = f"{BASE_URL}release/{block}/{slot}"
        qr_data = generate_qr(release_url) if QRCODE_AVAILABLE else None
        blocks[block][slot] = {
            "status": "occupied",
            "device_info": otp_data["device_info"],
            "release_qr": qr_data,
            "staff_id": otp_data["staff_id"],
            "priority_booking": True,
            "booking_time": time.time()
        }
        save_booking_info(block, slot, otp_data["phone_number"], otp_data["device_info"])
        staff_info = get_staff_info(otp_data["staff_id"])
        hospital_bookings[f"{block}_{slot}"] = {
            "staff_id": otp_data["staff_id"],
            "staff_info": staff_info,
            "phone_number": otp_data["phone_number"],
            "booking_time": time.time(),
            "priority_level": get_staff_priority(otp_data["staff_id"])
        }
        del otps[otp_key]
        return jsonify({
            "success": True,
            "message": "Priority slot booked successfully!",
            "qr_code": qr_data,
            "release_url": release_url,
            "staff_info": staff_info,
            "booking_details": {
                "block": block,
                "slot": slot,
                "priority_level": get_staff_priority(otp_data["staff_id"])
            }
        }), 200
    except Exception as e:
        print(f"Error verifying priority OTP: {e}")
        return jsonify({"success": False, "message": "OTP verification failed"}), 500

# === Original Routes ===

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/status/<block>")
def status(block):
    if block in blocks:
        return jsonify(blocks[block])
    return jsonify({"error": "Block not found"}), 404

@app.route("/generate_qr/<block>/<slot>", methods=["POST"])
def generate_booking_qr(block, slot):
    if block in blocks and slot in blocks[block] and blocks[block][slot]["status"] == "available":
        data = request.get_json()
        device_info = data.get("device_info", {})
        encoded_device = base64.b64encode(json.dumps(device_info).encode()).decode()
        booking_url = f"{BASE_URL}/book/{block}/{slot}/{encoded_device}"
        qr_code = generate_qr(booking_url)
        return jsonify({"qr_code": qr_code}), 200
    return jsonify({"error": "Slot not available"}), 400

@app.route("/send_otp/<block>/<slot>", methods=["POST"])
def send_booking_otp(block, slot):
    data = request.get_json()
    phone_number = data.get("phone_number")
    if not phone_number:
        return jsonify({"error": "Phone number required"}), 400

    try:
        phone_number = normalize_phone(phone_number)
    except ValueError as ve:
        return jsonify({"error": str(ve)}), 400

    otp = generate_otp()
    otps[phone_number] = {
        "otp": otp,
        "block": block,
        "slot": slot,
        "expires_at": time.time() + 300
    }

    if send_otp(phone_number, otp, get_booking_message(otp)):
        return jsonify({"success": True}), 200
    return jsonify({"success": False, "message": "Failed to send OTP"}), 500

@app.route("/verify_otp", methods=["POST"])
def verify_otp():
    data = request.get_json()
    try:
        phone_number = normalize_phone(data.get("phone_number"))
    except ValueError as ve:
        return jsonify({"success": False, "message": str(ve)}), 400

    otp = str(data.get("otp")).strip()
    record = otps.get(phone_number)

    if not record:
        return jsonify({"success": False, "message": "OTP not found"}), 400
    if time.time() > record["expires_at"]:
        return jsonify({"success": False, "message": "OTP expired"}), 400
    if record["otp"] == otp:
        block = record["block"]
        slot = record["slot"]
        if blocks[block][slot]["status"] == "available":
            encoded_device = base64.b64encode(phone_number.encode()).decode()
            release_url_with_device = f"{BASE_URL}/release/{block}/{slot}/{encoded_device}"
            release_url_simple = f"{BASE_URL}/release/{block}/{slot}"

            blocks[block][slot]["status"] = "occupied"
            blocks[block][slot]["device_info"] = phone_number
            blocks[block][slot]["release_qr"] = generate_qr(release_url_with_device)

            # Generate the release QR code
            release_qr_image = generate_qr(release_url_with_device)

            # Create a downloadable file for the release QR
            qr_file_name = f"release_qr_{block}_{slot}.png"
            if release_qr_image:
                with open(f"static/{qr_file_name}", "wb") as qr_file:
                    qr_file.write(base64.b64decode(release_qr_image))

            device_info = {
                "userAgent": request.headers.get("User-Agent"),
                "ip": request.remote_addr,
                "timestamp": int(time.time())
            }
            save_booking_info(block, slot, phone_number, device_info)

            otps.pop(phone_number, None)

            return jsonify({
                "success": True,
                "message": f"Slot {slot} in {block} booked successfully!",
                "release_qr": blocks[block][slot]["release_qr"],
                "release_url": release_url_simple,
                "qr_download_link": f"/static/{qr_file_name}"
            }), 200

        return jsonify({"success": False, "message": "Slot already occupied"}), 403

    return jsonify({"success": False, "message": "Invalid OTP"}), 400

@app.route("/book/<block>/<slot>/<encoded_device>")
def book_slot(block, slot, encoded_device):
    return render_template("index.html", preselected_block=block, preselected_slot=slot)

@app.route("/release/<block>/<slot>", defaults={"encoded_device": None})
@app.route("/release/<block>/<slot>/<encoded_device>")
def release_slot(block, slot, encoded_device):
    if encoded_device is None:
        try:
            with open("bookings.json", "r") as f:
                bookings = json.load(f)
            booking = bookings.get(f"{block}_{slot}")
            if booking:
                phone_number = booking["phone_number"]
                encoded_device = base64.b64encode(phone_number.encode()).decode()
                return redirect(f"/release/{block}/{slot}/{encoded_device}")
            else:
                return "No booking found to release", 404
        except Exception as e:
            return f"Error reading booking: {e}", 500

    try:
        phone_number = base64.b64decode(encoded_device).decode()
        phone_number = normalize_phone(phone_number)
    except Exception as e:
        return f"Invalid encoded device info: {e}", 400

    print(f"Decoded phone: {phone_number}, Slot Status: {blocks[block][slot]}")

    if blocks[block][slot]["status"] == "occupied" and blocks[block][slot]["device_info"] == phone_number:
        otp = generate_otp()
        otps[phone_number] = {
            "otp": otp,
            "block": block,
            "slot": slot,
            "release": True,
            "expires_at": time.time() + 300
        }
        print(f"Generated Release OTP: {otp}")
        send_otp(phone_number, otp, get_release_message(otp))

    return render_template("release.html", block=block, slot=slot, encoded_device=encoded_device)

@app.route("/verify_release_otp", methods=["POST"])
def verify_release_otp():
    data = request.get_json()
    try:
        phone_number = normalize_phone(data.get("phone_number"))
    except ValueError as ve:
        return jsonify({"success": False, "message": str(ve)}), 400

    otp = str(data.get("otp")).strip()
    record = otps.get(phone_number)

    if not record or not record.get("release"):
        return jsonify({"success": False, "message": "Invalid or expired OTP"}), 400
    if time.time() > record["expires_at"]:
        return jsonify({"success": False, "message": "OTP expired"}), 400
    if record["otp"] == otp:
        block = record["block"]
        slot = record["slot"]
        blocks[block][slot]["status"] = "available"
        blocks[block][slot]["device_info"] = None
        blocks[block][slot]["release_qr"] = None
        otps.pop(phone_number, None)
        return jsonify({"success": True, "message": f"Slot {slot} in {block} released successfully!"}), 200

    return jsonify({"success": False, "message": "Invalid OTP"}), 400

# === Enhanced Routes with Device Fingerprinting ===

@app.route("/fingerprint/verify", methods=["POST"])
def verify_fingerprint():
    """Verify device fingerprint for enhanced security"""
    data = request.get_json()
    phone_number = data.get("phone_number")
    fingerprint_data = extract_device_fingerprint(data)
    
    if not phone_number:
        return jsonify({"error": "Phone number required"}), 400
    
    try:
        phone_number = normalize_phone(phone_number)
    except ValueError as ve:
        return jsonify({"error": str(ve)}), 400
    
    # Save fingerprint
    saved_fingerprint = save_device_fingerprint(phone_number, fingerprint_data)
    
    # Verify device
    verification = verify_device_fingerprint(phone_number, fingerprint_data)
    
    # Calculate risk score
    risk_assessment = get_device_risk_score(fingerprint_data, phone_number)
    
    # Log the verification attempt
    log_security_event(phone_number, "FINGERPRINT_VERIFICATION", {
        "verification": verification,
        "risk_assessment": risk_assessment
    })
    
    return jsonify({
        "verification": verification,
        "risk_assessment": risk_assessment,
        "fingerprint_saved": bool(saved_fingerprint),
        "timestamp": int(time.time())
    }), 200

@app.route("/enhanced_send_otp/<block>/<slot>", methods=["POST"])
def enhanced_send_booking_otp(block, slot):
    """Enhanced OTP sending with device fingerprinting"""
    data = request.get_json()
    phone_number = data.get("phone_number")
    fingerprint_data = extract_device_fingerprint(data)
    
    if not phone_number:
        return jsonify({"error": "Phone number required"}), 400
    
    try:
        phone_number = normalize_phone(phone_number)
    except ValueError as ve:
        return jsonify({"error": str(ve)}), 400
    
    # Verify device fingerprint
    verification = verify_device_fingerprint(phone_number, fingerprint_data)
    risk_assessment = get_device_risk_score(fingerprint_data, phone_number)
    
    # Save fingerprint
    save_device_fingerprint(phone_number, fingerprint_data)
    
    # Log the attempt
    log_security_event(phone_number, "ENHANCED_BOOKING_ATTEMPT", {
        "block": block,
        "slot": slot,
        "verification": verification,
        "risk_assessment": risk_assessment
    })
    
    # Check risk level - block high risk devices
    if risk_assessment['risk_level'] == 'HIGH' and risk_assessment['risk_score'] > 80:
        return jsonify({
            "error": "Security verification failed",
            "risk_factors": risk_assessment['risk_factors'],
            "message": "Please contact support for assistance"
        }), 403
    
    # Generate OTP with device context
    otp = generate_otp()
    otps[phone_number] = {
        "otp": otp,
        "block": block,
        "slot": slot,
        "expires_at": time.time() + 300,
        "fingerprint_hash": fingerprint_data.get('fingerprint_hash'),
        "device_verified": verification['is_trusted'],
        "risk_level": risk_assessment['risk_level'],
        "enhanced": True  # Mark as enhanced booking
    }
    
    # Enhanced message with security info
    security_emoji = "🔒" if verification['is_trusted'] else "⚠️"
    risk_emoji = "🟢" if risk_assessment['risk_level'] == 'LOW' else "🟡" if risk_assessment['risk_level'] == 'MEDIUM' else "🔴"
    
    enhanced_message = f"""{security_emoji} Your Smart Parking OTP: {otp}

Device Trust: {verification['confidence']}%
Security Level: {risk_assessment['risk_level']} {risk_emoji}

Block: {str(block).upper()} | Slot: {slot}

You're almost there! Let's make today amazing 🌈✨

– Team Smart Parking 💛"""
    
    if send_otp(phone_number, otp, enhanced_message):
        return jsonify({
            "success": True,
            "device_verification": verification,
            "risk_assessment": risk_assessment,
            "enhanced_security": True
        }), 200
    
    return jsonify({"success": False, "message": "Failed to send OTP"}), 500

@app.route("/enhanced_verify_otp", methods=["POST"])
def enhanced_verify_otp():
    """Enhanced OTP verification with device fingerprinting"""
    data = request.get_json()
    try:
        phone_number = normalize_phone(data.get("phone_number"))
    except ValueError as ve:
        return jsonify({"success": False, "message": str(ve)}), 400
    
    otp = str(data.get("otp")).strip()
    current_fingerprint = extract_device_fingerprint(data)
    
    record = otps.get(phone_number)
    
    if not record:
        return jsonify({"success": False, "message": "OTP not found"}), 400
    if time.time() > record["expires_at"]:
        return jsonify({"success": False, "message": "OTP expired"}), 400
    
    # Enhanced verification only applies to enhanced bookings
    if record.get("enhanced"):
        # Verify fingerprint consistency
        stored_fingerprint_hash = record.get("fingerprint_hash")
        current_fingerprint_hash = current_fingerprint.get("fingerprint_hash")
        
        if stored_fingerprint_hash and current_fingerprint_hash and stored_fingerprint_hash != current_fingerprint_hash:
            log_security_event(phone_number, "FINGERPRINT_MISMATCH", {
                "stored_hash": str(stored_fingerprint_hash)[:16],
                "current_hash": str(current_fingerprint_hash)[:16] if current_fingerprint_hash else "None"
            })
            return jsonify({
                "success": False, 
                "message": "Security verification failed - device fingerprint mismatch"
            }), 403
    
    if record["otp"] == otp:
        block = record["block"]
        slot = record["slot"]
        
        if blocks[block][slot]["status"] == "available":
            encoded_device = base64.b64encode(phone_number.encode()).decode()
            release_url_with_device = f"{BASE_URL}/release/{block}/{slot}/{encoded_device}"
            release_url_simple = f"{BASE_URL}/release/{block}/{slot}"
            
            # Enhanced slot data with fingerprinting
            blocks[block][slot]["status"] = "occupied"
            blocks[block][slot]["device_info"] = phone_number
            blocks[block][slot]["release_qr"] = generate_qr(release_url_with_device)
            
            if record.get("enhanced"):
                blocks[block][slot]["fingerprint_hash"] = current_fingerprint.get('fingerprint_hash')
                blocks[block][slot]["device_verified"] = record.get("device_verified", False)
                blocks[block][slot]["risk_level"] = record.get("risk_level", "UNKNOWN")
                blocks[block][slot]["enhanced_security"] = True
            
            # Generate the release QR code
            release_qr_image = generate_qr(release_url_with_device)
            
            # Create a downloadable file for the release QR
            qr_file_name = f"release_qr_{block}_{slot}.png"
            if release_qr_image:
                with open(f"static/{qr_file_name}", "wb") as qr_file:
                    qr_file.write(base64.b64decode(release_qr_image))
            
            # Enhanced device info with fingerprinting
            device_info = {
                "userAgent": request.headers.get("User-Agent"),
                "ip": request.remote_addr,
                "timestamp": int(time.time())
            }
            
            if record.get("enhanced"):
                device_info.update({
                    "fingerprint_hash": current_fingerprint.get('fingerprint_hash'),
                    "device_verified": record.get("device_verified", False),
                    "risk_level": record.get("risk_level", "UNKNOWN"),
                    "enhanced_security": True
                })
            
            save_booking_info(block, slot, phone_number, device_info)
            
            # Log successful booking
            log_security_event(phone_number, "BOOKING_SUCCESS", {
                "block": block,
                "slot": slot,
                "enhanced": record.get("enhanced", False),
                "device_verified": record.get("device_verified", False)
            })
            
            otps.pop(phone_number, None)
            
            response_data = {
                "success": True,
                "message": f"Slot {slot} in {block} booked successfully!",
                "release_qr": blocks[block][slot]["release_qr"],
                "release_url": release_url_simple,
                "qr_download_link": f"/static/{qr_file_name}"
            }
            
            if record.get("enhanced"):
                response_data.update({
                    "device_verified": record.get("device_verified", False),
                    "security_level": record.get("risk_level", "UNKNOWN"),
                    "enhanced_security": True
                })
            
            return jsonify(response_data), 200
        
        return jsonify({"success": False, "message": "Slot already occupied"}), 403
    
    return jsonify({"success": False, "message": "Invalid OTP"}), 400

@app.route("/device_analytics")
def device_analytics():
    """Get device analytics dashboard"""
    try:
        with open("device_fingerprints.json", "r") as f:
            fingerprints = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        fingerprints = {}
    
    try:
        with open("security_log.json", "r") as f:
            security_logs = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        security_logs = []
    
    analytics = {
        "total_users": len(fingerprints),
        "total_devices": sum(len(devices) for devices in fingerprints.values()),
        "platform_stats": {},
        "risk_distribution": {"LOW": 0, "MEDIUM": 0, "HIGH": 0},
        "recent_activity": [],
        "security_events": {"last_24h": 0, "last_week": 0},
        "top_risk_factors": {}
    }
    
    # Calculate platform statistics and risk distribution
    all_devices = []
    for user_devices in fingerprints.values():
        all_devices.extend(user_devices)
    
    for device in all_devices:
        platform = device.get('platform', 'Unknown')
        analytics["platform_stats"][platform] = analytics["platform_stats"].get(platform, 0) + 1
        
        # Calculate risk for analytics
        risk_score = get_device_risk_score(device, "analytics")
        analytics["risk_distribution"][risk_score["risk_level"]] += 1
        
        # Count risk factors
        for factor in risk_score["risk_factors"]:
            analytics["top_risk_factors"][factor] = analytics["top_risk_factors"].get(factor, 0) + 1
        
        # Recent activity (last 24 hours)
        if device.get('timestamp', 0) > time.time() - 86400:
            analytics["recent_activity"].append({
                "timestamp": device.get('timestamp'),
                "platform": platform,
                "risk_level": risk_score["risk_level"],
                "ip_address": device.get('ip_address', 'Unknown')
            })
    
    # Security event statistics
    current_time = time.time()
    for log in security_logs:
        log_time = log.get('timestamp', 0)
        if log_time > current_time - 86400:  # Last 24 hours
            analytics["security_events"]["last_24h"] += 1
        if log_time > current_time - 604800:  # Last week
            analytics["security_events"]["last_week"] += 1
    
    return jsonify(analytics), 200

@app.route("/security_dashboard")
def security_dashboard():
    """Render security dashboard"""
    return render_template("security_dashboard.html")

# === PWA Support Routes ===

@app.route("/offline")
def offline_page():
    """Offline page for PWA functionality"""
    return render_template("offline.html")

@app.route("/api/slots")
def api_slots():
    """API endpoint for slot data (used by PWA for caching)"""
    return jsonify(blocks)

@app.route("/api/pwa/status")
def pwa_status():
    """PWA status and capabilities endpoint"""
    return jsonify({
        "pwa_enabled": True,
        "offline_support": True,
        "install_supported": True,
        "background_sync": True,
        "push_notifications": False,  # Can be enabled later
        "timestamp": int(time.time())
    })

@app.route("/api/pwa/sync", methods=["POST"])
def pwa_background_sync():
    """Handle background sync requests from PWA"""
    data = request.get_json()
    sync_type = data.get("type")
    
    if sync_type == "booking":
        # Process offline booking sync
        return jsonify({"success": True, "message": "Booking sync processed"})
    elif sync_type == "release":
        # Process offline release sync
        return jsonify({"success": True, "message": "Release sync processed"})
    
    return jsonify({"success": False, "message": "Unknown sync type"})

# === End PWA Routes ===

@app.route("/reset", methods=["POST"])
def reset_all():
    global blocks
    for block in blocks:
        for slot in blocks[block]:
            blocks[block][slot] = {"status": "available", "device_info": None, "release_qr": None}
    return jsonify({"status": "reset"})

@app.route("/booking_qr/<block>/<slot>")
def booking_qr(block, slot):
    return jsonify({"qr_code": blocks[block][slot].get("release_qr", "")})

@app.route("/release_qr/<block>/<slot>")
def release_qr(block, slot):
    return jsonify({"qr_code": blocks[block][slot].get("release_qr", "")})

@app.route("/send_release_otp/<block>/<slot>", methods=["POST"])
def send_release_otp(block, slot):
    data = request.get_json()
    phone_number = data.get("phone_number")
    if not phone_number:
        return jsonify({"error": "Phone number required"}), 400

    try:
        phone_number = normalize_phone(phone_number)
    except ValueError as ve:
        return jsonify({"error": str(ve)}), 400

    if blocks[block][slot]["status"] == "occupied" and blocks[block][slot]["device_info"] == phone_number:
        otp = generate_otp()
        otps[phone_number] = {
            "otp": otp,
            "block": block,
            "slot": slot,
            "release": True,
            "expires_at": time.time() + 300
        }

        if send_otp(phone_number, otp, get_release_message(otp)):
            return jsonify({"success": True}), 200

    return jsonify({"success": False, "message": "Failed to send OTP"}), 500

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
