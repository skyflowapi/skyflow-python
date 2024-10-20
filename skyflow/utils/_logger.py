import logging
from .enums.log_level import LogLevel


class Logger:
    def __init__(self, level=LogLevel.ERROR):
        self.current_level = level
        self.logger = logging.getLogger('skyflow-python')
        self.logger.propagate = False  # Prevent logs from being handled by parent loggers
        self.set_log_level(level)

        if not self.logger.hasHandlers():
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)

    def set_log_level(self, level):
        self.current_level = level
        log_level_mapping = {
            LogLevel.DEBUG: logging.DEBUG,
            LogLevel.INFO: logging.INFO,
            LogLevel.WARN: logging.WARNING,
            LogLevel.ERROR: logging.ERROR,
            LogLevel.OFF: logging.CRITICAL + 1
        }
        self.logger.setLevel(log_level_mapping[level])

    def debug(self, message):
        if self.current_level.value <= LogLevel.DEBUG.value:
            self.logger.debug(message)

    def info(self, message):
        if self.current_level.value <= LogLevel.INFO.value:
            self.logger.info(message)

    def warn(self, message):
        if self.current_level.value <= LogLevel.WARN.value:
            self.logger.warning(message)

    def error(self, message):
        if self.current_level.value <= LogLevel.ERROR.value:
            self.logger.error(message)