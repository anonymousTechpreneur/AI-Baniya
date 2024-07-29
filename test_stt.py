#from google.cloud import speech_v1p1beta1 as speech
import os
import io
from google.cloud.speech_v2 import SpeechClient
from google.cloud.speech_v2.types import cloud_speech
from google.api_core.client_options import ClientOptions

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

    for result in response.results:
        print(f"Transcript: {result.alternatives[0].transcript}")
        print(f"Detected Language: {result.language_code}")

    if response.results:
        transcript = " ".join(result.alternatives[0].transcript for result in response.results)
        return transcript

    else:
        print("Nahi Chla Error 3")
        return None

# def convert_audio_to_text(audio_path: str) -> str:
#     # Check if GOOGLE_APPLICATION_CREDENTIALS is set, and set it if not
#     google_credentials = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
#     if not google_credentials:
#         # Set the environment variable programmatically
#         credentials_path = "D:\\Cheeldhar\\key_STT.json"
#         os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = credentials_path
#         google_credentials = credentials_path  # Update local variable to reflect change

#     # Verify if the environment variable is correctly set
#     if not os.getenv('GOOGLE_APPLICATION_CREDENTIALS'):
#         print("Nahi Chla Error 2")

#     client = speech.SpeechClient()
    
#     with io.open(audio_path, "rb") as audio_file:
#         content = audio_file.read()

#     audio = speech.RecognitionAudio(content=content)
#     config = speech.RecognitionConfig(
#         encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
#         sample_rate_hertz=48000,  # Adjust this to match the sample rate of your audio file
#         language_code="en-US",
#     )

#     response = client.recognize(config=config, audio=audio)

#     # Extract and return the transcript
#     if response.results:
#         transcript = " ".join(result.alternatives[0].transcript for result in response.results)
#         return transcript
#     else:
#         print("Nahi Chla Error 3")
#         return None
    
if __name__ == "__main__":
    # Save the uploaded audio file
    audio_path = "D:\\Cheeldhar\\AI-Baniya\\Recording.wav"

    # Perform speech-to-text conversion
    try:
        text = convert_audio_to_text(audio_path)
        print({"message": "Audio uploaded successfully", "transcription": text})
    except Exception as e:
        print("Nahi Chla Error 1, ",e)