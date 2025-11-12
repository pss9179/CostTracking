FROM python:3.11-slim

WORKDIR /app

# Copy proxy code
COPY proxy/ /app/proxy/
COPY collector/pricing/ /app/collector/pricing/

# Install dependencies
RUN pip install --no-cache-dir -r proxy/requirements.txt

# Expose proxy port
EXPOSE 9000

# Run proxy
CMD ["uvicorn", "proxy.main:app", "--host", "0.0.0.0", "--port", "9000"]

