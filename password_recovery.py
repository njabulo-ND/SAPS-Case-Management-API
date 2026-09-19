import api
import random
from datetime import datetime, timedelta
import firebase_admin
from firebase_admin import credentials, firestore, exceptions as firebase_exceptions
import os
from dotenv import load_dotenv

load_dotenv()
#firebase connection
firebase_key = os.getenv("FIREBASE_CREDENTIALS")
if not firebase_admin._apps:
    cred = credentials.Certificate(
        firebase_key)
    firebase_admin.initialize_app(cred)
firebase_db = firestore.client()

otp_store = {}

otp_store ={}
def check_employee_and_sendotp(emp_no):
    doc = firebase_db.collection('employees').document(emp_no).get()
    if doc.exists:
        api.save_json_data({"employee":'exist'})
        data = doc.to_dict()
        email = data.get('email')
        otp = api.send_otp_email(email)
        return otp
    else:
        api.save_json_data({"employee":'Doesnt exist'})
        return {"employee":'Doesnt exist'}
    

def verify_otp(emp_no,otp_from_user):
    stored = otp_store.get(emp_no)
    if not stored or datetime.now() > stored.get('expiry'):
        return {"valid": False, "message": "Invalid or expired code"}, 400

    if otp_from_user == stored.get('otp'):
        del otp_store[emp_no]
        return {"valid": True}
    else:
        return {"valid": False, "message": "Invalid or expired code"}

def resend_otp(emp_no):
    return check_employee_and_sendotp(emp_no)

def reset_password(emp_no,new_password):
    firebase_db.collection('employees').document(emp_no).set({'password':new_password},merge=True)
    return {"success": True, "message": "Password reset successful"}

