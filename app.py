from flask import Flask, request
import fitz, random, string, os, datetime, csv
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders

app = Flask(__name__)

def gen_license():
    # INFINITE - generates new every time
    p1 = ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))
    p2 = ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))
    chk = str(random.randint(0,9))
    return f"BAHITH-ED1-2026-{p1}-{p2}-{chk}"

def stamp_pdf(email, license_key):
    watermark = f"Licensed to {email} | {license_key}"
    doc = fitz.open("master.pdf")
    for page in doc:
        w,h = page.rect.width, page.rect.height
        page.insert_text((w/2-200, h/2), watermark, fontsize=11, color=(0.85,0.85,0.85), overlay=True)
        page.insert_text((30, h-15), watermark, fontsize=7, color=(0.6,0.6,0.6), overlay=True)
    out = f"/tmp/{license_key}.pdf"
    doc.save(out)
    doc.close()
    return out

@app.route('/')
def home():
    return "BAHITH Backend Running - Infinite Licensing Active"

@app.route('/submit', methods=['POST'])
def submit():
    email = request.form['email']
    tid = request.form['tid']
    bank = request.form['bank']
    
    license_key = gen_license() # INFINITE - new every booking
    
    # Save to CSV (this becomes your infinite sheet)
    with open('licenses.csv','a', newline='') as f:
        writer = csv.writer(f)
        writer.writerow([email, tid, bank, license_key, datetime.datetime.now(), "Approved"])
    
    # Stamp
    pdf_path = stamp_pdf(email, license_key)
    
    # Email will be added after Gmail step
    return f"<h1>Success! License {license_key} created for {email}. PDF will be emailed after Gmail setup.</h1>"

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=10000)
