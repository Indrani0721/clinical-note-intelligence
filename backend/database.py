from sqlalchemy import create_engine, Column, String, Float, Boolean, Text, DateTime
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.dialects.postgresql import UUID
from dotenv import load_dotenv
from datetime import datetime
import uuid
import os

load_dotenv()

# --- Step 1: Database connection ---
# Why DATABASE_URL in .env?
# Same reason as API key — never hardcode credentials in your code
# When you deploy to the cloud, you just change the .env file
# not the code itself

DATABASE_URL = os.environ.get(
    "DATABASE_URL",
    "postgresql://clinical_user:clinical_pass@localhost/clinical_notes_db"
)

# Why create_engine?
# This is your connection to PostgreSQL
# SQLAlchemy manages the connection pool — 
# meaning it reuses connections instead of
# opening a new one for every request (which would be slow)
engine = create_engine(DATABASE_URL)

# Why SessionLocal?
# A session is one "conversation" with the database
# You open a session, do your queries, close it
# Each API request gets its own session
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

# Base is the foundation all your table models inherit from
Base = declarative_base()


# --- Step 2: Define your table ---
# This class = one table in PostgreSQL
# Each attribute = one column

class ClinicalNoteRecord(Base):
    __tablename__ = "clinical_notes"

    # Why UUID instead of 1, 2, 3?
    # Auto-incrementing integers are predictable — 
    # someone could guess note IDs
    # UUIDs are random and unique — 
    # better for medical records privacy
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )

    # The raw note exactly as the doctor submitted it
    original_note = Column(Text, nullable=False)

    # Why Text not String?
    # String has a length limit (usually 255 chars)
    # Clinical notes can be very long — Text has no limit

    # Store extraction and evaluation as JSON strings
    # Why not separate columns for each field?
    # Because your extraction schema might change as you improve it
    # Storing as JSON means you don't have to change the database
    # every time you update your Pydantic model
    extracted_data = Column(Text, nullable=True)
    evaluation_data = Column(Text, nullable=True)

    # These two are stored separately for easy querying
    # You don't want to parse JSON every time you want to filter
    overall_confidence = Column(Float, nullable=True)
    needs_human_review = Column(Boolean, default=False)

    # Automatically set when the record is created
    # Why default=datetime.utcnow?
    # UTC ensures consistency regardless of timezone
    # A clinic in Boston and one in LA both store the same format
    created_at = Column(DateTime, default=datetime.utcnow)


# --- Step 3: Create the table ---
def init_db():
    Base.metadata.create_all(bind=engine)
    print("Database tables created successfully")


# --- Step 4: Dependency for FastAPI ---
# This function gives each API request its own database session
# Why yield instead of return?
# yield pauses here, lets the request run, then comes back
# to close the session — even if the request fails
# This guarantees sessions are always cleaned up properly
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# --- Step 5: Save a complete record ---
def save_note_record(
    db,
    original_note: str,
    extracted_data: dict,
    evaluation_data: dict,
    overall_confidence: float,
    needs_human_review: bool
) -> ClinicalNoteRecord:

    import json

    record = ClinicalNoteRecord(
        original_note=original_note,
        extracted_data=json.dumps(extracted_data),
        evaluation_data=json.dumps(evaluation_data),
        overall_confidence=overall_confidence,
        needs_human_review=needs_human_review
    )

    db.add(record)      # Stage the record
    db.commit()         # Write to database
    db.refresh(record)  # Get the saved record back with its ID
    return record


# --- Step 6: Test the connection ---
if __name__ == "__main__":
    init_db()
