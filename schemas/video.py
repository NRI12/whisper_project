from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime

class SubtitleSegment(BaseModel):
    start: float
    end: float
    text: str

    class Config:
        from_attributes = True

class TranscriptionHistoryItem(BaseModel):
    id: int
    video_name: str
    file_path: str
    file_size: float
    video_duration: Optional[float] = None
    created_at: datetime
    subtitles: Optional[List] = None
    user_id: Optional[int] = None
    class Config:
        from_attributes = True
class GeminiRequest(BaseModel):
    text: str