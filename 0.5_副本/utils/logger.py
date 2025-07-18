import logging
from logging.handlers import TimedRotatingFileHandler
import os
from pathlib import Path
from datetime import datetime

# 创建日志目录
LOG_DIR = "logs"
os.makedirs(LOG_DIR, exist_ok=True)

# 日志格式
LOG_FORMAT = "%(asctime)s | %(levelname)s | %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

def setup_logger(name: str):
    """配置并返回一个日志记录器"""
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    
    # 按日滚动的文件处理器
    log_file = Path(LOG_DIR) / "app.log"
    file_handler = TimedRotatingFileHandler(
        log_file,
        when="midnight",
        interval=1,
        backupCount=7,
        encoding="utf-8"
    )
    file_handler.setFormatter(logging.Formatter(LOG_FORMAT, DATE_FORMAT))
    
    # 控制台处理器
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(logging.Formatter(LOG_FORMAT, DATE_FORMAT))
    
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger

# 应用日志记录器
app_logger = setup_logger("app")

def log_event(event_type: str, ip: str = None, **kwargs):
    """记录事件日志"""
    log_data = {
        "event": event_type,
        "ip": ip,
        **kwargs
    }
    app_logger.info(log_data)