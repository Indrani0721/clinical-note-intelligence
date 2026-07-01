from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
from backend.extractor import extract_clinical_note
from backend.evaluator import evaluate_extraction
from backend.database import get_db, save_note_record, init_db
import json

app = FastAPI(
    title="Clinical Note Intelligence System",
    description="Extracts and evaluates structured data from clinical notes",
    version="1.0.0"
)

# Why run this on startup?
# Ensures the table exists before any requests come in
# If someone runs this on a fresh database, it won't crash
@app.on_event("startup")
def startup():
    init_db()


class NoteInput(BaseModel):
    note: str


@app.get("/health")
def health_check():
    return {"status": "ok"}


@app.post("/extract")
def extract_note(input: NoteInput, db: Session = Depends(get_db)):
    
    # Why Depends(get_db)?
    # This is FastAPI's dependency injection
    # It automatically calls get_db() for every request,
    # gives you a fresh database session, and closes it
    # when the request finishes — even if it crashes

    if not input.note.strip():
        raise HTTPException(status_code=400, detail="Note cannot be empty")

    try:
        # Step 1: Extract
        extraction = extract_clinical_note(input.note)
        extraction_dict = extraction.model_dump()

        # Step 2: Evaluate
        evaluation = evaluate_extraction(input.note, extraction_dict)
        evaluation_dict = evaluation.model_dump()

        # Step 3: Save everything to the database
        record = save_note_record(
            db=db,
            original_note=input.note,
            extracted_data=extraction_dict,
            evaluation_data=evaluation_dict,
            overall_confidence=evaluation_dict["overall_confidence"],
            needs_human_review=evaluation_dict["needs_human_review"]
        )

        return {
            "status": "success",
            "note_id": str(record.id),
            "extraction": extraction_dict,
            "evaluation": evaluation_dict
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Processing failed: {str(e)}")


# --- New endpoint: see all notes that need review ---
@app.get("/notes/needs-review")
def get_notes_needing_review(db: Session = Depends(get_db)):
    from backend.database import ClinicalNoteRecord
    
    records = db.query(ClinicalNoteRecord).filter(
        ClinicalNoteRecord.needs_human_review == True
    ).all()
    
    return [
        {
            "note_id": str(r.id),
            "original_note": r.original_note,
            "overall_confidence": r.overall_confidence,
            "created_at": r.created_at.isoformat()
        }
        for r in records
    ]
