import os
from pydub import AudioSegment
from fastapi import UploadFile
UPLOAD_DIR = "uploads/videos"

def split_audio(file_path, chunk_duration=30):
    """
    Chia nhỏ file audio thành các chunk.
    Args:
        file_path (str): Đường dẫn đến file audio.
        chunk_duration (int): Thời gian của mỗi chunk (giây).
    Returns:
        List[str]: Danh sách đường dẫn đến các file chunk.
    """
    audio = AudioSegment.from_file(file_path)
    duration_ms = len(audio)
    chunks = []

    for i in range(0, duration_ms, chunk_duration * 1000):
        chunk = audio[i:i + chunk_duration * 1000]
        chunk_path = os.path.join(os.getcwd(), f"temp/chunk_{i // 1000}.wav")
        chunk.export(chunk_path, format="wav")
        chunks.append(chunk_path)

    return chunks
def save_uploaded_file(file: UploadFile):
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    file_path = os.path.join(UPLOAD_DIR, file.filename)
    
    with open(file_path, "wb") as f:
        f.write(file.file.read())
    
    return file_path  # Trả về đường dẫn đầy đủ
