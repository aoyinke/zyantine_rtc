import logging
import os
from datetime import datetime
from typing import Optional, Dict, Any

# 日志级别配置
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()

# 日志目录
LOG_DIR = os.getenv("LOG_DIR", "./logs")

# 确保日志目录存在
os.makedirs(LOG_DIR, exist_ok=True)

# 日志文件名格式
LOG_FILE = f"{LOG_DIR}/zyantine_{datetime.now().strftime('%Y%m%d')}.log"

# 日志格式
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s"

# 控制台日志格式（更简洁）
CONSOLE_FORMAT = "%(asctime)s - %(levelname)s - %(message)s"

# 日期格式
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


class CustomFormatter(logging.Formatter):
    """自定义日志格式化器"""
    
    def format(self, record: logging.LogRecord) -> str:
        # 添加额外的上下文信息
        if hasattr(record, 'session_id'):
            record.msg = f"[Session: {record.session_id}] {record.msg}"
        if hasattr(record, 'client_id'):
            record.msg = f"[Client: {record.client_id}] {record.msg}"
        return super().format(record)


def setup_logger(name: Optional[str] = None, level: Optional[str] = None) -> logging.Logger:
    """设置并返回一个配置好的logger"""
    logger = logging.getLogger(name)
    logger.setLevel(level or LOG_LEVEL)
    
    # 避免重复添加处理器
    if not logger.handlers:
        # 文件处理器
        file_handler = logging.FileHandler(LOG_FILE, encoding="utf-8")
        file_handler.setLevel(logging.DEBUG)  # 文件记录所有级别
        file_formatter = CustomFormatter(LOG_FORMAT, DATE_FORMAT)
        file_handler.setFormatter(file_formatter)
        
        # 控制台处理器
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)  # 控制台只显示INFO及以上
        console_formatter = CustomFormatter(CONSOLE_FORMAT, DATE_FORMAT)
        console_handler.setFormatter(console_formatter)
        
        # 添加处理器
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)
    
    return logger


def get_logger(name: Optional[str] = None) -> logging.Logger:
    """获取一个logger实例"""
    return setup_logger(name)


# 性能日志装饰器
def log_performance(func):
    """记录函数执行性能的装饰器"""
    def wrapper(*args, **kwargs):
        import time
        logger = get_logger(func.__name__)
        start_time = time.time()
        
        try:
            result = func(*args, **kwargs)
            execution_time = (time.time() - start_time) * 1000  # 转换为毫秒
            logger.debug(f"Function {func.__name__} executed in {execution_time:.2f} ms")
            return result
        except Exception as e:
            execution_time = (time.time() - start_time) * 1000
            logger.error(f"Function {func.__name__} failed after {execution_time:.2f} ms: {str(e)}")
            raise
    return wrapper


# 异步性能日志装饰器
async def async_log_performance(func):
    """记录异步函数执行性能的装饰器"""
    async def wrapper(*args, **kwargs):
        import time
        logger = get_logger(func.__name__)
        start_time = time.time()
        
        try:
            result = await func(*args, **kwargs)
            execution_time = (time.time() - start_time) * 1000  # 转换为毫秒
            logger.debug(f"Async function {func.__name__} executed in {execution_time:.2f} ms")
            return result
        except Exception as e:
            execution_time = (time.time() - start_time) * 1000
            logger.error(f"Async function {func.__name__} failed after {execution_time:.2f} ms: {str(e)}")
            raise
    return wrapper


# 上下文管理器，用于记录代码块的执行时间
class PerformanceTimer:
    """性能计时器上下文管理器"""
    
    def __init__(self, name: str, logger: Optional[logging.Logger] = None):
        self.name = name
        self.logger = logger or get_logger("performance")
        self.start_time = None
    
    def __enter__(self):
        self.start_time = datetime.now()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.start_time:
            execution_time = (datetime.now() - self.start_time).total_seconds() * 1000
            if exc_type is None:
                self.logger.debug(f"{self.name} completed in {execution_time:.2f} ms")
            else:
                self.logger.error(f"{self.name} failed after {execution_time:.2f} ms: {str(exc_val)}")


# 创建默认logger实例
default_logger = get_logger()

# 导出常用的日志方法
def debug(msg: str, *args, **kwargs) -> None:
    default_logger.debug(msg, *args, **kwargs)

def info(msg: str, *args, **kwargs) -> None:
    default_logger.info(msg, *args, **kwargs)

def warning(msg: str, *args, **kwargs) -> None:
    default_logger.warning(msg, *args, **kwargs)

def error(msg: str, *args, **kwargs) -> None:
    default_logger.error(msg, *args, **kwargs)

def critical(msg: str, *args, **kwargs) -> None:
    default_logger.critical(msg, *args, **kwargs)

def exception(msg: str, *args, **kwargs) -> None:
    default_logger.exception(msg, *args, **kwargs)
