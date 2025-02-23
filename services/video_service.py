import os
import whisper
from typing import Generator,List
from sqlalchemy.orm import Session
from fastapi import HTTPException, UploadFile,status
from models.models import TranscriptionHistory
from utils.video_utils import split_audio
from schemas.video import TranscriptionHistoryItem
from config import settings
from loguru import logger
from pathlib import Path
import uuid
from services.model_service import ModelService
from moviepy.video.io.VideoFileClip import VideoFileClip
import httpx
class TranscriptionService: 
    def __init__(self, model_name: str = None):
        self.model = whisper.load_model(model_name) if model_name else None
        
    def transcribe_file(self, file_path: str) -> dict:
        service = ModelService()
        try:
            service.load_model()
            result = service.check_ram_and_use_model(file_path)
            return {
                "text": result["text"],
                "segments": result["segments"],
            }   
        except Exception as e:
            print("Lỗi:", e)

    def transcribe_streaming(self, file_path: str, chunk_duration: int = 30) -> Generator[dict, None, None]:
        chunks = split_audio(file_path, chunk_duration)
        for chunk in chunks:
            result = self.model.transcribe(chunk)
            yield {
                "text": result["text"],
                "start": result["segments"][0]["start"] if result["segments"] else 0,
                "end": result["segments"][-1]["end"] if result["segments"] else 0,
                "segments": result["segments"]
            }
    @classmethod
    async def transcribe_and_save(cls, file: UploadFile, db: Session, user_id: int):
        # Tạo bản ghi với trạng thái processing = True
        transcription = TranscriptionHistory(
            user_id=user_id,
            video_name=file.filename,
            processing=True,
            file_path="",
            file_size=0
        )
        db.add(transcription)
        db.commit()
        db.refresh(transcription)

        try:
            # Xử lý file và transcribe
            original_extension = Path(file.filename).suffix
            random_filename = f"{uuid.uuid4()}{original_extension}"
            upload_dir = os.path.join(os.getcwd(), "uploads", "videos")
            os.makedirs(upload_dir, exist_ok=True)
            
            file_path = os.path.join(upload_dir, random_filename)
            with open(file_path, "wb") as f:
                f.write(file.file.read())

            # Tính các thông số
            file_size = os.path.getsize(file_path) / (1024 * 1024)
            video = VideoFileClip(file_path)
            video_duration = video.duration
            video.close()

            # Thực hiện transcribe
            service = cls()
            result = service.transcribe_file(file_path)

            # Cập nhật bản ghi với kết quả
            transcription.file_path = file_path
            transcription.file_size = file_size
            transcription.video_duration = video_duration
            transcription.text = result["text"]
            transcription.processing = False
            db.commit()

            return result["segments"], result["text"]

        except Exception as e:
            # Xóa bản ghi nếu có lỗi
            db.delete(transcription)
            db.commit()
            raise e
    @staticmethod
    def get_user_history(db: Session, user_id: int) -> List[TranscriptionHistoryItem]:
        histories = db.query(TranscriptionHistory).filter(TranscriptionHistory.user_id == user_id).all()
        return [TranscriptionHistoryItem.from_orm(h) for h in histories]
    
    @staticmethod
    def delete_transcription_history(db: Session, history_id: int, user_id: int):
        # Tìm bản ghi lịch sử
        history = db.query(TranscriptionHistory).filter(
            TranscriptionHistory.id == history_id,
            TranscriptionHistory.user_id == user_id
        ).first()

        if history:
            if os.path.exists(history.file_path):
                os.remove(history.file_path)
        if not history:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Transcription history not found or access denied"
            )

        # Xóa bản ghi  
        db.delete(history)
        db.commit()
        return {"message": "Transcription history deleted successfully"}
    @staticmethod
    async def generate_gemini_content(prompt_text: str) -> dict:
        try:
            gemini_api_key = settings.GEMINI_API_KEY
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={gemini_api_key}"
            
            headers = {
                "Content-Type": "application/json"
            }
            
            payload = {
                "contents": [{
                    "parts": [{
                        "text": prompt_text
                    }]
                }]
            }
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(url, headers=headers, json=payload)
                response.raise_for_status()
                
                data = response.json()
                
                # Log response để debug
                logger.debug(f"Gemini API response: {data}")
                
                return data
                
        except httpx.HTTPError as e:
            logger.error(f"HTTP error occurred: {e.response.text if hasattr(e, 'response') else str(e)}")
            raise
        except Exception as e:
            logger.error(f"Gemini API call failed: {str(e)}")
            raise