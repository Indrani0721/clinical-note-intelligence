# Start with an official Python image
# Why 3.11-slim? Slim removes unnecessary system packages
# making the image smaller and faster to download
FROM python:3.11-slim

# Set working directory inside the container
# All commands from here run inside /app
WORKDIR /app

# Why copy requirements first, then the rest of the code?
# Docker caches each step — if requirements.txt hasn't changed,
# it skips the pip install step entirely on rebuilds
# This makes rebuilds much faster during development
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Now copy the rest of your code
COPY . .

# Why create a startup script?
# You need TWO processes running — FastAPI and Streamlit
# Docker containers typically run one process
# A startup script lets you run both
COPY start.sh .
RUN chmod +x start.sh

# Expose both ports
# FastAPI runs on 8000, Streamlit on 8501
EXPOSE 8000
EXPOSE 8501

# Run the startup script when container starts
CMD ["./start.sh"]
