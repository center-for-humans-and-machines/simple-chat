# Use the official Python image from the dockerhub
FROM python:3.15-slim-bookworm

# Set the working directory in the container to /app
WORKDIR /app

# Copy the pyproject.toml file to the working directory
COPY pyproject.toml poetry.lock /app/

# Install the project dependencies
RUN pip install --no-cache-dir --upgrade pip==23.3.1 && \
    pip install --no-cache-dir poetry==2.1.2 && \
    poetry config virtualenvs.create false && \
    poetry install --no-interaction --no-root

# Copy the rest of the code
COPY . /app/

# Start the application
CMD ["poetry", "run", "uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
