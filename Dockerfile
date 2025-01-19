# Use the official Python image as a bases
FROM --platform=linux/amd64 python:3.9-slim

# Set the working directory
WORKDIR /app

# Copy requirements file and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application code
COPY . .

# Set environment variables
ENV PORT=8080
ENV PYTHONPATH=/app

# Expose the port
EXPOSE 8080

# Run the Flask application with gunicorn
# Run the Flask application with gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:8080", "--workers", "1", "--threads", "8", "--timeout", "0", "--log-level", "debug", "app:app"]