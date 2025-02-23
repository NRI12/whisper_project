import whisper

# Load the Whisper model
model = whisper.load_model("base")

# Transcribe an example audio file
result = model.transcribe(r"C:\Users\pc\Videos\aaa.mp4")

# Print the transcription
print(result["text"])