# Use an official Python runtime as a parent image
FROM python:3.10.14

# Set the working directory in the container
WORKDIR /usr/src/app

# Copy the current directory contents into the container
COPY . .

# Install system dependencies and Rust
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    gcc \
    curl \
    && apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Install Rust using rustup and retry if it fails
RUN curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y || \
    (sleep 5 && curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y)

# Set environment variables for Rust
ENV PATH="/root/.cargo/bin:${PATH}"

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt
# Ensure ~/.local/bin is in the PATH
ENV PATH="/root/.local/bin:${PATH}"
# Make port 5000 available to the world outside this container
EXPOSE 5000

# Define environment variable
ENV FLASK_APP=run.py

# Run the command to start the Flask server
CMD ["flask", "run", "--host=0.0.0.0"]
