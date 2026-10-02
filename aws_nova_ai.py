import json
import boto3
from dotenv import load_dotenv
import time



load_dotenv()

def run_nova(client, model, contents, retries=5):

    for i in range(retries):

        try:

            print(
                f"\n[Nova] Sending forms to {model}..."
            )

            response = client.converse(
                modelId=model,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "text": contents
                            }
                        ]
                    }
                ],
                inferenceConfig={
                    "temperature": 0,
                    "maxTokens": 5000
                }
            )

            print(
                f"[Nova] Forms received successfully on attempt {i + 1}/{retries}."
            )

            return response

        except Exception as e:

            err_msg = str(e)

            # Temporary AWS/Nova errors
            is_transient = (
                "429" in err_msg
                or "500" in err_msg
                or "502" in err_msg
                or "503" in err_msg
                or "504" in err_msg
                or "ThrottlingException" in err_msg
                or "ServiceUnavailableException" in err_msg
                or "TooManyRequestsException" in err_msg
                or "InternalServerException" in err_msg
                or "ServiceUnavailable" in err_msg
            )

            if is_transient and i < retries - 1:

                sleep_time = 4 * (2 ** i)

                print(
                    f"[Nova Temporary Error] Model busy or service temporarily unavailable."
                )

                print(
                    f"[Nova Error] {err_msg}"
                )

                print(
                    f"[Nova Retry] Retrying attempt {i + 2}/{retries} after {sleep_time}s..."
                )

                time.sleep(sleep_time)

                continue

            # Permanent error or all retries exhausted
            print(
                f"[Nova Error] Request failed permanently or all retries were exhausted."
            )

            print(
                f"[Nova Error Details] {err_msg}"
            )

            raise e




bedrock_client = boto3.client(
    "bedrock-runtime",
    region_name="us-east-1"
)

def fill_all_forms(p21_form, case_number):

    try:

        combined_instructions = f"""
        You are completing THREE separate police case-file forms in one go, using
        the same P21 complainant statement and case number as your only source of
        information. Return one JSON object with three top-level keys:
        "investigationDiary", "modusOperandi", and "statement". Treat each
        section below as completely self-contained - follow its own
        instructions only, and do not let field names or logic from one
        section bleed into another.
        Here is the completed P21 form and the case number, including the complainant's statement in the form:
        {json.dumps(p21_form, indent=4)}
        CASE NUMBER:
        {case_number}
        ============================================================
        SECTION 1: investigationDiary
        ============================================================
        You are completing an Investigation Diary entry for a police case file.
        An Investigation Diary is the chronological working record of a case -
        it captures WHEN things happened and WHAT is relevant for building the
        case, so an investigator can review the case history at a glance.
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
        A list of diary entries describing what happened.
        - date: the date the incident occurred, as stated in the statement
        - time: the time the incident occurred, as stated in the statement
        - particulars: a factual, investigator-useful account of what
            happened, written the way an officer would log it in a diary.
            Include details that could help build the case or lead to a
            suspect - for example, presence of CCTV footage, distinguishing
            suspect features, direction suspects fled, items taken, or
            anything the complainant offered (e.g. willingness to view an
            identification parade). Do not simply copy the statement word
            for word - summarise it clearly and usefully it should not be to long 3 lines specifically stating the particulars
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
        ============================================================
        SECTION 2: modusOperandi
        ============================================================
        You are completing a Modus Operandi (MO) form for a police case file.
        This form records the PATTERN of how a crime was carried out, so
        investigators can compare it against other cases and identify repeat
        offenders or linked incidents. The letter prefixes on each field name
        (A_, B_, C_, etc.) are just labels for form layout - ignore them and
        focus only on the meaning of the field name itself.
        Fill in the following fields using ONLY what is stated or clearly and
        reasonably inferable from the P21 form's context. Do not force an
        answer where the context genuinely does not support one.
        casNumber - the case number for this matter, if stated anywhere in
        the P21 form.
        A_offence - what actually happened to the victim; the specific crime
        or wrongdoing committed against them, which is the reason this case
        was opened (e.g. robbery, assault, theft,etc).
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
        ============================================================
        SECTION 3: statement
        ============================================================
        You are completing a Statement Form for a police case file, based on
        information already captured in a P21 complainant statement.
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
        or city name alone but if victim mentioned location which the incident
        happend using that location you can identify to wich postal code the
        location mentioned belongs to.
        street name - the street the adress has on the statement if it is not there write not found
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

        Return ONLY valid JSON.
        Do not use markdown.
        Do not use ```json.
        Do not add explanations.
        """

        response = run_nova(
    client=bedrock_client,
    model="us.amazon.nova-2-lite-v1:0",
    contents=combined_instructions
)

        response_text = response["output"]["message"]["content"][0]["text"]

        # Remove markdown code fences if Nova adds them anyway
        response_text = response_text.strip()

        if response_text.startswith("```json"):
            response_text = response_text[7:]

        if response_text.startswith("```"):
            response_text = response_text[3:]

        if response_text.endswith("```"):
            response_text = response_text[:-3]

        response_text = response_text.strip()

        filled_data = json.loads(response_text)

        print("[Nova] Investigation Diary generated.")
        print("[Nova] Modus Operandi generated.")
        print("[Nova] Statement generated.")
        print("[Nova] All three forms generated successfully.")

        return filled_data

    except Exception as e:
        print("[Nova JSON Error] Nova responded, but the response was not valid JSON.")
        print(f"[Nova JSON Error Details] {e}")
        return {
            "error": f"Unexpected Error: {e}"
        }


