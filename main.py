from fastapi import FastAPI, Request
from routers import user, video
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os
from fastapi.templating import Jinja2Templates
import warnings
warnings.filterwarnings("ignore", category=FutureWarning)
import uvicorn
app = FastAPI()

uploads_directory = os.path.join(os.path.dirname(__file__), "uploads")
app.mount("/uploads", StaticFiles(directory=uploads_directory), name="uploads")

static_directory = os.path.join(os.path.dirname(__file__), "static")
app.mount("/static", StaticFiles(directory=static_directory), name="static")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Cho phép tất cả domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(user.router)
app.include_router(video.router)

templates = Jinja2Templates(directory="templates")

@app.get("/")
def root(request: Request):
    return templates.TemplateResponse("authentication.html", {"request": request})

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
