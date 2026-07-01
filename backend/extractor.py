from groq import Groq
from dotenv import load_dotenv
from pydantic import BaseModel
from typing import Optional
import os
import json

load_dotenv()

client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

# --- Step 1: Define your Pydantic model ---
# This is the structure you EXPECT the LLM to return
# Every field has a type — str, list, Optional means it might be missing
# Why Optional? Because not every note mentions every field
# A doctor might not mention referrals if none are needed

class ClinicalExtraction(BaseModel):
    patient_age: Optional[str] = None       # e.g. "58 years old"
    patient_sex: Optional[str] = None       # e.g. "Male"
    chief_complaint: Optional[str] = None   # e.g. "chest pain for 3 days"
    diagnoses: Optional[list[str]] = None   # e.g. ["hypertension", "type 2 diabetes"]
    current_medications: Optional[list[str]] = None  # existing meds
    new_medications: Optional[list[str]] = None      # newly prescribed
    followup: Optional[str] = None          # e.g. "2 weeks"
    referrals: Optional[str] = None         # e.g. "cardiology"
    risk_level: Optional[str] = None        # "low", "medium", "high"


# --- Step 2: Write the extraction function ---
def extract_clinical_note(note: str) -> ClinicalExtraction:
    
    # Why this prompt structure?
    # 1. You tell the LLM exactly what role it plays (system message)
    # 2. You give it the note + tell it EXACTLY what format to return
    # 3. You explicitly say "return ONLY JSON" — otherwise it adds 
    #    conversational text like "Sure! Here is the extraction:"
    #    which breaks your JSON parser
    
    prompt = f"""
    You are a medical data extraction assistant.
    Extract the following fields from the clinical note below.
    
    Return ONLY a valid JSON object with these exact keys:
    - patient_age (string or null)
    - patient_sex (string or null)  
    - chief_complaint (string or null)
    - diagnoses (list of strings or null)
    - current_medications (list of strings or null)
    - new_medications (list of strings or null)
    - followup (string or null)
    - referrals (string or null)
    - risk_level (string: "low", "medium", or "high" based on clinical urgency)
    
    If a field is not mentioned in the note, return null for that field.
    Do not include any explanation or text outside the JSON object.
    
    Clinical Note:
    {note}
    """
    
    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[
            {
                "role": "system",
                "content": "You are a precise medical data extraction assistant. You return only valid JSON, nothing else."
            },
            {
                "role": "user", 
                "content": prompt
            }
        ],
        temperature=0.1  
        # Why temperature=0.1?
        # Temperature controls how "creative" the LLM is
        # 0.0 = very deterministic, same answer every time
        # 1.0 = more creative and varied
        # For data extraction you want LOW temperature
        # You want consistent, accurate extraction not creative interpretation
    )
    
    # --- Step 3: Parse the response ---
    # The LLM returns text — we need to convert it to a Python dict
    # then validate it against our Pydantic model
    
    raw_text = response.choices[0].message.content
    
    # Why try/except here?
    # LLMs sometimes return slightly malformed JSON despite instructions
    # Instead of crashing, you catch the error and handle it gracefully
    # In production systems, silent failures are worse than loud ones
    try:
        raw_json = json.loads(raw_text)
        extraction = ClinicalExtraction(**raw_json)
        return extraction
    except json.JSONDecodeError as e:
        print(f"LLM returned invalid JSON: {e}")
        print(f"Raw response was: {raw_text}")
        raise


# --- Step 4: Test it with a sample note ---
if __name__ == "__main__":
    
    sample_note = """
    58M c/o chest pain x 3 days, worsening with exertion. 
    Hx of HTN, T2DM. Current meds: metformin 500mg, amlodipine 5mg. 
    EKG done - normal sinus rhythm. Advised to reduce salt intake. 
    Starting lisinopril 10mg. 
    Refer to cardiology if symptoms persist.
    """
    
    print("Sending note to LLM for extraction...")
    print("-" * 40)
    
    result = extract_clinical_note(sample_note)
    
    # .model_dump() converts your Pydantic object back to a dict
    # json.dumps with indent=2 makes it readable
    print(json.dumps(result.model_dump(), indent=2))
