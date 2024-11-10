import os
import uuid
import json
import asyncio
import torch
import tempfile
import shutil
import logging
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import JSONResponse
from dotenv import load_dotenv
from starlette.status import HTTP_400_BAD_REQUEST
import magic

load_dotenv()

app = FastAPI()

# Configure logging
logger = logging.getLogger("app_logger")
logger.setLevel(logging.INFO)

# Create handler
handler = logging.StreamHandler()
handler.setLevel(logging.INFO)

# Create formatter and add it to the handler
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)

# Add the handler to the logger
logger.addHandler(handler)

# Validate environment variables
HF_TOKEN = os.getenv("HF_TOKEN")
if not HF_TOKEN:
    logger.error("HF_TOKEN environment variable is not set.")
    raise RuntimeError("Server configuration error: HF_TOKEN is not set.")

TRANSCRIPTION_BATCH_SIZE = os.getenv("TRANSCRIPTION_BATCH_SIZE", "24")
TRANSCRIPTION_MODEL_NAME = os.getenv("TRANSCRIPTION_MODEL_NAME", "openai/whisper-tiny")
TRANSCRIPTION_MAX_SPEAKERS = os.getenv("TRANSCRIPTION_MAX_SPEAKERS")
TRANSCRIPTION_MIN_SPEAKERS = os.getenv("TRANSCRIPTION_MIN_SPEAKERS")
TASK = os.getenv("TASK", "transcribe")
TRANSCRIPTION_DIARIZATION_MODEL = os.getenv(
    "TRANSCRIPTION_DIARIZATION_MODEL", "pyannote/speaker-diarization-3.1"
)
PORT = os.getenv("PORT", "8080")

@app.post("/transcribe/")
async def transcribe_audio(file: UploadFile = File(...)):
    # Validate file type using python-magic
    file_contents = await file.read()  # Read the file content
    file.file.seek(0)  # Reset file pointer to the beginning

    mime_type = magic.from_buffer(file_contents, mime=True)
    logger.info(f"Detected MIME type: {mime_type}")

    if not mime_type.startswith('audio/'):
        logger.error("Uploaded file is not an audio file.")
        raise HTTPException(status_code=HTTP_400_BAD_REQUEST, detail="Invalid file type.")

    # Create temporary directory
    temp_dir = tempfile.mkdtemp()
    temp_filename = os.path.join(temp_dir, f"temp_{uuid.uuid4()}")

    # Write the file to the temporary directory
    try:
        with open(temp_filename, "wb") as buffer:
            buffer.write(file_contents)

        # Use a unique output path
        output_path = os.path.join(temp_dir, f"output_{uuid.uuid4()}.json")

        # Check for GPU availability
        if torch.cuda.is_available():
            device_id = "0"  # Use GPU 0
        elif hasattr(torch.backends, 'mps') and torch.backends.mps.is_available():
            device_id = "mps"
        else:
            logger.error("No GPU devices available. This application requires a GPU.")
            raise HTTPException(status_code=500, detail="No GPU devices available.")

        logger.info(f"Using device: {device_id}")

        command = [
            "insanely-fast-whisper",
            "--file-name",
            temp_filename,
            "--transcript-path",
            output_path,
            "--model-name",
            TRANSCRIPTION_MODEL_NAME,
            "--task",
            TASK,
            "--batch-size",
            TRANSCRIPTION_BATCH_SIZE,
            "--diarization_model",
            TRANSCRIPTION_DIARIZATION_MODEL,
            "--hf-token",
            HF_TOKEN,
            "--device-id",
            device_id,
        ]

        if TRANSCRIPTION_MAX_SPEAKERS:
            command.extend(["--max-speakers", TRANSCRIPTION_MAX_SPEAKERS])
        if TRANSCRIPTION_MIN_SPEAKERS:
            command.extend(["--min-speakers", TRANSCRIPTION_MIN_SPEAKERS])

        # Run the transcription command asynchronously without 'text' parameter
        process = await asyncio.create_subprocess_exec(
            *command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=temp_dir,
            env=os.environ.copy()
        )
        stdout_bytes, stderr_bytes = await process.communicate()

        # Decode the outputs
        stdout = stdout_bytes.decode('utf-8')
        stderr = stderr_bytes.decode('utf-8')

        if process.returncode != 0:
            logger.error(f"Transcription failed: {stderr}")
            raise HTTPException(status_code=500, detail="Transcription failed.")

        # Read the transcription output
        with open(output_path, "r") as f:
            transcription = json.load(f)

        return JSONResponse(content=transcription)

    except Exception as e:
        logger.exception("An error occurred during transcription.")
        raise HTTPException(status_code=500, detail="An internal error occurred.")

    finally:
        # Clean up temporary files and directories
        try:
            shutil.rmtree(temp_dir)
        except Exception as cleanup_error:
            logger.warning(f"Failed to clean up temporary files: {cleanup_error}")

# Optional: Add a root endpoint for health checks
@app.get("/")
async def read_root():
    return {"message": "Application is running"}