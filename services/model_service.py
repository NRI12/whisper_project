import os
import whisper
import psutil
class ModelService:
    def __init__(self, model_name: str = "tiny",input_audio=None):
        self.model_name = model_name
        self.model = None
    def model_exists(self):
        return os.path.exists(os.path.join(os.path.expanduser("~"), ".cache", "whisper", self.model_name + ".pt"))
    def load_model(self):
            """
            Tải model Whisper nếu đủ tài nguyên hoặc đã tồn tại, đồng thời kiểm tra thông tin RAM.
            """
            if not self.model_name:
                raise ValueError("Model name is not provided.")

            if not self.model_exists():
                print(f"Model '{self.model_name}' không tồn tại trên máy. Vui lòng tải về...")
                try:
                    self.model = whisper.load_model(self.model_name)
                except Exception as e:
                    raise RuntimeError(f"Không thể tải model '{self.model_name}'. Lỗi: {e}")
            else:
                print(f"Model '{self.model_name}' đã tồn tại. Đang tải từ local...")
                self.model = whisper.load_model(self.model_name)
    def check_ram_and_use_model(self,input_audio):
        ram_avaible = psutil.virtual_memory().available / (1024 ** 3)  
        required_ram = self.get_required_ram()

        if ram_avaible < required_ram:
            raise MemoryError(f"Không đủ RAM để chạy model. RAM cần thiết: {required_ram} GB, RAM có sẵn: {ram_avaible} GB")
        
        try:
            print("Đang chạy model...")
            result = self.model.transcribe(input_audio,fp16=False)
            return result
        except Exception as e:
            raise RuntimeError(f"Lỗi khi chạy model: {e}")
    def get_required_ram(self):
        model_ram_mapping = {
            "tiny": 1.5,
            "base": 2.0,
            "small": 3.0,
            "medium": 5.0,
            "large": 10.0,
        }
        return model_ram_mapping.get(self.model_name, 2)