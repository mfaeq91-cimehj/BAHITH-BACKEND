import os, csv, uuid, json
from datetime import datetime
from flask import Flask, request, jsonify
from flask_cors import CORS
from werkzeug.utils import secure_filename
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

app = Flask(__name__)
CORS(app, origins=["*"])  # Allow your Vercel frontend

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
LICENSE_CSV = "licenses.csv"

# Gmail Config — Set in Render Env Variables
SMTP_EMAIL = os.getenv("SMTP_EMAIL", "muhammadfaeq91@gmail.com")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "YOUR_16_DIGIT_APP_PASSWORD")
ADMIN_EMAIL = os.getenv("ADMIN_EMAIL", "muhammadfaeq91@gmail.com")

# Ensure CSV exists
if not os.path.exists(LICENSE_CSV):
    with open(LICENSE_CSV, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["date","name","email","bank","txn_id","license_key","status","screenshot"])

def generate_license():
    return f"BAHITH-MSTR-{uuid.uuid4().hex[:4].upper()}-{uuid.uuid4().hex[:4].upper()}-{uuid.uuid4().hex[:2].upper()}"

def save_to_csv(data):
    with open(LICENSE_CSV, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([data["date"], data["name"], data["email"], data["bank"], data["txn"], data["license"], "PENDING_VERIFICATION", data["screenshot"]])

def send_admin_alert(data):
    try:
        msg = MIMEMultipart()
        msg['From'] = SMTP_EMAIL
        msg['To'] = ADMIN_EMAIL
        msg['Subject'] = f"NEW PAYMENT - {data['name']} - {data['bank']} - {data['txn']}"
        body = f"""
        NEW SALE RECEIVED - Rafiq al-Bahith

        Name: {data['name']}
        Email: {data['email']}
        Bank: {data['bank']}
        Txn ID: {data['txn']}
        License: {data['license']}
        Date: {data['date']}
        Screenshot: {data['screenshot']}

        ACTION NEEDED:
        1. Verify payment in bank app
        2. If OK, update licenses.csv status to APPROVED
        3. Email buyer PDF with license
        
        Quick Approve Link: https://bahith-backend.onrender.com/admin
        """
        msg.attach(MIMEText(body, 'plain'))
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(SMTP_EMAIL, SMTP_PASSWORD)
        server.send_message(msg)
        server.quit()
        return True
    except Exception as e:
        print(f"Email error: {e}")
        return False

@app.route('/')
def home():
    return jsonify({"status":"Bahith Backend LIVE","email":SMTP_EMAIL})

@app.route('/api/verify-sale', methods=['POST'])
def verify_sale():
    try:
        name = request.form.get('name')
        email = request.form.get('email')
        bank = request.form.get('bank')
        txn = request.form.get('txn')
        screenshot_file = request.files.get('screenshot')

        if not all([name,email,bank,txn]):
            return jsonify({"success":False,"message":"Missing fields"}), 400

        # Save screenshot
        screenshot_name = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{secure_filename(screenshot_file.filename)}" if screenshot_file else "no_screenshot"
        if screenshot_file:
            screenshot_file.save(os.path.join(UPLOAD_FOLDER, screenshot_name))

        license_key = generate_license()
        date_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        data = {
            "date": date_str,
            "name": name,
            "email": email,
            "bank": bank,
            "txn": txn,
            "license": license_key,
            "screenshot": screenshot_name
        }

        # 1. Save to CSV
        save_to_csv(data)

        # 2. TODO: Google Sheet - Add here later (see comment below)
        # save_to_google_sheet(data)  # Uncomment after setting GOOGLE_CREDENTIALS

        # 3. Send admin email
        send_admin_alert(data)

        return jsonify({
            "success": True,
            "message": "Payment proof received",
            "license_key": license_key,
            "email": email
        })

    except Exception as e:
        print(f"Error: {e}")
        return jsonify({"success":False,"message":str(e)}), 500

# Admin view to see pending licenses
@app.route('/admin')
def admin_view():
    licenses = []
    if os.path.exists(LICENSE_CSV):
        with open(LICENSE_CSV, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            licenses = list(reader)
    html = "<h1>Bahith Sales - Licenses.csv</h1><table border=1 cellpadding=8><tr><th>Date</th><th>Name</th><th>Email</th><th>Bank</th><th>Txn</th><th>License</th><th>Status</th></tr>"
    for row in licenses[::-1]: # newest first
        html += f"<tr><td>{row.get('date')}</td><td>{row.get('name')}</td><td>{row.get('email')}</td><td>{row.get('bank')}</td><td>{row.get('txn_id')}</td><td><b>{row.get('license_key')}</b></td><td>{row.get('status')}</td></tr>"
    html += "</table>"
    return html

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
