import pytest
from unittest.mock import patch, MagicMock
from backend.extractor import ClinicalExtraction


def test_clinical_extraction_model_valid():
    """Test that ClinicalExtraction accepts valid data"""
    extraction = ClinicalExtraction(
        patient_age="58",
        patient_sex="M",
        chief_complaint="chest pain",
        diagnoses=["hypertension", "type 2 diabetes"],
        current_medications=["metformin 500mg"],
        new_medications=["lisinopril 10mg"],
        followup="2 weeks",
        referrals="cardiology",
        risk_level="medium"
    )
    assert extraction.patient_age == "58"
    assert extraction.patient_sex == "M"
    assert extraction.risk_level == "medium"


def test_clinical_extraction_model_optional_fields():
    """Test that optional fields can be None"""
    extraction = ClinicalExtraction(
        patient_age="45",
        patient_sex="F"
    )
    assert extraction.diagnoses is None
    assert extraction.followup is None
    assert extraction.referrals is None


def test_clinical_extraction_model_null_values():
    """Test that null values are handled correctly"""
    extraction = ClinicalExtraction()
    assert extraction.patient_age is None
    assert extraction.patient_sex is None
    assert extraction.chief_complaint is None
