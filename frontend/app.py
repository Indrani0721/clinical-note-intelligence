import streamlit as st
import requests
import json

# Why this URL?
# Your FastAPI backend is running locally on port 8000
# Streamlit runs on a different port (8501 by default)
# They're two separate processes that communicate via HTTP
API_URL = "http://localhost:8000"

# --- Page config ---
st.set_page_config(
    page_title="Clinical Note Intelligence System",
    page_icon="🏥",
    layout="wide"
)

st.title("🏥 Clinical Note Intelligence System")
st.markdown("Paste a clinical note below to extract and evaluate structured data.")

# --- Input section ---
note_input = st.text_area(
    label="Clinical Note",
    placeholder="58M c/o chest pain x 3 days, worsening with exertion. Hx of HTN, T2DM...",
    height=200
)

# --- Submit button ---
if st.button("Extract & Evaluate", type="primary"):
    
    # Why check for empty input?
    # Same reason as FastAPI — never process empty data
    if not note_input.strip():
        st.error("Please enter a clinical note before submitting.")
    
    else:
        # Show spinner while waiting for the API
        # Why? LLM calls take 2-5 seconds
        # Without this the user sees a frozen page and thinks it crashed
        with st.spinner("Processing note..."):
            
            try:
                response = requests.post(
                    f"{API_URL}/extract",
                    json={"note": note_input}
                )
                
                if response.status_code == 200:
                    data = response.json()
                    extraction = data["extraction"]
                    evaluation = data["evaluation"]
                    note_id = data["note_id"]
                    
                    # --- Success header ---
                    st.success(f"✅ Note processed successfully — ID: `{note_id}`")
                    
                    # --- Overall confidence banner ---
                    overall = evaluation["overall_confidence"]
                    needs_review = evaluation["needs_human_review"]
                    
                    if needs_review:
                        st.warning(
                            f"⚠️ This note needs human review — "
                            f"overall confidence: {overall:.0%}"
                        )
                    else:
                        st.success(
                            f"✅ High confidence extraction — "
                            f"overall confidence: {overall:.0%}"
                        )
                    
                    # --- Two columns: extraction left, evaluation right ---
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.subheader("📋 Extracted Fields")
                        
                        # Why loop instead of hardcoding each field?
                        # If you add a new field to your model later,
                        # this UI updates automatically with no changes
                        for field, value in extraction.items():
                            if value is not None:
                                st.markdown(f"**{field.replace('_', ' ').title()}:** {value}")
                            else:
                                st.markdown(
                                    f"**{field.replace('_', ' ').title()}:** "
                                    f"<span style='color: gray'>Not mentioned</span>",
                                    unsafe_allow_html=True
                                )
                    
                    with col2:
                        st.subheader("🔍 Evaluation & Confidence")
                        
                        # Show each field's confidence as a progress bar
                        # Why progress bar? Humans understand visual scales
                        # better than numbers like 0.76
                        fields_to_show = [
                            "patient_age", "patient_sex", "chief_complaint",
                            "diagnoses", "current_medications", "new_medications",
                            "followup", "referrals", "risk_level"
                        ]
                        
                        for field in fields_to_show:
                            if field in evaluation:
                                field_eval = evaluation[field]
                                confidence = field_eval["confidence"]
                                flagged = field_eval["flag"]
                                reason = field_eval.get("reason")
                                
                                label = field.replace('_', ' ').title()
                                
                                if flagged:
                                    # Red for flagged fields
                                    st.markdown(
                                        f"🚩 **{label}** — {confidence:.0%} confidence"
                                    )
                                    if reason:
                                        st.caption(f"↳ {reason}")
                                else:
                                    # Normal for good fields
                                    st.markdown(
                                        f"✅ **{label}** — {confidence:.0%} confidence"
                                    )
                                
                                st.progress(confidence)

                else:
                    st.error(f"API error: {response.status_code} — {response.text}")
                    
            except requests.exceptions.ConnectionError:
                st.error(
                    "Cannot connect to the API. "
                    "Make sure your FastAPI server is running: "
                    "`uvicorn backend.main:app --reload`"
                )

# --- Divider ---
st.divider()

# --- Notes needing review section ---
st.subheader("📌 Notes Flagged for Human Review")

if st.button("Load flagged notes"):
    with st.spinner("Loading..."):
        try:
            response = requests.get(f"{API_URL}/notes/needs-review")
            
            if response.status_code == 200:
                records = response.json()
                
                if not records:
                    st.info("No notes currently flagged for review.")
                else:
                    st.markdown(f"**{len(records)} note(s) need review:**")
                    
                    for record in records:
                        with st.expander(
                            f"Note {record['note_id'][:8]}... — "
                            f"Confidence: {record['overall_confidence']:.0%} — "
                            f"{record['created_at']}"
                        ):
                            st.text(record["original_note"])
                            
        except requests.exceptions.ConnectionError:
            st.error("Cannot connect to the API.")
