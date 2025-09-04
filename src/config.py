import os, logging
from logging.handlers import RotatingFileHandler
from dotenv import load_dotenv
from pathlib import Path


load_dotenv()
LOG_PATH = os.getenv("LOG_PATH")
Path(LOG_PATH).parent.mkdir(parents=True, exist_ok=True)
GIGACHAT_CLIENT_ID = os.getenv("GIGACHAT_CLIENT_ID")
GIGACHAT_CLIENT_SECRET = os.getenv("GIGACHAT_CLIENT_SECRET")
API_ID=os.getenv("API_ID")
API_HASH=os.getenv("API_HASH")
PHONE=os.getenv("PHONE")
GROUP_ID=os.getenv("GROUP_ID")

def setup_logger() -> logging.Logger:
    logger = logging.getLogger("chat_processor")
    logger.setLevel(logging.INFO)

    if not logger.handlers:
        # Формат логов: timestamp, level, module, message
        log_format = logging.Formatter(
            "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )

        # Обработчик файлов с ротацией (макс. 10 МБ, сохранение 5 резервных копий)
        file_handler = RotatingFileHandler(
            LOG_PATH,
            maxBytes=10 * 1024 * 1024,
            backupCount=5
        )
        file_handler.setFormatter(log_format)
        logger.addHandler(file_handler)

        console_handler = logging.StreamHandler()
        console_handler.setFormatter(log_format)
        logger.addHandler(console_handler)

    return logger


logger = setup_logger()