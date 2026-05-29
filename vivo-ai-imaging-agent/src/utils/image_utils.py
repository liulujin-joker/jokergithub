"""图像处理工具函数"""
import base64
from typing import Optional, Tuple
from pathlib import Path


class ImageProcessor:
    @staticmethod
    def load_as_base64(image_path: str) -> Optional[str]:
        """加载图片并转为base64"""
        path = Path(image_path)
        if not path.exists():
            return None
        with open(path, 'rb') as f:
            return base64.b64encode(f.read()).decode('utf-8')

    @staticmethod
    def save_base64(base64_str: str, output_path: str) -> bool:
        """保存base64图片到文件"""
        try:
            data = base64.b64decode(base64_str)
            with open(output_path, 'wb') as f:
                f.write(data)
            return True
        except Exception:
            return False
