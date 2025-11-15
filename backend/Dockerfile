# Use the official Python image from the dockerhub
FROM python:3.10-slim-buster

# Set the working directory in the container to /app
WORKDIR /app

# Copy the pyproject.toml file to the working directory
COPY pyproject.toml /app/

# Install the project dependencies
RUN pip install --no-cache-dir --upgrade pip==23.3.1 && \
    pip install --no-cache-dir poetry==1.7.0 && \
    poetry config virtualenvs.create false && \
    poetry install --no-interaction --no-root

# Copy the rest of the code
COPY . /app/

# Start the application
CMD ["poetry", "run", "uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
