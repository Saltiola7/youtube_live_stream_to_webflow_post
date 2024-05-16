import logging
from functools import wraps

# Create a custom logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)  # Set logger to handle all messages of DEBUG and above
logger.propagate = False  # Prevent the log messages from being propagated to the root logger

# Create handlers: one for file and one for console
file_handler = logging.FileHandler('app.log', mode='a')
file_handler.setLevel(logging.DEBUG)  # File handler handles DEBUG and above

console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)  # Console handler handles INFO and above

# Create formatters and add them to the handlers
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
file_handler.setFormatter(formatter)
console_handler.setFormatter(formatter)

# Add handlers to the logger
logger.addHandler(file_handler)
logger.addHandler(console_handler)

def log_function_call(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        logger.debug(f"Calling function: {func.__name__}")  # Use logger instead of logging
        result = func(*args, **kwargs)
        logger.debug(f"Function {func.__name__} completed")  # Use logger instead of logging
        return result
    return wrapper

def class_log_function_call(cls):
    for name, method in cls.__dict__.items():
        if callable(method):
            setattr(cls, name, log_function_call(method))
    return cls