from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
from backend.extractor import extract_clinical_note
from backend.evaluator import evaluate_extraction
from backend.database import get_db, save_note_record, init_db, ClinicalNoteRecord
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

@app.get("/analytics")
def get_analytics(db: Session = Depends(get_db)):
    from sqlalchemy import func
    import json
    
    total_notes = db.query(ClinicalNoteRecord).count()
    
    avg_confidence = db.query(
        func.avg(ClinicalNoteRecord.overall_confidence)
    ).scalar() or 0.0
    
    notes_needing_review = db.query(ClinicalNoteRecord).filter(
        ClinicalNoteRecord.needs_human_review == True
    ).count()
    
    records = db.query(ClinicalNoteRecord).all()
    
    confidence_by_date = {}
    flagged_fields = {}
    recent_notes = []
    
    for record in records:
        date_key = record.created_at.strftime("%Y-%m-%d")
        if date_key not in confidence_by_date:
            confidence_by_date[date_key] = []
        if record.overall_confidence:
            confidence_by_date[date_key].append(record.overall_confidence)
        
        if record.evaluation_data:
            try:
                evaluation = json.loads(record.evaluation_data)
                fields = [
                    "patient_age", "patient_sex", "chief_complaint",
                    "diagnoses", "current_medications", "new_medications",
                    "followup", "referrals", "risk_level"
                ]
                for field in fields:
                    if field in evaluation:
                        if evaluation[field].get("flag"):
                            flagged_fields[field] = flagged_fields.get(field, 0) + 1
            except:
                pass
        
        recent_notes.append({
            "note_id": str(record.id)[:8] + "...",
            "overall_confidence": record.overall_confidence or 0,
            "needs_human_review": record.needs_human_review,
            "created_at": record.created_at.isoformat()
        })
    
    confidence_over_time = [
        {
            "date": date,
            "avg_confidence": sum(scores) / len(scores)
        }
        for date, scores in confidence_by_date.items()
        if scores
    ]
    
    recent_notes = sorted(
        recent_notes,
        key=lambda x: x["created_at"],
        reverse=True
    )[:10]
    
    return {
        "total_notes": total_notes,
        "avg_confidence": float(avg_confidence),
        "notes_needing_review": notes_needing_review,
        "confidence_over_time": confidence_over_time,
        "flagged_fields": flagged_fields,
        "recent_notes": recent_notes
    }
