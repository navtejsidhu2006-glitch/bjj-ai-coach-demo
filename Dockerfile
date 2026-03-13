FROM python:3.11-slim

# cache-bust: v2
WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy app code
COPY main.py .

# Run via Python so $PORT is read inside the process, not by the shell
CMD ["python", "main.py"]
