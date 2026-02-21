FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Install system dependencies required for CadQuery
RUN apt-get update && apt-get install -y \
    libgl1-mesa-glx \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Expose port 4242
EXPOSE 4242

# Run the application
# We use flask run directly, binding to 0.0.0.0 for external access
# and specifying port 4242 to match the application default.
CMD ["flask", "run", "--host=0.0.0.0", "--port=4242"]
