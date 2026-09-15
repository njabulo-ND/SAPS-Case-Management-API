from flask import Flask, render_template, request, jsonify, session
import random
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATE_DIR = os.path.join(BASE_DIR, 'templates')

app = Flask(__name__, template_folder=TEMPLATE_DIR)
app.secret_key = "demo123"

otp_store = {}

def send_email_otp(to_email, otp):
    print("="*50)
    print(f" [DEMO EMAIL] To: {to_email}")
    print(f" [DEMO EMAIL] OTP Code is: {otp}")
    print("="*50)
    return True

@app.route('/')
def login_page():
    return render_template('login_page.html')

@app.route('/forgot-password')
def forgot_password_page():
    return render_template('verify_employee_number.html')

@app.route('/verify-otp')
def verify_otp_page():
    email = session.get('reset_email', 'j****@company.com')
    if '@' in email:
        name, domain = email.split('@')
        masked = name[0] + '****@' + domain
    else:
        masked = email
    return render_template('otp_verification.html', masked_email=masked)


@app.route('/api/check-employee', methods=['POST'])
@app.route('/api/forgot-password', methods=['POST'])
def check_employee():
    data = request.get_json() or {}
    emp_no = data.get('employee_number','').strip().upper()
    print(f"Checking: {emp_no}")

    allowed = ["EMP00001", "EMP00002", "EMP00003", "EMP00004", "EMP00005"]
    if emp_no not in allowed:
        return jsonify({"exists": False, "message": "Employee number not found - please re-enter"}), 404

    otp = str(random.randint(100000, 999999))
    print("=================================")
    print(f"*** OTP for {emp_no} is {otp} ***")
    print("=================================")

    session['reset_emp'] = emp_no
    session['reset_otp'] = otp
    # also save in otp_store for verify step
    otp_store[emp_no] = {"otp": otp, "expiry": datetime.now() + timedelta(minutes=5)}
    session['reset_email'] = f"{emp_no.lower()}@company.com"

    return jsonify({"exists": True})

@app.route('/api/verify-otp', methods=['POST'])
def verify_otp():
    entered = "".join(request.get_json().get('otp', []))
    emp_no = session.get('reset_emp')
    stored = otp_store.get(emp_no)

    if not stored or datetime.now() > stored['expiry']:
        return jsonify({"valid": False, "message": "Invalid or expired code"}), 400

    if entered == stored['otp'] or entered == session.get('reset_otp'):
        if emp_no in otp_store:
            del otp_store[emp_no]
        return jsonify({"valid": True})
    return jsonify({"valid": False, "message": "Invalid or expired code"}), 400

@app.route('/api/resend-otp', methods=['POST'])
def resend_otp():
    emp_no = session.get('reset_emp')
    if not emp_no:
        return jsonify({"message": "Session expired"}), 400

    otp = str(random.randint(100000, 999999))
    otp_store[emp_no] = {"otp": otp, "expiry": datetime.now() + timedelta(minutes=5)}
    session['reset_otp'] = otp

    send_email_otp(session.get('reset_email'), otp)
    print(f"*** NEW OTP for {emp_no} is {otp} ***")
    return jsonify({"message": "New OTP sent"})

@app.route('/create-password')
def create_password_page():
    # Optional: check if OTP was verified
    # if 'otp_verified' not in session: return redirect('/verify-otp')
    return render_template('create_new_password.html')

@app.route('/api/reset-password', methods=['POST'])
def reset_password():
    data = request.get_json()
    new_pw = data.get('new_password')
    
    # TODO: Save this to your database
    # Example: update_employee_password(session.get('reset_employee_number'), new_pw)
    print(f"Password reset for {session.get('reset_employee_number')}: {new_pw}")
    
    # Clear session after reset
    session.pop('reset_employee_number', None)
    
    return jsonify({"success": True, "message": "Password reset successful"})

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5001, debug=True)