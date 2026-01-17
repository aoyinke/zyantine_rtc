import traceback
from typing import Dict, Any, Optional, Callable, TypeVar, Awaitable
from functools import wraps
from logger import get_logger

logger = get_logger(__name__)

# 类型变量，用于装饰器
t = TypeVar('t')


class ZyantineError(Exception):
    """Zyantine系统基础异常类"""
    def __init__(self, message: str, code: int = 500, details: Optional[Dict[str, Any]] = None):
        self.message = message
        self.code = code
        self.details = details or {}
        super().__init__(self.message)


class ConfigError(ZyantineError):
    """配置错误"""
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, 400, details)


class AudioError(ZyantineError):
    """音频处理错误"""
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, 415, details)


class STTError(ZyantineError):
    """语音识别错误"""
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, 502, details)


class TTSError(ZyantineError):
    """语音合成错误"""
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, 502, details)


class AIError(ZyantineError):
    """AI服务错误"""
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, 503, details)


class NetworkError(ZyantineError):
    """网络错误"""
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, 504, details)


def error_handler(func: Callable[..., t]) -> Callable[..., t]:
    """同步函数异常处理装饰器"""
    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> t:
        try:
            return func(*args, **kwargs)
        except ZyantineError as e:
            logger.error(f"ZyantineError: {e.message} (code: {e.code})")
            if e.details:
                logger.error(f"Error details: {e.details}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error: {str(e)}")
            logger.error(traceback.format_exc())
            raise ZyantineError(f"Internal server error: {str(e)}") from e
    return wrapper


def async_error_handler(func: Callable[..., Awaitable[t]]) -> Callable[..., Awaitable[t]]:
    """异步函数异常处理装饰器，支持普通异步函数和异步生成器函数"""
    
    # 检查函数是否是异步生成器函数
    # 这里我们通过检查函数定义是否包含yield来判断
    import inspect
    source = inspect.getsource(func)
    is_generator = 'yield' in source
    
    if is_generator:
        # 处理异步生成器函数
        @wraps(func)
        async def generator_wrapper(*args: Any, **kwargs: Any) -> t:
            try:
                async for item in func(*args, **kwargs):
                    yield item
            except ZyantineError as e:
                logger.error(f"ZyantineError: {e.message} (code: {e.code})")
                if e.details:
                    logger.error(f"Error details: {e.details}")
                raise
            except Exception as e:
                logger.error(f"Unexpected error: {str(e)}")
                logger.error(traceback.format_exc())
                raise ZyantineError(f"Internal server error: {str(e)}") from e
        return generator_wrapper
    else:
        # 处理普通异步函数
        @wraps(func)
        async def regular_wrapper(*args: Any, **kwargs: Any) -> t:
            try:
                return await func(*args, **kwargs)
            except ZyantineError as e:
                logger.error(f"ZyantineError: {e.message} (code: {e.code})")
                if e.details:
                    logger.error(f"Error details: {e.details}")
                raise
            except Exception as e:
                logger.error(f"Unexpected error: {str(e)}")
                logger.error(traceback.format_exc())
                raise ZyantineError(f"Internal server error: {str(e)}") from e
        return regular_wrapper


def format_error_response(error: Exception) -> Dict[str, Any]:
    """格式化错误响应"""
    if isinstance(error, ZyantineError):
        return {
            "error": {
                "code": error.code,
                "message": error.message,
                "details": error.details
            }
        }
    else:
        return {
            "error": {
                "code": 500,
                "message": f"Internal server error: {str(error)}",
                "details": {}
            }
        }


def handle_exception(exception: Exception) -> None:
    """处理未捕获的异常"""
    logger.critical(f"Uncaught exception: {str(exception)}")
    logger.critical(traceback.format_exc())


def setup_global_exception_handler() -> None:
    """设置全局异常处理"""
    import sys
    def excepthook(exc_type, exc_value, exc_traceback):
        if issubclass(exc_type, KeyboardInterrupt):
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
            return
        handle_exception(exc_value)
    sys.excepthook = excepthook


# 立即设置全局异常处理
setup_global_exception_handler()
