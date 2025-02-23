import os
import uuid
from pathlib import Path
from fastapi import UploadFile
from sqlalchemy.orm import Session
from loguru import logger
from config import settings

class TranscriptionService:
    # ... (other methods remain the same)

    @staticmethod
    def save_video(file: UploadFile, db: Session, user_id: int):
        """
        Lưu file video với tên ngẫu nhiên và lưu thông tin tương ứng vào database
        """
        # Tạo tên file ngẫu nhiên với uuid
        original_extension = Path(file.filename).suffix
        random_filename = f"{uuid.uuid4()}{original_extension}"
        
        # Tạo thư mục lưu trữ nếu chưa tồn tại
        upload_dir = os.path.join(os.getcwd(), "uploads", "videos")
        os.makedirs(upload_dir, exist_ok=True)
        logger.info(f"Uploading video to {upload_dir}")
        
        # Lưu file video với tên ngẫu nhiên
        file_path = os.path.join(upload_dir, random_filename)
        with open(file_path, "wb") as f:
            f.write(file.file.read())
        logger.info(f"Video saved as {random_filename}")

        # Tạo đường dẫn tương đối và URL đầy đủ
        relative_path = f"uploads/videos/{random_filename}"
        video_url = f"{settings.BASE_URL}/{relative_path}"
        
        # Lưu thông tin video vào database với cả tên gốc và tên ngẫu nhiên
        new_video = TranscriptionHistory(
            user_id=user_id,
            video_name=file.filename,  # Tên gốc của file
            random_name=random_filename,  # Tên ngẫu nhiên đã tạo
            video_path=video_url,  # URL đầy đủ
        )
        db.add(new_video)
        db.commit()
        db.refresh(new_video)

        return {
            "id": new_video.id,
            "original_name": new_video.video_name,
            "random_name": new_video.random_name,
            "url": new_video.video_path,
        }