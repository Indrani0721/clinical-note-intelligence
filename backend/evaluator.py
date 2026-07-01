from groq import Groq
from dotenv import load_dotenv
from pydantic import BaseModel
from typing import Optional
import os
import json

load_dotenv()

client = Groq(api_key=os.environ.get("GROQ_API_KEY"))


# --- Step 1: Define what an evaluation result looks like ---
# For each field we want to know:
# - confidence: how sure is the LLM that the extraction was correct (0.0 to 1.0)
# - flag: should a human review this? (True/False)
# - reason: why is it flagged? what specifically looks wrong?

class FieldEvaluation(BaseModel):
    confidence: float        # 0.0 = not confident at all, 1.0 = very confident
    flag: bool               # True = human should review this
    reason: Optional[str] = None  # Only needed when flag is True


class ExtractionEvaluation(BaseModel):
    patient_age: FieldEvaluation
    patient_sex: FieldEvaluation
    chief_complaint: FieldEvaluation
    diagnoses: FieldEvaluation
    current_medications: FieldEvaluation
    new_medications: FieldEvaluation
    followup: FieldEvaluation
    referrals: FieldEvaluation
    risk_level: FieldEvaluation
    overall_confidence: float   # Average confidence across all fields
    needs_human_review: bool    # True if ANY field is flagged


# --- Step 2: The evaluation function ---
def evaluate_extraction(
    original_note: str,
    extraction: dict
) -> ExtractionEvaluation:

    # Why pass both the original note AND the extraction?
    # The evaluator needs to compare them side by side
    # It reads the note, reads what was extracted, and checks:
    # "Does the extraction accurately reflect what's in the note?"
    # Without the original note, it has nothing to compare against

    prompt = f"""
    You are a medical data quality reviewer with expertise in clinical documentation.

    IMPORTANT MEDICAL CONTEXT:
    - "58M" means "58 year old Male" — age and sex combined
    - "HTN" means Hypertension — this IS a diagnosis
    - "T2DM" means Type 2 Diabetes Mellitus — this IS a diagnosis  
    - "Hx of" means "history of" — these are existing diagnoses
    - "c/o" means "complains of" — this is the chief complaint
    - If a field is null and the note truly doesn't mention it, that is CORRECT
    - Only flag a field if the extraction is genuinely wrong or missing

    CONFIDENCE SCORING GUIDE:
    - 0.9-1.0: Extraction is clearly correct, matches the note exactly
    - 0.7-0.9: Extraction is mostly correct, minor interpretation differences
    - 0.4-0.7: Something looks wrong, needs review
    - 0.0-0.4: Clearly incorrect or important information was missed

    FLAGGING RULES:
    - flag: true ONLY if confidence is below 0.7
    - flag: false if confidence is 0.7 or above
    - null fields are CORRECT if the note doesn't mention that information

    Your job is to evaluate whether a clinical note was extracted correctly.

    Original Clinical Note:
    {original_note}

    Extracted Data:
    Here is EXACTLY what was extracted — read each field carefully:
    - patient_age: {extraction.get('patient_age')}
    - patient_sex: {extraction.get('patient_sex')}
    - chief_complaint: {extraction.get('chief_complaint')}
    - diagnoses: {extraction.get('diagnoses')}
    - current_medications: {extraction.get('current_medications')}
    - new_medications: {extraction.get('new_medications')}
    - followup: {extraction.get('followup')}
    - referrals: {extraction.get('referrals')}
    - risk_level: {extraction.get('risk_level')}

    A field showing "None" means nothing was extracted for it.
    A field showing a value means the extractor DID find something.
    Evaluate whether each extracted value is correct based on the note.

    Return this exact JSON structure: 
    {{
        "patient_age": {{"confidence": 0.0, "flag": true, "reason": "string or null"}},
        "patient_sex": {{"confidence": 0.0, "flag": true, "reason": "string or null"}},
        "chief_complaint": {{"confidence": 0.0, "flag": true, "reason": "string or null"}},
        "diagnoses": {{"confidence": 0.0, "flag": true, "reason": "string or null"}},
        "current_medications": {{"confidence": 0.0, "flag": true, "reason": "string or null"}},
        "new_medications": {{"confidence": 0.0, "flag": true, "reason": "string or null"}},
        "followup": {{"confidence": 0.0, "flag": true, "reason": "string or null"}},
        "referrals": {{"confidence": 0.0, "flag": true, "reason": "string or null"}},
        "risk_level": {{"confidence": 0.0, "flag": true, "reason": "string or null"}},
        "overall_confidence": 0.0,
        "needs_human_review": true
    }}
    """

    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[
            {
                "role": "system",
                "content": "You are a precise medical data quality reviewer. You return only valid JSON."
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        temperature=0.1
        # Why 0.1 again?
        # Same reason as the extractor — you want consistent
        # evaluation scores, not creative interpretation
    )

    raw_text = response.choices[0].message.content

    try:
        raw_json = json.loads(raw_text)
        
        # Calculate overall_confidence yourself from field scores
        # Never trust the LLM to do math reliably
        field_names = [
            "patient_age", "patient_sex", "chief_complaint",
            "diagnoses", "current_medications", "new_medications",
            "followup", "referrals", "risk_level"
        ]
        
        scores = [
            raw_json[field]["confidence"] 
            for field in field_names 
            if field in raw_json
        ]
        
        calculated_confidence = sum(scores) / len(scores) if scores else 0.0
        raw_json["overall_confidence"] = round(calculated_confidence, 2)
        
        # needs_human_review is true if ANY field is flagged
        raw_json["needs_human_review"] = any(
            raw_json[field]["flag"] 
            for field in field_names 
            if field in raw_json
        )
        
        evaluation = ExtractionEvaluation(**raw_json)
        return evaluation

    except json.JSONDecodeError as e:
        print(f"Evaluator returned invalid JSON: {e}")
        print(f"Raw response: {raw_text}")
        raise


# --- Step 3: Test it ---
if __name__ == "__main__":

    # Use the same note as before
    sample_note = """
    58M c/o chest pain x 3 days. Hx of HTN, T2DM. 
    Current meds: metformin 500mg. Starting lisinopril 10mg. 
    Follow up in 2 weeks.
    """

    # This is what your extractor returned last week
    # Notice the errors we spotted:
    # - diagnoses was null (wrong, note mentions HTN and T2DM)
    # - lisinopril appeared in current_medications (wrong, it was newly prescribed)
    sample_extraction = {
        "patient_age": "58",
        "patient_sex": "M",
        "chief_complaint": "chest pain x 3 days",
        "diagnoses": None,
        "current_medications": ["metformin 500mg", "lisinopril 10mg"],
        "new_medications": ["lisinopril 10mg"],
        "followup": "in 2 weeks",
        "referrals": None,
        "risk_level": "medium"
    }

    print("Sending extraction to evaluator...")
    print("-" * 40)

    result = evaluate_extraction(sample_note, sample_extraction)

    print(json.dumps(result.model_dump(), indent=2))
