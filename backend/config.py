# backend/config.py
import os

# 项目根目录
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# 临时文件上传目录
TEMP_UPLOAD_DIR = os.path.join(BASE_DIR, "temp_uploads")

# 确保启动时目录存在
os.makedirs(TEMP_UPLOAD_DIR, exist_ok=True)