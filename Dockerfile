# ---------- Stage 1: Build ----------
    FROM python:3.10.0-slim AS builder

    # Set working directory
    WORKDIR /app
    
    # Install system dependencies
    RUN apt-get update && apt-get install -y gcc && rm -rf /var/lib/apt/lists/*
    
    # Copy requirements and install dependencies into a temp location
    COPY requirements.txt .
    RUN pip install --no-cache-dir --prefix=/install -r requirements.txt
    
    # ---------- Stage 2: Runtime ----------
    FROM python:3.10.0-slim
    
    # Set working directory
    WORKDIR /app
    
    # Create non-root user
    RUN addgroup --system appgroup && adduser --system --ingroup appgroup appuser
    
    # Copy installed dependencies
    COPY --from=builder /install /usr/local
    
    # Copy app source code
    COPY . .
    
    # Create and set permission for config directory
    RUN mkdir -p /app/config && chown -R appuser:appgroup /app /app/config
    
    # Use non-root user
    USER appuser
    
    # Expose FastAPI port
    EXPOSE 8000
    
    # Command to run the app
    CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
    