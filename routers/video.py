from fastapi import APIRouter, HTTPException, UploadFile, WebSocket, WebSocketDisconnect, Depends,status,Request
from sqlalchemy.orm import Session
from services.video_service import TranscriptionService
from database.db import get_db
from dependencies import get_current_user_id 
from loguru import logger
from typing import List
from models.models import TranscriptionHistory
from schemas.video import TranscriptionHistoryItem,GeminiRequest
from fastapi.responses import FileResponse
router = APIRouter()
transcription_service = TranscriptionService(model_name="tiny")
    
@router.post("/transcribe")
async def transcribe_file(file: UploadFile, db: Session = Depends(get_db), user_id: int = Depends(get_current_user_id)):
    segments, text = await TranscriptionService.transcribe_and_save(file, db, user_id=user_id)
    return {"status": "done", "segments": segments, "text": text}

@router.websocket("/ws/transcribe")
async def websocket_transcribe(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_bytes()
            file_path = "temp/chunk_temp.wav"
            with open(file_path, "wb") as f:
                f.write(data)

            for chunk_result in transcription_service.transcribe_streaming(file_path):
                await websocket.send_json({"text": chunk_result})
    except WebSocketDisconnect:
        print("WebSocket connection closed")
@router.get("/transcribe/history")
def get_history(db: Session = Depends(get_db), user_id: int = Depends(get_current_user_id)):
    logger.info(f"Getting history for user_id: {user_id}")
    # Gọi service để lấy dữ liệu
    histories = TranscriptionService.get_user_history(db, user_id)
    logger.info(f"Found {len(histories)} histories")
    logger.info(histories)
    return {"data": histories}

@router.delete("/transcribe/history/{history_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_transcription_history(history_id: int, db: Session = Depends(get_db), user_id: int = Depends(get_current_user_id)):
    print(f"Deleting history_id: {history_id} for user_id: {user_id}")
    # Gọi service để xóa lịch sử
    return TranscriptionService.delete_transcription_history(db=db, history_id=history_id, user_id=user_id)

@router.get("/transcription_histories", response_model=List[TranscriptionHistoryItem])
def get_transcription_histories(
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    """
    Lấy tất cả lịch sử transcription của user hiện tại
    """
    histories = TranscriptionService.get_user_history(db, user_id)
    if not histories:
        raise HTTPException(
            status_code=404,
            detail="No transcription history found for the user"
        )
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
    """
    Route nhận 1 'text' từ client -> gửi lên Gemini -> trả về kết quả.
    """
    try:
        # Gọi service với req.text
        data = await TranscriptionService.generate_gemini_content(req.text)
        
        # Parse response từ Gemini
        if 'candidates' in data and len(data['candidates']) > 0:
            content = data['candidates'][0]['content']
            if 'parts' in content and len(content['parts']) > 0:
                translated_text = content['parts'][0]['text']
                return {"translated_text": translated_text}
            
        raise HTTPException(status_code=500, detail="Invalid response from Gemini")
        
    except Exception as e:
        logger.error(f"Error generating Gemini content: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))