import os

def create_file(file_path, content=""):
    """Tạo file và thêm nội dung nếu có."""
    with open(file_path, 'w') as f:
        f.write(content)

def create_project_structure():
    """Tạo cấu trúc project theo yêu cầu."""
    structure = {
        "Backend": [
            "app/main.py",
            "app/config.py",
            "app/routers/__init__.py",
            "app/routers/user.py",
            "app/routers/video.py",
            "app/services/__init__.py",
            "app/services/video_service.py",
            "app/services/auth_service.py",
            "app/models/__init__.py",
            "app/models/models.py",
            "app/database/__init__.py",
            "app/database/db.py",
            "tests/__init__.py",
            "tests/test_main.py",
            "requirements.txt",
            "Dockerfile",
            ".env",
            ".gitignore",
        ]
    }

    for root, files in structure.items():
        for file in files:
            # Tạo các thư mục nếu chưa tồn tại
            dir_path = os.path.join(root, os.path.dirname(file))
            os.makedirs(dir_path, exist_ok=True)
            
            # Tạo file rỗng hoặc với nội dung cơ bản
            file_path = os.path.join(root, file)
            if file.endswith("main.py"):
                create_file(file_path, "from fastapi import FastAPI\n\napp = FastAPI()\n\n@app.get('/')\ndef root():\n    return {'message': 'Hello, World!'}\n")
            elif file.endswith("config.py"):
                create_file(file_path, "from pydantic import BaseSettings\n\nclass Settings(BaseSettings):\n    DATABASE_URL: str = 'sqlite:///./db.sqlite3'\n    SECRET_KEY: str = 'your-secret-key'\n    ALGORITHM: str = 'HS256'\n    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30\n\n    class Config:\n        env_file = '.env'\n\nsettings = Settings()\n")
            elif file.endswith("requirements.txt"):
                create_file(file_path, "fastapi\nuvicorn\n")
            elif file.endswith("Dockerfile"):
                create_file(file_path, """FROM python:3.9-slim\n\nWORKDIR /app\nCOPY requirements.txt ./\nRUN pip install --no-cache-dir -r requirements.txt\nCOPY . .\nCMD [\"uvicorn\", \"app.main:app\", \"--host\", \"0.0.0.0\", \"--port\", \"8000\"]\n""")
            else:
                create_file(file_path)

if __name__ == "__main__":
    create_project_structure()
    print("Project structure created successfully!")
