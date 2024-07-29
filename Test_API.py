import os
import io
from fastapi import FastAPI, HTTPException, File, UploadFile
from pydantic import BaseModel, EmailStr
from fastapi.middleware.cors import CORSMiddleware
from google.cloud.speech_v2 import SpeechClient
from google.cloud.speech_v2.types import cloud_speech
from google.api_core.client_options import ClientOptions

app = FastAPI()

# CORS configuration
orig_origins = [
    "http://localhost:3000",  # Frontend application URL
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=orig_origins,
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods, e.g., GET, POST, PUT, DELETE
    allow_headers=["*"],  # Allows all headers
)

# Hardcoded credentials
VALID_EMAIL = "user@example.com"
VALID_PASSWORD = "securepassword"

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

@app.post("/login")
async def login(request: LoginRequest):
    if request.email == VALID_EMAIL and request.password == VALID_PASSWORD:
        return {"message": "Login successful"}
    raise HTTPException(status_code=401, detail="Invalid credentials")

@app.post("/upload-audio")
async def upload_audio(file: UploadFile = File(...)):

    # Save the uploaded audio file
    audio_path = "uploaded_audio.wav"
    with open(audio_path, "wb") as audio_file:
        content = await file.read()
        audio_file.write(content)

    # Perform speech-to-text conversion
    try:
        text = convert_audio_to_text(audio_path)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error during speech-to-text conversion: {str(e)}")

    return {"message": "Audio uploaded successfully", "transcription": text}

def convert_audio_to_text(
    audio_file: str,
    project_id = "planar-method-425304-t6",
    recognizer_id = "test-recognizer",
    region = "us-central1",
) -> cloud_speech.RecognizeResponse:
    """Transcribe an audio file."""
    # Check if GOOGLE_APPLICATION_CREDENTIALS is set, and set it if not
    google_credentials = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
    if not google_credentials:
        # Set the environment variable programmatically
        credentials_path = "D:\\Cheeldhar\\AI-Baniya\\key_STT.json"
        os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = credentials_path
        google_credentials = credentials_path  # Update local variable to reflect change

    # Verify if the environment variable is correctly set
    if not os.getenv('GOOGLE_APPLICATION_CREDENTIALS'):
        print("Nahi Chla Error 2")
    # Instantiates a client
    client = SpeechClient(client_options=ClientOptions(
            api_endpoint=f"{region}-speech.googleapis.com",
        ))

    # Reads a file as bytes
    with open(audio_file, "rb") as f:
        content = f.read()

    request = cloud_speech.RecognizeRequest(
        recognizer=f"projects/{project_id}/locations/{region}/recognizers/{recognizer_id}",
        content=content,
    )

    # Transcribes the audio into text
    response = client.recognize(request=request)

    if response.results:
        transcript = " ".join(result.alternatives[0].transcript for result in response.results)
        return transcript

    else:
        print("Nahi Chla Error 3")
        return None