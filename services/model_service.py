import os
import whisper
import psutil
class ModelService:
    def __init__(self, model_name: str = "small",input_audio=None):
        self.model_name = model_name
        self.model = None
    def model_exists(self):
        return os.path.exists(os.path.join(os.path.expanduser("~"), ".cache", "whisper", self.model_name + ".pt"))
    def load_model(self):
            if not self.model_name:
                raise ValueError("Không có tên model này.")

            if not self.model_exists():
                print(f"Model '{self.model_name}' không tồn tại trên máy. Vui lòng tải về...")
                try:
                    self.model = whisper.load_model(self.model_name)
                except Exception as e:
                    raise RuntimeError(f"Không thể tải model '{self.model_name}'. Lỗi: {e}")
            else:
                print(f"Model '{self.model_name}' đã tồn tại. Đang tải từ local...")
                self.model = whisper.load_model(self.model_name)
    def run_model(self,input_audio):
        print("Đang chạy model...")
        result = self.model.transcribe(input_audio,fp16=False)
        return result
