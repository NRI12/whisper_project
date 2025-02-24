from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect, Depends,status,Request
from fastapi import UploadFile
from sqlalchemy.orm import Session
from services.video_service import TranscriptionService
from database.db import get_db
from dependencies import get_current_user_id 
from loguru import logger
from typing import List,Union
from models.models import TranscriptionHistory
from schemas.video import TranscriptionHistoryItem,GeminiRequest,VideoRequest
from fastapi.responses import FileResponse
router = APIRouter()
transcription_service = TranscriptionService(model_name="tiny")
    
@router.post("/transcribe")
async def transcribe_file(file: Union[UploadFile,str], db: Session = Depends(get_db), user_id: int = Depends(get_current_user_id)):
    segments, text = await TranscriptionService.transcribe_and_save(file, db, user_id=user_id)
    return {"status": "done", "segments": segments, "text": text}
@router.delete("/transcribe/history/{history_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_transcription_history(history_id: int, db: Session = Depends(get_db), user_id: int = Depends(get_current_user_id)):
    print(f"Deleting history_id: {history_id} for user_id: {user_id}")
    # Gọi service để xóa lịch sử
    return TranscriptionService.delete_transcription_history(db=db, history_id=history_id, user_id=user_id)
@router.get("/transcription_histories", response_model=List[TranscriptionHistoryItem])
def get_transcription_histories(
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id),):
    histories = TranscriptionService.get_user_history(db, user_id)
    return histories
@router.get("/video/{video_id}")
async def get_video(video_id: str, db: Session = Depends(get_db), user_id: int = Depends(get_current_user_id)):
    video = db.query(TranscriptionHistory).filter(  # Dùng TranscriptionHistory model
        TranscriptionHistory.id == video_id,
        TranscriptionHistory.user_id == user_id
    ).first()
   
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")
       
    return FileResponse(
        video.file_path,
        media_type="video/mp4",
        filename=video.video_name
    )
@router.delete("/transcribe/history/{history_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_transcription_history(
    history_id: int, 
    db: Session = Depends(get_db), 
    user_id: int = Depends(get_current_user_id)
):
    # Find the history entry
    history = db.query(TranscriptionHistory).filter(
        TranscriptionHistory.id == history_id,
        TranscriptionHistory.user_id == user_id
    ).first()
    
    if not history:
        raise HTTPException(status_code=404, detail="History not found")
    
    try:
        # Delete the video file if it exists
        if history.file_path and os.path.exists(history.file_path):
            os.remove(history.file_path)
            
        # Delete from database
        db.delete(history)
        db.commit()
        
        return Response(status_code=status.HTTP_204_NO_CONTENT)
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Error deleting transcription history: {str(e)}"
        )
@router.get("/transcribe/history/{history_id}")
async def get_transcription_history(
    history_id: int,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id)
):
    history = db.query(TranscriptionHistory).filter(
        TranscriptionHistory.id == history_id,
        TranscriptionHistory.user_id == user_id
    ).first()
    
    if not history:
        raise HTTPException(status_code=404, detail="History not found")
    
    return {
        "id": history.id,
        "text": history.text,           
        "video_duration": history.video_duration  
    }
@router.post("/generate_gemini_content")
async def generate_gemini_content(req: GeminiRequest):
    try:
        # Tạo prompt yêu cầu Gemini dịch
        prompt = f"""Translate the following text into {req.language}.
        ONLY return the translated text, no explanation, no commentary, no additional analysis.

        Text to translate:
        {req.text}"""

        # Gọi Gemini API
        data = await TranscriptionService.generate_gemini_content(prompt)

        # Parse response từ Gemini
        if "candidates" in data and data["candidates"]:
            content = data["candidates"][0].get("content", {})
            if "parts" in content and content["parts"]:
                translated_text = content["parts"][0].get("text", "")
                return {"translated_text": translated_text}
        
        raise HTTPException(status_code=500, detail="Invalid response format from Gemini")
    
    except Exception as e:
        logger.error(f"Error generating Gemini content: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
@router.post("/transcribe_and_download")
async def transcribe_file(
    request: VideoRequest, 
    db: Session = Depends(get_db), 
    user_id: int = Depends(get_current_user_id)
):
    print(f"User ID: {user_id}")  # Debug xem user_id có nhận đúng không
    if not user_id:
        raise HTTPException(status_code=401, detail="Unauthorized")

    # Lấy URL từ request JSON
    video_url = request.url
    video_path = await TranscriptionService.download_video(video_url)
    print(video_path)
    # Gọi hàm async với await
    await TranscriptionService.transcribe_and_save(video_path, db, user_id=user_id)

    return {"status": "done"}
