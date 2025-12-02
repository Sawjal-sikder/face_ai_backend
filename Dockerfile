FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
      PYTHONDONTWRITEBYTECODE=1

# Create application directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
      build-essential \
      libpq-dev \
      && rm -rf /var/lib/apt/lists/*


# Copy requirements and install Python packages
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Copy project code
COPY . /app/

# Expose Django/Gunicorn port
EXPOSE 14009

