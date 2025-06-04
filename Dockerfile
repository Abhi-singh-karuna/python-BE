# ---------- Stage 1: Build ----------
    FROM python:3.10.0-slim AS builder

    WORKDIR /app
    
    # Define build arguments
    ARG DB_HOST
    ARG DB_USER
    ARG DB_PASSWORD
    ARG DB_NAME
    ARG DB_PORT
    
    # Optionally use them in build steps if needed
    
    RUN apt-get update && apt-get install -y gcc && rm -rf /var/lib/apt/lists/*
    
    COPY requirements.txt .
    RUN pip install --no-cache-dir --prefix=/install -r requirements.txt
    
    # ---------- Stage 2: Runtime ----------
    FROM python:3.10.0-slim
    
    WORKDIR /app
    
    RUN addgroup --system appgroup && adduser --system --ingroup appgroup appuser
    
    COPY --from=builder /install /usr/local
    COPY config/ /app/config/
    COPY . .
    
    RUN mkdir -p /app/config && chown -R appuser:appgroup /app
    
    # Bring build-time ARGs into this stage
    ARG DB_HOST
    ARG DB_USER
    ARG DB_PASSWORD
    ARG DB_NAME
    ARG DB_PORT
    
    # Now set ENV from ARGs
    ENV POLICY_GENERAL__SQL__WRITE__HOST=${DB_HOST}
    ENV POLICY_GENERAL__SQL__WRITE__USER=${DB_USER}
    ENV POLICY_GENERAL__SQL__WRITE__PASSWORD=${DB_PASSWORD}
    ENV POLICY_GENERAL__SQL__WRITE__DATABASE=${DB_NAME}
    ENV POLICY_GENERAL__SQL__WRITE__PORT=${DB_PORT}
    
    USER appuser
    
    EXPOSE 8000
    
    CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
    