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
        section below as self-contained for its own field logic, and do not let
        field names from one section bleed into another. However, the facts must
        be identical on all three forms: case number, station, date, time, place,
        instrument and suspect descriptions must never differ between sections.
        Here is the completed P21 form and the case number, including the complainant's statement in the form:
        {json.dumps(p21_form, indent=4)}
        CASE NUMBER:
        {case_number}
        ============================================================
        GENERAL RULES (apply to all three sections)
        ============================================================
        Every field must contain a value. Never return null or an empty string,
        except where a field below says to return "".
        SOURCE PRIORITY (use in this order):
        1. Facts stated in the P21 form.
        2. Fixed defaults stated in these rules.
        3. If neither applies, write exactly "PENDING".
        PLACEHOLDERS (use exactly these words, never "not specified"):
        - "N/A" = the field does not apply to this case (for example, no property
        was involved, or no premises were entered).
        - "PENDING" = the field applies, but the detail is not in the P21 form and
        will be completed later by the officer or the system (for example, a
        reference number or a postal code that cannot be worked out).
        Never guess, estimate, or invent names, numbers, addresses, postal codes,
        ranks or reference numbers. An honest "PENDING" is always better than a
        fabricated detail in a case file. Never copy a value into a different field
        just to fill it.
        FORMATS:
        - Dates on the diary and modus operandi: DD Month YYYY (e.g. 6 August 2026).
        - Dates on the statement: YYYY-MM-DD (e.g. 2026-08-06).
        - Times: 24-hour HH:MM (e.g. 21:45).
        EXTRACTION RULES:
        - The incident date and time are the first date and time in the statement.
        - The deponent (the person giving the statement) is not a witness and is
        never an officer. Never take an officer's name from the P21 text.
        - Classify the offence from the outcome. If the victim died as a result of
        the attack, the offence is "Murder". Do not use another classification
        unless the statement says death did not occur.
        - Write neutrally: say "suspects", not "murderers" or "killers". Do not
        state anything as proven that the statement does not say.
        - Copy suspect details exactly as written. Do not merge, reorder or
        embellish them.
        ============================================================
        SECTION 1: investigationDiary
        ============================================================
        You are completing an Investigation Diary entry for a police case file.
        An Investigation Diary is the chronological working record of a case -
        it captures WHEN things happened and WHAT is relevant for building the
        case, so an investigator can review the case history at a glance.
        Fill in the following fields using ONLY what is stated in the P21 form.
        Do not force an answer where the statement does not support one.
        1. station
        The police station responsible for handling this matter, as stated in the
        P21 form. If the station is not mentioned, use "JHB Central". The value
        must be identical to the station on the statement section.
        2. casNo
        The case number, exactly as given above. Format AREA/NNNNN/YEAR
        (e.g. JHB/00089/2026).
        3. entries
        A list of diary entries describing what happened.
        - date: the date the incident occurred, as stated in the statement
        (DD Month YYYY)
        - time: the time the incident occurred, as stated in the statement (HH:MM)
        - particulars: a factual, investigator-useful account of what
            happened, written the way an officer would log it in a diary.
            State who did what, to whom, where, and the outcome. Include
            details that could help build the case or lead to a suspect - for
            example, presence of CCTV footage, distinguishing suspect
            features, direction suspects fled, items taken, or anything the
            complainant offered (e.g. willingness to view an identification
            parade). Do not copy the statement word for word. Maximum 3 lines,
            stating the particulars only, with no story telling and no opinions.
        4. notes
        A short 1-2 sentence high-level summary of the incident: the type of
        case, whether the suspects are known, and who identified them. Enough for
        someone to understand what the case is about at a glance.
        5. investigatingOfficer
        Always return "". The investigating officer is the officer who compiled
        the case (the logged-in officer), and the system fills this in after you
        respond. Never take this from the P21 form.
        ============================================================
        SECTION 2: modusOperandi
        ============================================================
        You are completing a Modus Operandi (MO) form for a police case file.
        This form records the PATTERN of how a crime was carried out, so
        investigators can compare it against other cases and identify repeat
        offenders or linked incidents. The letter prefixes on each field name
        (A_, B_, C_, etc.) are just labels for form layout - ignore them and
        focus only on the meaning of the field name itself.
        Fill in the following fields using ONLY what is stated in the P21 form.
        casNumber - the case number, exactly as given above.
        ir - the Incident Report number. It is never in a statement. Always write
        "PENDING".
        A_offence - the specific crime committed against the victim, which is the
        reason this case was opened (e.g. Murder, robbery, assault, theft).
        Classify from the outcome (see general rules).
        B_date - the date on which the offence occurred (DD Month YYYY).
        C_time - the time at which the offence occurred (HH:MM).
        D_place - the exact place where the offence occurred: premises name,
        sub-location (e.g. parking area), street, suburb and city, as stated.
        E_methodUsed - HOW the suspect(s) carried out the offence, as a short
        phrase describing the actions in order (e.g. Physical assault followed by
        stabbing). Not a story.
        F_instrumentUsed - the physical object, weapon, or tool used to commit
        the offence (e.g. firearm, knife), in one or two words. If a weapon was
        used, do not list fists. If nothing was used, write "N/A".
        G_propertyInvolvedAndValue - if any property was taken, damaged, or
        otherwise involved (cash, phones, a vehicle, or other possessions),
        describe exactly what was involved and its value if stated. If no
        property was involved, write "No property involved".
        H_serialOrRegistrationNo - ONLY fill this in if the offence involves a
        vehicle or an item with a stated serial or registration number. If no
        property or vehicle is involved, write "N/A". If a vehicle is involved but
        no number is given, write "PENDING". Do not invent a number under any
        circumstances.
        I_suspects - a list with ONE entry per suspect described in the
        statement. For each suspect, provide:
        - involved: the suspect's name if the statement gives it, otherwise
        "Suspect 1", "Suspect 2", etc., in the order they are introduced in the
        statement.
        - description: their individual characteristics exactly as described in
        the statement: sex, approximate age, height in metres, build,
        complexion, hair, facial hair and clothing. Any detail not given is
        written as "Not described". Do not merge multiple suspects into a single
        description; each suspect gets their own entry. If the statement does not
        distinguish individual suspects at all, return a single entry with
        involved set to "Suspect 1" and description set to "Not described".
        J_witnessDetails - details of anyone other than the deponent who
        witnessed the incident in any way (saw it, heard it, or was present and
        could have observed something relevant). Give name, age if stated, and
        what they saw. If there are none, write "N/A".
        K_circulationNo, K_lcrcNo, L_sap13No, L_sap14No - these are internal
        administrative reference numbers that are never contained in a statement.
        Always write "PENDING" for these four fields.
        M_comments - additional investigative facts from the statement: how the
        suspects were identified, who used the weapon, direction the suspects
        fled, whether their whereabouts are known, witnesses available, CCTV
        footage, willingness to attend an identification parade.
        N_compiledBy - the officer who compiled this form (the logged-in
        officer). The system fills this in after you respond. Always return
        "no", "rank", and "initialAndSurname" as empty strings "".
        O_perusedBy - the commander who reviews this form, assigned at a later
        stage. Always return "no", "rank", and "initialAndSignature" as "PENDING".
        checklist - this is a separate administrative checklist not covered by
        the statement. Always return this as an empty list [].
        ============================================================
        SECTION 3: statement
        ============================================================
        You are completing a Statement Form for a police case file, based on
        information already captured in a P21 complainant statement.
        Fill in the following fields using ONLY what is stated in the P21 form,
        plus ordinary context (for example, a tavern is business premises).
        station - the police station, as stated in the P21 form. If it is not
        mentioned, use "JHB Central". Must be identical to the diary station.
        cas - the case number, exactly as given above.
        whenCertain vs whenUncertainRange - these two sections are
        alternatives, not both used at once. Read the statement and decide:
        - If the statement gives a specific, exact date and time for when the
        offence occurred (e.g. "on 6 August 2026 at approximately 21:45"), this
        counts as CERTAIN. Fill in "whenCertain" with a short description of what
        happened at that time, plus the date (YYYY-MM-DD) and time (HH:MM). In
        this case, write "N/A" for every value inside "whenUncertainRange".
        - If instead the deponent is unsure of exactly when it happened and can
        only give a range or estimate (e.g. "sometime between Friday night and
        Saturday morning"), this counts as UNCERTAIN. Fill in
        "whenUncertainRange" with a description plus the "from" and "to"
        date/time boundaries given. In this case, write "N/A" for every value
        inside "whenCertain".
        Never guess a range if a certain time is given, and never invent a false
        sense of certainty if the deponent was actually unsure. Note that the
        "certain" label refers to the person giving the statement, not the
        victim.
        dayOfWeek - work out the day of the week using the DATE found above
        (certain or uncertain), based on a real calendar - do not copy a day
        of the week merely because it happens to be mentioned in the
        statement. Count carefully from the date and write the full weekday
        name (e.g. Thursday). Only provide this if a complete, specific date
        (day, month, and year) was found. If no usable complete date was
        found, or if you cannot reliably determine the day of week from it,
        write "PENDING".
        offenceDescription - one clear, factual sentence stating who was harmed,
        what was done, by whom, and the outcome (e.g. The deceased, Themba
        Ndlovu, was assaulted and stabbed by three suspects following an
        argument, resulting in his death).
        methodEntrance - HOW the suspect(s) gained access to the scene, only if
        the offence involved forcing or gaining entry to premises (e.g. broke a
        window, forced a door). If no entry was involved (for example, the
        incident happened in an open or public place), write "N/A".
        instrumentType - the weapon, tool, or object used by the suspect(s).
        Must match F_instrumentUsed. If none was used, write "N/A".

        betweenA, betweenB, street, building, suburb, town - these six
        fields describe the address of the place where the offence occurred.
        Each one is its own separate top-level key of the statement
        section. Do NOT nest them inside another object and do NOT return a
        "scene" key. Spell the key "suburb" exactly as shown. Every one of
        these keys must hold a text value, never null and never an empty
        string.

        The location is either EXACT or APPROXIMATE. These are alternatives,
        not both used at once. Read the statement and decide:
        - EXACT: the statement names a specific street and/or building where
        the offence happened (e.g. "at Blue Moon Tavern on 7th Avenue").
        Fill "street" and "building" with those details. Write "N/A" for
        both "betweenA" and "betweenB".
        - APPROXIMATE: the complainant is not sure of the exact spot and
        describes it as being between or around two places (e.g. "between
        the garage and the taxi rank", "between 5th and 6th Street"). Fill
        "betweenA" with the first place and "betweenB" with the second place,
        in the order given. Fill "street" and "building" only if the
        statement also names them, otherwise write "N/A".
        Never invent betweenA or betweenB from nearby streets, landmarks or
        the direction the suspects fled. They come only from two places the
        complainant actually gave as the approximate location. Never invent
        a false sense of certainty if the complainant was actually unsure.

        street - the street the offence happened on (e.g. 7th Avenue). Use
        the street named for the incident location, not the deponent's home
        street. If the location is exact but no street is stated, work it
        out from the place named only if you reliably know it, otherwise
        write "PENDING".
        building - the name of the building, business or premises where the
        offence occurred (e.g. Blue Moon Tavern). If it happened in an open
        space with no named building, write "N/A".
        suburb - the suburb or township of the place (e.g. Alexandra), as
        stated, or the one the named street or premises belongs to. Always
        filled, in both cases.
        town - the city or town of the place (e.g. Johannesburg), as stated,
        or the one the suburb belongs to. Always filled, in both cases.
        Use ordinary geographic knowledge of the named place (for example,
        knowing which suburb a named street or tavern belongs to) when the
        statement names the place but not every part of its address. Never
        invent a street, building or area that is not supported by the
        statement or by what you reliably know about the place named in it.
        Use "PENDING" only as a last resort when nothing points to a detail.

        postalCode - the 4-digit postal code of the place where the
        offence occurred. Use the one given in the
        statement. If none is given, work it out from the place named in
        the statement (street, building or suburb) and write the code that
        belongs to that place. If you are not sure, write "PENDING".
        geographicalBlock - the police sector or block code. It is never in a
        statement. Always write "PENDING".
        premisesType - the type of premises where the offence occurred, chosen
        from: business/shop, private residence, open street, vehicle. Base it on
        the scene description (a tavern or shop is business/shop). If none fits,
        write "PENDING".
        footerDate - the date the statement was taken, which is not the incident
        date. It is not in the P21 form. Always write "PENDING".
        footerSignature - the officer's sign-off, which is not in the P21 form.
        Always write "PENDING".

        BEFORE RETURNING, CHECK:
        - Every field is present. None are empty (except the "" fields above) and
        none say "not specified".
        - Case number, station, date, time, place and instrument are identical on
        all three sections.
        - The number of suspects in I_suspects equals the number described in the
        P21 form.
        - dayOfWeek is the correct weekday for the statement date on a real
        calendar. Recount it if unsure.
        - betweenA, betweenB, street, building, suburb and town are all present
        as separate keys, with no nested "scene" object. betweenA and betweenB
        are "N/A" whenever the location is exact.

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


