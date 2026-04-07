import sys
import os
from loguru import logger

# Ensure logs directory exists
os.makedirs("logs", exist_ok=True)

# Remove default standard logger
logger.remove()

# Add standard terminal logging with color
logger.add(
    sys.stdout,
    colorize=True,
    format="<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan> - <level>{message}</level>"
)

# Add file logging with rotation (10 MB per file, keeps last 10 days)
logger.add(
    "logs/docurag.log",
    rotation="10 MB",
    retention="10 days",
    level="INFO",
    format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {name}:{function} - {message}"
)
