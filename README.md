# Audio Transcription Service

This service accepts audio input and returns a transcription as a JSON object. It leverages 'insanely-fast-whisper' for audio transcription and is designed to run on GPUs in Google Cloud Run.

## Requirements

- Docker
- NVIDIA GPU with CUDA support (for local GPU execution)
- For development on non-GPU machines, the code defaults to CPU execution.

## Configuration

Copy `.env.example` to `.env` and fill in the required environment variables:
HF_TOKEN=your_huggingface_token

You can adjust other configurations in the `.env` file as needed.

## Running Locally

1. Install the required Python packages:

    ```
    pip install -r requirements.txt
    ```

2. Run the application:

    ```
    uvicorn src.app:app --host 0.0.0.0 --port 8080
    ```

## Building the Docker Image

docker build -t audio-transcription-service .

## Deploying to Google Cloud Run

1. **Build and push the Docker image to Google Container Registry or Artifact Registry**:

    ```
    docker tag audio-transcription-service gcr.io/YOUR_PROJECT_ID/audio-transcription-service
    docker push gcr.io/YOUR_PROJECT_ID/audio-transcription-service
    ```

2. **Deploy the service with GPU support**:

    ```
    gcloud beta run deploy audio-transcription-service \
        --image gcr.io/YOUR_PROJECT_ID/audio-transcription-service \
        --region YOUR_REGION \
        --platform managed \
        --allow-unauthenticated \
        --cpu 4 \
        --memory 16Gi \
        --gpu 1 \
        --gpu-type nvidia-l4 \
        --max-instances 1 \
        --no-cpu-throttling \
        --set-env-vars HF_TOKEN=your_huggingface_token
    ```

    Replace `YOUR_PROJECT_ID` and `YOUR_REGION` with your Google Cloud project ID and desired region.

3. **Ensure necessary quotas and permissions**:

    - Request GPU quota in your region.
    - Ensure your service account has the necessary roles.

## Notes

- The service requires at least 4 CPUs and 16 GiB of memory when deploying to Cloud Run with GPU support.

- Make sure to set the `LD_LIBRARY_PATH` environment variable as required by Cloud Run GPU documentation.

Make sure to set the environment variables in the Cloud Run service with your `.env` configurations.