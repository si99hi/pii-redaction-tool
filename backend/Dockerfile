FROM python:3.11-slim

# Install build dependencies (needed for package installations)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Set up user 1000 (required by Hugging Face Spaces to run as non-root)
RUN useradd -m -u 1000 user
USER user
ENV PATH="/home/user/.local/bin:${PATH}"

WORKDIR /home/user/app

# Copy requirements and install dependencies
COPY --chown=user requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# Download spaCy model
RUN python -m spacy download en_core_web_sm

# Copy the rest of the application
COPY --chown=user . .

# Expose port (Hugging Face Spaces defaults to 7860)
EXPOSE 7860

# Run the FastAPI server
CMD ["python", "-m", "uvicorn", "app:app", "--host", "0.0.0.0", "--port", "7860"]
