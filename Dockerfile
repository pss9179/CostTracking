FROM python:3.11-slim

WORKDIR /app

# Copy and install dependencies from collector directory
COPY collector/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy collector application code
COPY collector/ .

# Expose port
EXPOSE 8000

# Start command - Railway sets PORT env var
CMD uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}

