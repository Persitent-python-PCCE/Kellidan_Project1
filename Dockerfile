FROM python:3.12-slim

# 1. Create a non-root user and set permissions
RUN adduser --disabled-password --gecos "" appuser

WORKDIR /app

# 2. Copy dependencies first
COPY requirements.txt .

# 3. Install packages as binary-only wheels without executing source setup scripts
RUN pip install  -r requirements.txt
# --no-cache-dir --only-binary=:all:
# 4. Copy application source code
COPY . .

# 5. Change ownership to the non-root user
RUN chown -R appuser:appuser /app

# 6. Switch away from root user
USER appuser

EXPOSE 5000

CMD ["python", "app.py"]