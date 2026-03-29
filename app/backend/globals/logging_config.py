import os
import logging

_PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
_LOG_FOLDER = os.path.join(_PROJECT_ROOT, '.logs')
_LOG_FILE = os.path.join(_LOG_FOLDER, 'midas.log')

_LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'


def setup_logging():
    """Configure application-wide logging to file and console."""
    os.makedirs(_LOG_FOLDER, exist_ok=True)

    file_handler = logging.FileHandler(_LOG_FILE, mode='w', encoding='utf-8')
    file_handler.setLevel(logging.DEBUG)

    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)

    formatter = logging.Formatter(_LOG_FORMAT)
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)

    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)
