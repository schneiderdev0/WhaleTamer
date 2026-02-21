# Use a lightweight Python image
FROM python:3.11-slim-buster

# Set the working directory in the container
WORKDIR /app

# Install uv, the dependency manager indicated by uv.lock
RUN pip install uv

# Copy dependency files first to leverage Docker cache
COPY pyproject.toml uv.lock ./

# Install dependencies using uv
RUN uv sync

# Copy the rest of the application code
COPY backend ./backend

# Expose the port the application will run on
EXPOSE 8000

# Command to run the application using Uvicorn
# Assuming the main FastAPI app object is named 'app' in 'backend/app/main.py'
CMD ["uvicorn", "backend.app.main:app", "--host", "0.0.0.0", "--port", "8000"]