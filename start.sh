#!/bin/bash

# Why run uvicorn in background (&)?
# Without & it would block and Streamlit would never start
# & runs it in background, then continues to next command
uvicorn backend.main:app --host 0.0.0.0 --port 8000 &

# Why --host 0.0.0.0?
# Inside a container, localhost only refers to the container itself
# 0.0.0.0 means "accept connections from outside the container"
# Without this, you couldn't reach FastAPI from your browser

# Run Streamlit in foreground
# This keeps the container alive — when this process ends, container stops
streamlit run frontend/app.py --server.port 8501 --server.address 0.0.0.0
