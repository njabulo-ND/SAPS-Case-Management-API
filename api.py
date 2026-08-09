from flask import Flask, request
from flask_restful import Api, Resource
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError
import urllib
import json
import pandas as pd
from flask_cors import CORS
import firebase_admin
from firebase_admin import credentials, firestore, exceptions as firebase_exceptions
from werkzeug.exceptions import HTTPException
import secrets
import smtplib
from email.message import EmailMessage
import os
from dotenv import load_dotenv

load_dotenv()

def send_otp_email(receiver_email):
    try:
        
        # 1. Generate a secure 6-digit OTP
        otp = "".join(secrets.choice("0123456789") for _ in range(6))

        # 2. Automatically pull your hidden credentials
        sender_email =os.getenv("EMAIL_USER")
        sender_password = os.getenv("EMAIL_PASS")

        # Safety check to make sure the variables loaded correctly
        if not sender_email or not sender_password:
            print("Error: Could not find your email credentials in the .env file.")
            return None

        # 3. Configure server details
        smtp_server = "smtp.gmail.com"
        smtp_port = 587

        # 4. Create the email content
            # 4. Create a more formal email structure to pass spam filters
        msg = EmailMessage()
        # Change "Your Business Name" to whatever you want people to see
        msg["From"] = f"SAPS Case Management System <{sender_email}>"
        msg["Subject"] = "Security Verification: Your One-Time Password Code"
        # msg["From"] = sender_email
        msg["To"] = receiver_email
        msg.set_content(
    f"Dear Officer,"
    f"We received a request to log in to / sign up for your SAPS Case Management "
    f"account. Please use the following One-Time Password (OTP) to complete your "
    f"verification:"
    f"Verification Code: {otp}"
    f"This code was generated securely and will expire shortly. If you did not "
    f"initiate this request, please contact your system administrator immediately."
    f"Regards,")
        # 5. Connect and send
        
        with smtplib.SMTP(smtp_server, smtp_port) as server:
                server.starttls()
                server.login(sender_email, sender_password)
                server.send_message(msg)

        print(f"OTP successfully sent to {receiver_email}!")
        return otp

    except Exception as e:
        print(f"Failed to send email. Error: {e}")
        return None
try:

    load_dotenv()
    # ============================================
    # SQL Server Configuration
    # ============================================
    driver = os.getenv("DB_DRIVER")
    server = os.getenv("DB_SERVER")
    database = os.getenv("DB_NAME")
    username = os.getenv("DB_USERNAME")
    password = os.getenv("DB_PASSWORD")
    conection_string = (
        f"DRIVER={{{driver}}};"
        f"SERVER={server};"
        f"DATABASE={database};"
        f"UID={username};"
        f"PWD={password};"
        "TrustServerCertificate=yes;"
    )
    refined_connecting_string = urllib.parse.quote_plus(conection_string)
    engine = create_engine(
        f"mssql+pyodbc:///?odbc_connect={refined_connecting_string}")

    # ============================================
    # Flask Configuration
    # ============================================
    hostsite = Flask(__name__)
    CORS(hostsite)
    api = Api(hostsite)

    # ============================================
    # Firebase Configuration
    # ============================================
    if not firebase_admin._apps:
        cred = credentials.Certificate(
            os.getenv("FIREBASE_CREDENTIALS"))
        firebase_admin.initialize_app(cred)
    firebase_db = firestore.client()

    # ==========================================================
    # JSON Logging Function
    # ==========================================================
    # Saves data into a JSON file for debugging and tracking API responses.
    # ==========================================================

    def save_json_data(data):
        with open('jsonToReadData.json', 'w') as file:
            json.dump(data, file, indent=4)

except SQLAlchemyError as e:
    print(f"Database Error: {e}")

except firebase_exceptions.FirebaseError as e:
    print(f"Firebase Error: {e}")

except HTTPException as e:
    print(f"HTTP Error: {e}")

except urllib.error.URLError as e:
    print(f"URL Error: {e}")

except json.JSONDecodeError as e:
    print(f"JSON Error: {e}")

except Exception as e:
    print(f"Unexpected Error: {e}")





# ==========================================================
# Employee Management API
# ==========================================================
# This resource handles all employee-related operations:
#
# 1. Employee Verification:
#    - Checks if an officer exists in the SAPS employee database.
#    - Retrieves employee information from the database.
#    - Creates an employee profile in Firebase.
#
# 2. Employee Login:
#    - Retrieves the employee profile from Firebase.
#    - Verifies the employee password.
#
# 3. Employee Filtering:
#    - Searches employees based on rank and case type.
#    - Used for finding suitable officers for case assignments.
#
# 4. Account Setup:
#    - Allows verified employees to create their login password.
# ==========================================================
otp = ''
try:
    class EmployeeDetails(Resource):
        def get(self):
            # ==========================================================
            # Retrieve Employee Information
            # ==========================================================
            # Handles employee GET requests:
            #
            # 1. Verify:
            #    - Confirms officer exists in the SAPS database.
            #    - Sends employee details to Firebase.
            #
            # 2. Login:
            #    - Authenticates employee using Firebase credentials.
            #
            # 3. Filter:
            #    - Searches employees using rank and case type.
            # ==========================================================
            try:
                action = request.args.get('action')
                employee_id = str(request.args.get('id'))
                user_password = request.args.get('password')
                rank = request.args.get('rank')
                case_type = request.args.get('case_type')
                otp_from_user = str(request.args.get('otp'))

                if action is None:
                    return {'act`ion': 'add action'}

                if employee_id is None:
                    return {'status': 'employee id'}

                if action.lower() == 'verify':
                    if not employee_id:
                        return {'error': 'parameters missing'}, 400

                    query = """
                                    SELECT * FROM EMPLOYEES
                                    WHERE EMPLOYEE_NUMBER = ?;"""
                    df = pd.read_sql(query, engine, params=(employee_id,))
                    doc = firebase_db.collection(
                        'employees').document(employee_id).get()

                    if df.empty:
                        save_json_data({'account': 'not retrieved'})
                        return {'status': 'not found'}

                    elif doc.exists and doc.to_dict().get('password'):
                        save_json_data({'account': 'exists'})
                        return {'status': f'account exists{employee_id}'}

                    else:
                        data = df.to_dict(orient="records")
                        save_json_data({'data': 'found'})
                        empty_dict = {}

                        for row in data:
                            empty_dict[row['EMPLOYEE_NUMBER']] = {
                                'name': row['NAME'],
                                'surname': row['SURNAME'],
                                'rank': row['RANKS'],
                                'station': row['STATION'],
                                'city': row['CITY'],
                                'case_type': row['CASE_TYPE']
                            }
                        for key, value in empty_dict.items():
                            firebase_db.collection(
                                'employees').document(key).set(value)
                            
                        save_json_data({'data': 'sent to firebase'})
                        empty_dict.update({'status': 'found'})
                        return empty_dict


                if action.lower() == 'login':
                    doc = firebase_db.collection(
                        'employees').document(employee_id).get()

                    if doc.exists:
                        firebase_password = doc.to_dict().get('password')

                        if firebase_password:

                            if firebase_password == user_password:
                                save_json_data({'password': 'matches'})
                                otp = send_otp_email("ayabulelandzombane@gmail.com")
                                return {doc.id: doc.to_dict(), 'status': 'otp_sent'}

                            elif firebase_password != user_password:
                                save_json_data({'password': 'not matching'})
                                return {'status': 'does not match'}

                        else:
                            save_json_data({'password': 'user did not add'})  
                            return {'status': 'user did not add password'}

                    else:
                        save_json_data({'employee': 'does exists'})
                        return {'status': 'not found'}
                if action == 'verify_otp':
                    if otp_from_user == otp:
                       return {doc.id: doc.to_dict(), 'status': 'verified'}
                    else:
                         return {'status':'invalid_otp'}
        
                if action.lower() == 'filter':
                    if rank and case_type:
                        query = """
                                        SELECT EMPLOYEE_NUMBER,NAME,SURNAME FROM EMPLOYEES
                                        WHERE RANKS = ? AND CASE_TYPE =?;"""
                        df = pd.read_sql(
                            query, engine, params=(rank, case_type))
                        data = df.to_dict(orient="records")
                        save_json_data([{rank: 'found', case_type: 'found'}, data])
                        return data
                    
                    elif rank and not case_type:
                        query = """
                                        SELECT EMPLOYEE_NUMBER,NAME,SURNAME FROM EMPLOYEES
                                        WHERE RANKS = ?;"""
                        df = pd.read_sql(query, engine, params=(rank,))
                        data = df.to_dict(orient="records")
                        save_json_data([{rank: 'found'}, data])
                        return data
                    
                    elif case_type and not rank:
                        query = """
                                        SELECT EMPLOYEE_NUMBER,NAME,SURNAME FROM EMPLOYEES
                                        WHERE CASE_TYPE =?;"""
                        df = pd.read_sql(query, engine, params=(case_type,))
                        data = df.to_dict(orient="records")
                        save_json_data([{case_type: 'found'}, data])
                        return data
                    
                    else:
                        return {'data': 'not found you did not add rank or casetype'}
                    
            # catches ALL database errors in one line
            except SQLAlchemyError as e:
                return {"Database Error": str(e)}, 500
                # catches ALL firebase errors in one line
            except firebase_exceptions.FirebaseError as e:
                return {'error': f'Firebase error: {e}'}, 500
                # catches ALL unexpected errors in one line
            except Exception as e:
                return {"error": str(e)}, 500
            
        def post(self):
            # ==========================================================
            # Employee Account Setup
            # ==========================================================
            # Handles employee account creation:
            #
            # 1. Receives employee ID and password.
            #
            # 2. Checks if employee profile exists in Firebase.
            #
            # 3. Saves the employee password for future login.
            # ==========================================================
            try:
                data = request.get_json()

                if not data:
                    save_json_data( {'data': 'data not sent'})
                    return {'error': 'Invalid data you should send json data'}

                password = data.get('password')
                employee_id = data.get('employee_id')

                if not password or not employee_id:
                    save_json_data({'problem': 'password or employee id not added'})
                    return {'error': 'Invalid data,password and id not added'}

                else:
                    doc = firebase_db.collection(
                        'employees').document(employee_id).get()

                    if not doc.exists:
                        save_json_data({'employee': 'was not found to set password'})
                        return {f'Employee:{employee_id} doesnt exists'}

                    else:
                        firebase_db.collection('employees').document(
                            employee_id).set({'password': password}, merge=True)
                        save_json_data({'password': f'password was addded {password}'})
                        return {'status': 'Successfully added'}
                    
            # catches ALL database errors in one line
            except SQLAlchemyError as e:
                return {"Database Error": str(e)}, 500
            # catches ALL firebase errors in one line
            except firebase_exceptions.FirebaseError as e:
                return {'error': f'Firebase error: {e}'}, 500
            # catches ALL unexpected errors in one line
            except Exception as e:
                return {"error": str(e)}, 500
# catches ALL HTTP errors in one line
except HTTPException as e:
    print(f"HTTP Error {e.code}: {e.description}")
# catches ALL pandas errors in one line
except pd.errors.ParserError as e:
    print(f"Pandas Error: {e}")
# catches ALL json errors in one line
except json.JSONDecodeError as e:
    print(f"JSON Error: {e}")
# catches ALL urllib errors in one line
except urllib.error.URLError as e:
    print(f"URL Error: {e}")


# ==========================================================
# Case Management API
# ==========================================================
# This Case resource handles all case-related operations:
#
# 1. Case Retrieval:
#    - Retrieves all cases from the SAPS database.
#    - Retrieves cases assigned to a specific officer.
#
# 2. Case Creation:
#    - Creates new cases using submitted P21 information.
#
# 3. Case Updates:
#    - Updates investigation diary information.
#    - Updates modus operandi details.
#    - Updates statement forms.
#
# 4. Case Assignment:
#    - Assigns cases to specific officers.
#    - Updates the assigned officer information in the database.
# ==========================================================

try:
    class Cases(Resource):
        def get(self):
            # ==========================================================
            # Retrieve Cases
            # ==========================================================
            # Handles requests for retrieving case information:
            #
            # 1. Case List:
            #    - Returns all available cases.
            #
            # 2. Detective Case List:
            #    - Returns only cases assigned to a specific officer.
            # ==========================================================
            try:
                action = request.args.get('action')
                if action.lower() == "case_list":
                    query = """
                                SELECT VICTIM,STATEMENT_FORM,MODUS_OPERANDI,FORMAT(DATE_OPENED, 'yyyy-MM-dd HH:mm') AS DATE_OPENED,P21,CASE_NUMBER
                                FROM CASES;"""
                    df = pd.read_sql(query, engine)
                    data = df.to_dict(orient='records')
                    save_json_data({'case list': 'case list submitted'})
                    return data

                elif action.lower() == 'detective_case_list':
                    employee_number = request.args.get('employee_number')
                    query = """
                                SELECT VICTIM,STATEMENT_FORM,MODUS_OPERANDI,FORMAT(DATE_OPENED, 'yyyy-MM-dd HH:mm') AS DATE_OPENED,P21,CASE_NUMBER
                                FROM CASES
                                WHERE ASSIGNED_TO = ?;"""
                    df = pd.read_sql(query, engine, params=(employee_number,))
                    data = df.to_dict(orient='records')
                    save_json_data({'case list': data})
                    return data
            # catches ALL database errors in one line
            except SQLAlchemyError as e:
                return {"Database Error": str(e)}, 500
            # catches ALL firebase errors in one line
            except firebase_exceptions.FirebaseError as e:
                return {'error': f'Firebase error: {e}'}, 500
            # catches ALL pandas errors in one line
            except pd.errors.ParserError as e:
                return {f"Pandas Error: {e}"}
            except json.JSONDecodeError as e:
                # catches ALL json errors in one line
                return (f"JSON Error: {e}")
            except urllib.error.URLError as e:
                # catches ALL urllib errors in one line
                print(f"URL Error: {e}")
            except Exception as e:
                return {"error": str(e)}, 500

        def post(self):
            # ==========================================================
            # Create And Update Cases
            # ==========================================================
            # Handles all case submission and modification requests:
            #
            # 1. New Case:
            #    - Creates a new case record using P21 information.
            #
            # 2. Investigation Diary:
            #    - Adds investigation progress information.
            #
            # 3. Modus Operandi:
            #    - Adds details about the crime method.
            #
            # 4. Statement Form:
            #    - Adds witness or victim statements.
            #
            # 5. Case Assignment:
            #    - Assigns cases to officers responsible for investigation.
            # ==========================================================
            try:
                data = request.get_json()

                if not data:
                    save_json_data({'status': 'not added'})
                    return {'status': 'not added'}

                if data.get('p21'):
                    form = json.dumps(data.get('p21'))
                    victim = data.get('victim')
                    query = """
                                INSERT INTO CASES(P21,VICTIM)
                                OUTPUT INSERTED.CASE_NUMBER
                                VALUES
                                (:p21,:victim);
                        """
                    with engine.connect() as conn:
                        result = conn.execute(
                            text(query), {'p21': form, 'victim': victim})
                        case_number = result.fetchone()[0]
                        conn.commit()
                    save_json_data(data)
                    return {"caseNumber": case_number}
                
                elif data.get('investigationDiary'):
                    if data.get('caseNumber'):
                        form = json.dumps(data.get('investigationDiary'))
                        case_number = data.get('caseNumber')
                        query = """
                                UPDATE CASES
                                SET INVESTIGATION_DIARY = :diary
                                WHERE CASE_NUMBER = :number
                            """
                        with engine.connect() as conn:
                            conn.execute(
                                text(query), {'diary': form, 'number': case_number})
                            conn.commit()
                        save_json_data(data)
                        return {'status': 'added'}
                    
                    else:
                        save_json_data({'status': 'no case number to add invistigation diary'})
                        return {'status': 'no case number'}
                    
                elif data.get('modusOperandi'):
                    if data.get('caseNumber'):
                        form = json.dumps(data.get('modusOperandi'))
                        case_number = data.get('caseNumber')
                        query = """
                                UPDATE CASES
                                SET MODUS_OPERANDI = :operandi
                                WHERE CASE_NUMBER = :number
                                """
                        with engine.connect() as conn:
                            conn.execute(
                                text(query), {'operandi': form, 'number': case_number})
                            conn.commit()
                        save_json_data(data)
                        return {'status': 'added'}
                    
                    else:
                        save_json_data({'status': 'no case number to add modusOperandi'})
                        return {'status': 'no case number'}

                elif data.get('statement'):
                    if data.get('caseNumber'):
                        form = json.dumps(data.get('statement'))
                        case_number = data.get('caseNumber')
                        query = """
                            UPDATE CASES
                            SET STATEMENT_FORM = :statement
                            WHERE CASE_NUMBER = :number
                            """
                        with engine.connect() as conn:
                            conn.execute(
                                text(query), {'statement': form, 'number': case_number})
                            conn.commit()
                        save_json_data(data)
                        return {'status': 'added'}
                    
                    else:
                        save_json_data({'status': 'statement not added'})
                        return {'status': 'no case number'}
                    
                # Assigning police to a case
                if data.get('action'):
                    if data.get('action').lower() == 'assign':
                        case_number = data.get('case_number')
                        employee_number = data.get('employee_number')
                        query = """
                                UPDATE CASES
                                SET ASSIGNED_TO = :employee_number
                                WHERE CASE_NUMBER = :case_number
                                """
                        with engine.connect() as conn:
                            result = conn.execute(
                                text(query), {'employee_number': employee_number, 'case_number': case_number})
                            conn.commit()
                            rows_updated = result.rowcount
                        save_json_data({'rows': rows_updated, 'employee_number': employee_number,
                                      'case_number': case_number})
                        if rows_updated > 0:
                            return {'status': 'added'}
                        else:
                            return {'status': 'not added'}
                    else:
                        return {'status': 'not added'}
             # catches ALL database errors in one line
            except SQLAlchemyError as e:
                return {"Database Error": str(e)}, 500
            # catches ALL firebase errors in one line
            except firebase_exceptions.FirebaseError as e:
                return {'error': f'Firebase error: {e}'}, 500
            # catches ALL pandas errors in one line
            except pd.errors.ParserError as e:
                return {f"Pandas Error: {e}"}
            except json.JSONDecodeError as e:
                # catches ALL json errors in one line
                return (f"JSON Error: {e}")
            except urllib.error.URLError as e:
                # catches ALL urllib errors in one line
                print(f"URL Error: {e}")
            except Exception as e:
                return {"error": str(e)}, 500
# catches ALL HTTP errors in one line
except HTTPException as e:
    print(f"HTTP Error {e.code}: {e.description}")
# catches ALL pandas errors in one line
except pd.errors.ParserError as e:
    print(f"Pandas Error: {e}")
# catches ALL json errors in one line
except json.JSONDecodeError as e:
    print(f"JSON Error: {e}")
# catches ALL urllib errors in one line
except urllib.error.URLError as e:
    print(f"URL Error: {e}")


# ==========================================================
# Application Entry Point
# ==========================================================
# Starts the Flask API server.
#
# host 0.0.0.0 allows access from other devices on the network.
# port 5000 is the API communication port.
# ==========================================================
try:
    api.add_resource(EmployeeDetails, '/employees')
    api.add_resource(Cases, '/cases')
    if __name__ == '__main__':
        hostsite.run(host="0.0.0.0", port=5000, debug=True)
except firebase_exceptions.FirebaseError as e:
    print(f"Firebase Error: {e}")