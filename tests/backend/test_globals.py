import logging

from backend.globals import logging_config


class TestLoggingConfiguration:
    def test_setup_logging_adds_file_and_console_handlers(self, tmp_path, monkeypatch):
        monkeypatch.setattr(logging_config, "_LOG_FOLDER", str(tmp_path))
        monkeypatch.setattr(logging_config, "_LOG_FILE", str(tmp_path / "midas.log"))
        root_logger = logging.getLogger()
        previous_handlers = root_logger.handlers[:]
        previous_level = root_logger.level
        root_logger.handlers.clear()
        try:
            logging_config.setup_logging()

            assert len(root_logger.handlers) == 2
            assert (tmp_path / "midas.log").exists()
        finally:
            for handler in root_logger.handlers[:]:
                handler.close()
            root_logger.handlers.clear()
            root_logger.handlers.extend(previous_handlers)
            root_logger.setLevel(previous_level)
