from openai import OpenAI
import os

def convert_audio_to_text(audio_file_path: str,):
    """Transcribe an audio file."""
    # Check if GOOGLE_APPLICATION_CREDENTIALS is set, and set it if not
    credentials = os.getenv('OPENAI_API_KEY')
    if not credentials:
        # Set the environment variable programmatically
        key = "sk-proj-pqNbgxG7jT7GHIj08FRRT3BlbkFJPZB5QqeNAiqYKOoIVLwS"
        os.environ['OPENAI_API_KEY'] = key
        credentials = key

    # Verify if the environment variable is correctly set
    if not os.getenv('OPENAI_API_KEY'):
        print("Nahi Chla Error 2")

    client = OpenAI()

    audio_file= open(audio_file_path, "rb")
    transcription = client.audio.transcriptions.create(
    model="whisper-1", 
    file=audio_file
    )

    print(transcription.text)
    if transcription.text:
        return transcription.text
    else:
        return None
    
if __name__ == "__main__":
    # Save the uploaded audio file
    audio_path = "D:\\Cheeldhar\\Recording.wav"

    # Perform speech-to-text conversion
    try:
        text = convert_audio_to_text(audio_path)
        print({"message": "Audio uploaded successfully", "transcription": text})
    except Exception as e:
        print("Nahi Chla Error 1, ",e)