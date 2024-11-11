# Use NVIDIA CUDA base image
FROM nvidia/cuda:12.6.2-cudnn-devel-ubuntu22.04

# Set environment variables to avoid prompts
ENV DEBIAN_FRONTEND=noninteractive
ENV TZ=Europe/Zurich
ENV LD_LIBRARY_PATH /usr/local/nvidia/lib64:${LD_LIBRARY_PATH}

# Set the working directory
WORKDIR /app

# Copy requirements file
COPY requirements.txt .

# Install Python, dependencies, and other tools
RUN apt-get update && \
    apt-get install -y python3 python3-pip ffmpeg libmagic1 && \
    pip3 install --no-cache-dir -r requirements.txt && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# Copy the source code
COPY src/ src/

# Expose the port for the application
ENV PORT 8080

# Start the Uvicorn server
CMD ["uvicorn", "src.app:app", "--host", "0.0.0.0", "--port", "8080", "--workers", "1"]