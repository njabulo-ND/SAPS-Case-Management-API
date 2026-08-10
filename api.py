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
from google import genai
from google.genai import errors
from google.genai import types

load_dotenv()


def send_otp_email(receiver_email):
    try:

        # 1. Generate a secure 6-digit OTP
        otp = "".join(secrets.choice("0123456789") for _ in range(6))

        # 2. Automatically pull your hidden credentials
        sender_email = os.getenv("EMAIL_USER")
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
            f"Dear Officer,\n\n"
            f"We received a request to log in to / sign up for your SAPS Case Management "
            f"account. Please use the following One-Time Password (OTP) to complete your "
            f"verification.\n\n"
            f"Verification Code: {otp}\n\n"
            f"This code was generated securely and will expire shortly. If you did not "
            f"initiate this request, please contact your system administrator immediately.\n\n"
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


def sending_victim_email(message, receiver_email):
    try:

        # 2. Automatically pull your hidden credentials
        sender_email = os.getenv("EMAIL_USER")
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
        msg["Subject"] = "Case Registration Confirmation: Your Case Reference Number"
        # msg["From"] = sender_email
        msg["To"] = receiver_email
        msg.set_content(message)
        # 5. Connect and send

        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(sender_email, sender_password)
            server.send_message(msg)

        print(f"OTP successfully sent to {receiver_email}!")
        return

    except Exception as e:
        print(f"Failed to send email. Error: {e}")
        return None


def caseUpdate_email(message, receiver_email):
    try:

        # 2. Automatically pull your hidden credentials
        sender_email = os.getenv("EMAIL_USER")
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
        msg["Subject"] = "Case Assignment Update"
        msg["To"] = receiver_email
        msg.set_content(message)
        # 5. Connect and send

        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(sender_email, sender_password)
            server.send_message(msg)

        print(f"OTP successfully sent to {receiver_email}!")
        return

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

# AI intergration to all forms


def invistigation_diary_form(p21_form, case_number):
    try:
        api_key = os.environ["GEMINI_API_KEY"]
        # print(api_key)
        client = genai.Client(api_key=api_key)
        investigation_diary_schema = {
            "type": "OBJECT",
                    "properties": {
                        "station": {"type": "STRING"},
                        "casNo": {"type": "STRING"},
                        "entries": {
                            "type": "ARRAY",
                            "items": {
                                "type": "OBJECT",
                                "properties": {
                                    "date": {"type": "STRING"},
                                    "time": {"type": "STRING"},
                                    "particulars": {"type": "STRING"},
                                },
                                "required": ["date", "time", "particulars"],
                            },
                        },
                        "notes": {"type": "STRING"},
                        "investigatingOfficer": {"type": "STRING"},
                    },
            "required": ["station", "casNo", "entries", "notes", "investigatingOfficer"],
        }
        invistigation_diary_instructions = f"""
        You are completing an Investigation Diary entry for a police case file.
        An Investigation Diary is the chronological working record of a case -
        it captures WHEN things happened and WHAT is relevant for building the
        case, so an investigator can review the case history at a glance.
        
        Here is the completed P21 form and the case number, including the complainant's statement in the form:
        {json.dumps(p21_form), case_number}
        
        Fill in the following fields using ONLY what is stated or clearly and
        reasonably inferable from the P21 form's context. Do not force an
        answer where the context genuinely does not support one.
        
        
        1. station
        The police station responsible for handling this matter, based on
        what is stated or clearly implied in the P21 form but the  default is the jhb central station thats if the station is not
        mentioned in the p21
        
        2. casNo
        The case number for this matter, if it is stated anywhere in the
        P21 form or the one i sent along with the p21 form.
        
        3. entries
        A list of diary entries describing what happened. Include ONE entry
        containing:
        - date: the date the incident occurred, as stated in the statement
        - time: the time the incident occurred, as stated in the statement
        - particulars: a factual, investigator-useful account of what
            happened, written the way an officer would log it in a diary.
            Include details that could help build the case or lead to a
            suspect - for example, presence of CCTV footage, distinguishing
            suspect features, direction suspects fled, items taken, or
            anything the complainant offered (e.g. willingness to view an
            identification parade). Do not simply copy the statement word for
            word - summarise it clearly and usefully it should not be to long 3 lines specifically stating the particulars
            not explaining and story telling.
        
        4. notes
        A short 1-2 sentence high-level summary of the incident - enough
        for someone to understand what the case is about at a glance,
        without reading the full statement.
        
        5. investigatingOfficer
        The name of the investigating officer assigned to this case, if
        this is stated anywhere in the P21 form.
        
        STRICT RULE FOR MISSING INFORMATION:
        If the P21 form does not clearly provide a detail needed for a field
        above, you MUST write exactly "not specified" for that field. Never
        guess, estimate, or invent a detail that is not clearly stated in the
        P21 form. An honest gap is always better than a fabricated detail in
        a case file.
        """
        if api_key:
            response = client.models.generate_content(
                model="gemini-flash-latest",
                contents=invistigation_diary_instructions, config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=investigation_diary_schema,
                ),)

            filled_data = json.loads(response.text)
            json.dumps(filled_data, indent=2)
            save_json_data({"Filled investigation diary data": "Done"})
            return filled_data
        else:
            save_json_data({'invistigation diary data': 'not sent'})
            return {'invistigation diary data': 'not sent'}

    except Exception as e:
        return f"Unexpected Error: {e}"
    except KeyError:
        return ("PROBLEM: ...")
        exit()
    except errors.APIError as e:
        return ("PROBLEM talking to Gemini.")


def modus_operandi(p21_form, case_number):
    try:
        api_key = os.environ["GEMINI_API_KEY"]
        # print(api_key)
        client = genai.Client(api_key=api_key)
        modus_operandi_schema = {
            "type": "OBJECT",
            "properties": {
                    "caseNumber": {"type": "STRING"},
                    "ir": {"type": "STRING"},
                    "A_offence": {"type": "STRING"},
                    "B_date": {"type": "STRING"},
                    "C_time": {"type": "STRING"},
                    "D_place": {"type": "STRING"},
                    "E_methodUsed": {"type": "STRING"},
                    "F_instrumentUsed": {"type": "STRING"},
                    "G_propertyInvolvedAndValue": {"type": "STRING"},
                    "H_serialOrRegistrationNo": {"type": "STRING"},
                    "I_suspects": {
                        "type": "ARRAY",
                        "items": {
                            "type": "OBJECT",
                            "properties": {
                                "involved": {"type": "STRING"},
                                "description": {"type": "STRING"},
                            },
                            "required": ["involved", "description"],
                        },
                    },
                "J_witnessDetails": {"type": "STRING"},
                "K_circulationNo": {"type": "STRING"},
                "K_lcrcNo": {"type": "STRING"},
                "L_sap13No": {"type": "STRING"},
                "L_sap14No": {"type": "STRING"},
                "M_comments": {"type": "STRING"},
                "N_compiledBy": {
                        "type": "OBJECT",
                        "properties": {
                            "no": {"type": "STRING"},
                            "rank": {"type": "STRING"},
                            "initialAndSurname": {"type": "STRING"},
                        },
                        "required": ["no", "rank", "initialAndSurname"],
                    },
                "O_perusedBy": {
                        "type": "OBJECT",
                        "properties": {
                            "no": {"type": "STRING"},
                            "rank": {"type": "STRING"},
                            "initialAndSignature": {"type": "STRING"},
                        },
                        "required": ["no", "rank", "initialAndSignature"],
                    },
            },
            "required": [
                "caseNumber", "ir", "A_offence", "B_date", "C_time", "D_place",
                "E_methodUsed", "F_instrumentUsed", "G_propertyInvolvedAndValue",
                "H_serialOrRegistrationNo", "I_suspects", "J_witnessDetails",
                "K_circulationNo", "K_lcrcNo", "L_sap13No", "L_sap14No",
                "M_comments", "N_compiledBy", "O_perusedBy",
            ],
        }

        modus_instructions = f"""
        You are completing a Modus Operandi (MO) form for a police case file.
        This form records the PATTERN of how a crime was carried out, so
        investigators can compare it against other cases and identify repeat
        offenders or linked incidents. The letter prefixes on each field name
        (A_, B_, C_, etc.) are just labels for form layout - ignore them and
        focus only on the meaning of the field name itself.
        
        Here is the completed P21 form along with a casenumber, including the complainant's statement in the p21:
        {json.dumps(p21_form), case_number}
        
        Fill in the following fields using ONLY what is stated or clearly and
        reasonably inferable from the P21 form's context. Do not force an
        answer where the context genuinely does not support one.
        
        casNumber - the case number for this matter, if stated anywhere in
        the P21 form.
        
        A_offence - what actually happened to the victim; the specific crime
        or wrongdoing committed against them, which is the reason this case
        was opened (e.g. robbery, assault, theft,etc) for robbery ralated cases just say robbery dont specify
        what type of it just write robbery.
        
        B_date - the date on which the offence occurred, i.e. the date the
        victim was victimised, as stated in the statement.
        
        C_time - the time at which the offence occurred, as stated in the
        statement.
        
        D_place - the specific place or location where the offence occurred,
        as stated in the statement.
        
        E_methodUsed - HOW the suspect(s) carried out the offence against the
        victim; the actions and approach they used to commit the crime.
        
        F_instrumentUsed - what physical object, weapon, or tool the
        suspect(s) used to commit the offence (e.g. firearm, knife). If
        nothing was used, say so.
        
        G_propertyInvolvedAndValue - if any property was taken, damaged, or
        otherwise involved in the offence (cash, phones, a vehicle, or any
        other possessions), describe exactly what was involved and its value
        if stated. If no property was involved, say so clearly.
        
        H_serialOrRegistrationNo - ONLY fill this in if the offence is related
        to a vehicle being hijacked, stolen, or otherwise involved (e.g. a car
        registration or serial number). If the case does not involve a vehicle
        at all, or a serial/registration number is not given even though a
        vehicle is involved, write "not specified". Do not invent a number
        under any circumstances.
        
        I_suspects - a list with ONE entry per suspect described in the
        statement. For each suspect, provide:
        - involved: a short label identifying which suspect this is (e.g.
        "name of the suspect 1", "name of the suspect 2"), in the order they are introduced in the
        statement.
        - description: their individual identifying characteristics exactly
        as described in the statement - for example estimated age, height,
        build, and clothing. Do not merge multiple suspects into a single
        description; each suspect gets their own separate entry in the list.
        If the statement does not distinguish individual suspects at all (for
        example, it only mentions "a group of suspects" with no individual
        detail), return a single entry with involved set to "name of the suspect 1" and
        description set to "not specified".
        
        J_witnessDetails - details of anyone who witnessed the incident in any
        way - saw it, heard it, or was otherwise present and could have
        observed something relevant (e.g. a passerby, a companion of the
        victim). Include any details the statement gives about them.
        
        K_circulationNo, K_lcrcNo, L_sap13No, L_sap14No - these are internal
        administrative reference numbers that are never contained in a
        complainant's statement. Always write "not specified" for these four
        fields, regardless of the statement's content.
        
        M_comments - any additional observations from the statement that could
        help resolve the case - useful leads, things investigators should pay
        attention to, or notable circumstances (e.g. availability of CCTV
        footage, willingness to attend an identification parade).
        
        N_compiledBy - this section identifies the officer who compiled this
        form. You do NOT have this information. Always leave "no", "rank",
        and "initialAndSurname" as empty strings "".
        
        O_perusedBy - this section identifies the officer who reviewed this
        form. You do NOT have this information. Always leave "no", "rank",
        and "initialAndSignature" as empty strings "".
        
        checklist - this is a separate administrative checklist not covered by
        the statement. Always return this as an empty list [].
        
        STRICT RULE FOR MISSING INFORMATION:
        For any field above where you ARE expected to extract information, if
        the P21 form does not clearly provide that detail, you MUST write
        exactly "not specified". Never guess, estimate, or invent a detail
        that is not clearly stated in the P21 form. An honest gap is always
        better than a fabricated detail in a case file.
        """
        if api_key:
            response = client.models.generate_content(
                model="gemini-flash-latest",
                contents=modus_instructions, config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=modus_operandi_schema,
                ),)

            filled_data = json.loads(response.text)
            json.dumps(filled_data, indent=2)
            save_json_data({"Filled modus data": "Done"})
            return filled_data
        else:
            save_json_data({'modus': 'not sent'})
            return {'modus': 'not sent'}

    except Exception as e:
        return f"Unexpected Error: {e}"
    except KeyError:
        return ("PROBLEM: ...")
        exit()
    except errors.APIError as e:
        return ("PROBLEM talking to Gemini.")


def statement(p21_form, case_number):
    try:
        api_key = os.environ["GEMINI_API_KEY"]
        # print(api_key)
        client = genai.Client(api_key=api_key)
        statement_form_schema = {
            "type": "OBJECT",
            "properties": {
                "station": {"type": "STRING"},
                "cas": {"type": "STRING"},
                "whenCertain": {
                    "type": "OBJECT",
                    "properties": {
                        "description": {"type": "STRING"},
                        "date": {"type": "STRING"},
                        "time": {"type": "STRING"},
                    },
                    "required": ["description", "date", "time"],
                },
                "whenUncertainRange": {
                    "type": "OBJECT",
                    "properties": {
                        "description": {"type": "STRING"},
                        "from": {
                            "type": "OBJECT",
                            "properties": {
                                "date": {"type": "STRING"},
                                "time": {"type": "STRING"},
                            },
                            "required": ["date", "time"],
                        },
                        "to": {
                            "type": "OBJECT",
                            "properties": {
                                "date": {"type": "STRING"},
                                "time": {"type": "STRING"},
                            },
                            "required": ["date", "time"],
                        },
                    },
                    "required": ["description", "from", "to"],
                },
                "dayOfWeek": {"type": "STRING"},
                "offenceDescription": {"type": "STRING"},
                "methodEntrance": {"type": "STRING"},
                "instrumentType": {"type": "STRING"},
                "scene": {"type": "STRING"},
                "postalCode": {"type": "STRING"},
                "geographicalBlock": {"type": "STRING"},
                "premisesType": {"type": "STRING"},
                "footerDate": {"type": "STRING"},
                "footerSignature": {"type": "STRING"},
            },
            "required": [
                "station", "cas", "whenCertain", "whenUncertainRange", "dayOfWeek",
                "offenceDescription", "methodEntrance", "instrumentType", "scene",
                "postalCode", "geographicalBlock", "premisesType", "footerDate",
                "footerSignature",
            ],
        }
        statement_instructions = f"""
       You are completing a Statement Form for a police case file, based on
       information already captured in a P21 complainant statement.
       
       Here is the completed P21 form along with the case number, including the complainant's statement in the form:
       {json.dumps(p21_form), case_number}
       
       Fill in the following fields using ONLY what is stated or clearly and
       reasonably inferable from the P21 form's context. Do not force an
       answer where the context genuinely does not support one.
       
       station - the police station responsible for handling this matter,
       based on what is stated or clearly implied in the P21 form if not you can write JHB central station.
       
       cas - the case number for this matter, if stated anywhere in the
       P21 form.
       
       whenCertain vs whenUncertainRange - these two sections are
       alternatives, not both used at once. Read the statement and decide:
       - If the complainant states a specific, exact date and time for when
         the offence occurred (e.g. "on Saturday, 08 August 2026 at
         approximately 19:40"), this counts as CERTAIN. Fill in
         "whenCertain" with a short description of what happened at that
         time, plus the date and time. In this case, leave every value inside
         "whenUncertainRange" as "not specified".
       - If instead the complainant is unsure of exactly when it happened and
         can only give a range or estimate (e.g. "sometime between Friday
         night and Saturday morning"), this counts as UNCERTAIN. Fill in
         "whenUncertainRange" with a description plus the "from" and "to"
         date/time boundaries given. In this case, leave every value inside
         "whenCertain" as "not specified".
       Never guess a range if a certain time is given, and never invent a
       false sense of certainty if the complainant was actually unsure.
       
       dayOfWeek - work out the day of the week using the DATE found above
       (certain or uncertain), based on a real calendar - do not copy a day
       of the week merely because it happens to be mentioned in the
       statement. Only provide this if a complete, specific date (day,
       month, and year) was found. If no usable complete date was found, or
       if you cannot reliably determine the day of week from it, write
       "not specified".
       
       offenceDescription - a clear, factual description of what crime or
       wrongdoing was committed against the victim, based on the statement.
       
       methodEntrance - HOW the suspect(s) gained access to the scene, if
       this is relevant and stated (e.g. broke a window, entered through an
       unlocked door, walked in through the front entrance). If the incident
       did not involve gaining entry to a premises (for example, it happened
       in an open public place), write "not specified".
       
       instrumentType - the type of weapon, tool, or object used by the
       suspect(s) to commit the offence, if any is mentioned.
       
       scene - a description of the specific place where the offence
       occurred, as stated (e.g. the name and type of location).
       
       postalCode - the postal code of the scene, only if one is explicitly
       given in the statement. Do not guess a postal code based on a suburb
       or city name alone but if victim mentioned location which the incident happend using that location
       you can identify to wich postal code the location mentioned belongs to.
       
       geographicalBlock - the broader area, suburb, or precinct the scene
       falls within, if this can reasonably be determined from the address
       or location details given in the statement.
       
       premisesType - the type of premises where the offence occurred (for
       example: business/shop, private residence, open street, vehicle),
       based on what is stated or clearly implied by the scene description.
       
       footerDate and footerSignature - these are administrative sign-off
       fields completed by the officer finalising this form, not information
       contained in a complainant's statement. Always write "not specified"
       for both of these fields.
       
       STRICT RULE FOR MISSING INFORMATION:
       For any field where the P21 form does not clearly state or reasonably
       imply the needed detail through context, you MUST write exactly
       "not specified". You may use reasonable context-based understanding
       (for example, recognising that a shop counter and till imply a
       business premises), but you must never invent specific facts, numbers,
       or details that are not actually supported by the statement.
       """
        if api_key:
            response = client.models.generate_content(
                model="gemini-flash-latest",
                contents=statement_instructions, config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=statement_form_schema,
                ),)

            filled_data = json.loads(response.text)
            json.dumps(filled_data, indent=2)
            save_json_data({"Filled statement data": "Done"})
            return filled_data
        else:
            save_json_data({'statement': 'not sent'})
            return {'statement': 'not sent'}

    except Exception as e:
        return f"Unexpected Error: {e}"
    except KeyError:
        return ("PROBLEM: ...")
        exit()
    except errors.APIError as e:
        return ("PROBLEM talking to Gemini.")


# ==========================================================
# Employee Management API
# ==========================================================
# This resource handles all employee-related operations:
#
# 1. Employee Verification:
#    - Checks if an officer exists in the SAPS employee database.
#    -Sends an email to the email stored in the database for Authorization
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
otp_store = {}

# Employees end point
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
                                'case_type': row['CASE_TYPE'],
                                'email': row['EMAIL']
                            }
                        for key, value in empty_dict.items():
                            firebase_db.collection(
                                'employees').document(key).set(value)
                        doc = firebase_db.collection(
                            'employees').document(employee_id).get()
                        if doc.exists:
                            otp = send_otp_email(
                                empty_dict[employee_id].get('email'))
                            otp_store[employee_id] = otp
                            save_json_data(
                                {'data': f'sent to firebase and email {empty_dict[employee_id].get('email')}\nOtp {otp_store[employee_id]}'})
                            empty_dict.update({'status': 'found'})
                            return empty_dict
                        else:
                            save_json_data(
                                {'data': f'Data was not sent to firebase'})

                if action.lower() == 'login':
                    doc = firebase_db.collection(
                        'employees').document(employee_id).get()

                    if doc.exists:
                        firebase_password = doc.to_dict().get('password')

                        if firebase_password:

                            if firebase_password == user_password:
                                otp = send_otp_email(
                                    doc.to_dict().get('email'))
                                otp_store[employee_id] = otp
                                save_json_data(
                                    {'otp sent': f'otp sent to {doc.to_dict().get('email')} with otp:{otp_store[employee_id]}'})
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
                    stored_otp = otp_store.get(employee_id)
                    if otp_from_user == stored_otp:
                        doc = firebase_db.collection(
                            'employees').document(employee_id).get()
                        return {doc.id: doc.to_dict(), 'status': 'verified'}
                    else:
                        return {'status': 'invalid_otp'}

                if action.lower() == 'filter':
                    if rank and case_type:
                        query = """
                                        SELECT EMPLOYEE_NUMBER,NAME,SURNAME FROM EMPLOYEES
                                        WHERE RANKS = ? AND CASE_TYPE =?;"""
                        df = pd.read_sql(
                            query, engine, params=(rank, case_type))
                        data = df.to_dict(orient="records")
                        save_json_data(
                            [{rank: 'found', case_type: 'found'}, data])
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
                    save_json_data({'data': 'data not sent'})
                    return {'error': 'Invalid data you should send json data'}

                password = data.get('password')
                employee_id = data.get('employee_id')

                if not password or not employee_id:
                    save_json_data(
                        {'problem': 'password or employee id not added'})
                    return {'error': 'Invalid data,password and id not added'}

                else:
                    doc = firebase_db.collection(
                        'employees').document(employee_id).get()

                    if not doc.exists:
                        save_json_data(
                            {'employee': 'was not found to set password'})
                        return {f'Employee:{employee_id} doesnt exists'}

                    else:
                        firebase_db.collection('employees').document(
                            employee_id).set({'password': password}, merge=True)
                        save_json_data(
                            {'password': f'password was addded {password}'})
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
#    -AI Autofills
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
                                SELECT VICTIM,STATEMENT_FORM,MODUS_OPERANDI,FORMAT(DATE_OPENED, 'yyyy-MM-dd HH:mm') AS DATE_OPENED,P21,CASE_NUMBER,STATUS
                                FROM CASES;"""
                    df = pd.read_sql(query, engine)
                    data = df.to_dict(orient='records')

                    save_json_data({'case list': data})
                    return data

                elif action.lower() == 'detective_case_list':
                    employee_number = request.args.get('employee_number')
                    query = """
                                SELECT VICTIM,STATEMENT_FORM,MODUS_OPERANDI,FORMAT(DATE_OPENED, 'yyyy-MM-dd HH:mm') AS DATE_OPENED,P21,CASE_NUMBER,STATUS
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
                    save_json_data({'data sent': data})
                    p21_form = json.dumps(data.get('p21'))
                    victim = data.get('victim')
                    initials = data.get('initials')
                    # Sending p21 to SQL and returning casenumber
                    query = """
                                INSERT INTO CASES(P21,VICTIM,VICTIM_EMAIL,STATUS)
                                OUTPUT INSERTED.CASE_NUMBER
                                VALUES
                                (:p21,:victim,:initials,'ACTIVE');
                        """
                    with engine.connect() as conn:
                        result = conn.execute(
                            text(query), {'p21': p21_form, 'victim': victim, 'initials': initials})
                        case_number = result.fetchone()[0]
                        conn.commit()

                    # AI autofilling
                    invistigation_diary_results = invistigation_diary_form(
                        p21_form, case_number)
                    modus_results = modus_operandi(p21_form, case_number)
                    statement_results = statement(p21_form, case_number)

                    # Saving to progress view
                    save_json_data({'statement': statement_results,
                                   'investigation': invistigation_diary_results, 'modus': modus_results})

                    # Emailing victim about the activation of the case
                    case_message = (
                        f"Dear Complainant,\n\n"
                        f"This is to formally confirm that your case has been successfully "
                        f"logged and activated within the SAPS Case Management System.\n\n"
                        f"Case number: {case_number}\n\n"
                        f"Please retain this case number for future reference, as it will be "
                        f"required for any enquiries regarding the progress of your case. You "
                        f"will be notified as further updates become available, including once "
                        f"an investigating officer has been assigned.\n\n"
                        f"Regards,\n"
                        f"SAPS Case Management System"
                    )
                    sending_victim_email(case_message, initials)
                    # save_json_data({'Email':'Sent to victim'})
                    # Sending all the Autofilled forms to front end
                    return {"caseNumber": case_number, 'investigationDiary': invistigation_diary_results, "modusOperandi": modus_results,
                            "statement": statement_results}

                # Activates if the front end personnel verifies the Autofilled Invistigation Diary to be true then it is sent to Database
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
                        save_json_data(
                            {'status': 'no case number to add invistigation diary'})
                        return {'status': 'no case number'}

                # Activates if the front end personnel verifies the Autofilled Modus Operandi to be true then it is sent to Database
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
                        save_json_data(
                            {'status': 'no case number to add modusOperandi'})
                        return {'status': 'no case number'}

                # Activates if the front end personnel verifies the Autofilled statement to be true then it is sent to Database
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

                        # Writing to progress viewing file
                        save_json_data({'rows': rows_updated, 'employee_number': employee_number,
                                        'case_number': case_number})

                        # Validating if the assignment was successful then updates the victim about the assignment
                        if rows_updated > 0:
                            #Changing the status of the case after assignement
                            query = """
                                        UPDATE CASES
                                        SET STATUS = 'IN PROGRESS'
                                        WHERE CASE_NUMBER = :case_number
                                                            """
                            with engine.connect() as conn:
                                result = conn.execute(
                                    text(query), {'case_number': case_number})
                                conn.commit()
                                another_rows_updated = result.rowcount
                                
                            save_json_data({'Status change to in progress row count':another_rows_updated})

                            #Finding information of the assigned case
                            query = """
                                        SELECT E.NAME,E.SURNAME,E.RANKS,E.EMAIL,C.VICTIM_EMAIL
                                        FROM EMPLOYEES E
                                        JOIN CASES C ON E.EMPLOYEE_NUMBER = C.ASSIGNED_TO
                                        WHERE C.CASE_NUMBER = ?;"""
                            df = pd.read_sql(
                                query, engine, params=(str(case_number),))
                            employee_rows = df.to_dict(orient='records')

                            # If Verify whether the information was found if yes then victim and officer are updated
                            if employee_rows:
                                row = employee_rows[0]
                                name = row.get('NAME')
                                surname = row.get('SURNAME')
                                rank = row.get('RANKS')
                                officer_email = row.get('EMAIL')
                                victim_email = row.get('VICTIM_EMAIL')
                                offMessage = (
                                    f"Dear {rank} {name} {surname},\n\n"
                                    f"This is to formally notify you that case number {case_number} has been "
                                    f"assigned to you for investigation. Please log into the Case Management "
                                    f"System at your earliest convenience to review the case details and "
                                    f"proceed accordingly.\n\n"
                                    f"Regards,\n"
                                    f"SAPS Case Management System")
                                victMessage = (
                                    f"Dear Complainant,\n\n"
                                    f"This message serves to inform you of an update regarding case number "
                                    f"{case_number}. The case has been formally assigned to {rank} {name} "
                                    f"{surname} for investigation.\n\nCase Status: In Progress\n\n"
                                    f"Should you wish to make any enquiries regarding the progress of your "
                                    f"case, you may contact the investigating officer directly via email at "
                                    f"{officer_email}.\n\n"
                                    f"Regards,\n"
                                    f"SAPS Case Management System")

                                # Emailing the officer about the assignement
                                caseUpdate_email(offMessage, officer_email)
                                save_json_data({'officer': 'emailed'})

                                # Emailing the victim about the assignemnt
                                caseUpdate_email(victMessage, victim_email)
                                save_json_data(
                                    {'victim': F'emailed for case {case_number} assigned to {name}'})
                                return {'status': 'added'}
                            else:
                                save_json_data({'victim': 'not emailed'})
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
