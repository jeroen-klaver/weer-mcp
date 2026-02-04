FROM python:3.11-slim

WORKDIR /app

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY src/ ./src/

# Make the script executable
RUN chmod +x src/weather_server.py

# Run the server
CMD ["python", "src/weather_server.py"]
