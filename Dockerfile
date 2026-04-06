FROM python:3.10-slim

# Prevent python from buffering logs
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Install system dependencies if needed
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first (better caching)
COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

# Copy app
COPY . .

# Expose SNMP trap port (UDP 162 example)
EXPOSE 162/udp

CMD ["python", "app/pysnmp_trap_receiver.py"]