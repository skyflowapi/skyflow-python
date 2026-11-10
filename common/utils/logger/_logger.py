import logging
from ..enums.log_level import LogLevel

LOGGER_NAME = 'skyflow-python'
LOG_MESSAGE_FORMAT = '%(message)s'
_SKYFLOW_HANDLER_FLAG = '_skyflow_handler'


class Logger:
    def __init__(self, level=LogLevel.ERROR):
        self.current_level = level
        self.logger = logging.getLogger(LOGGER_NAME)
        self.logger.propagate = False

        if not any(getattr(handler, _SKYFLOW_HANDLER_FLAG, False) for handler in self.logger.handlers):
            self.logger.handlers.clear()
            handler = logging.StreamHandler()
            handler.setFormatter(logging.Formatter(LOG_MESSAGE_FORMAT))
            setattr(handler, _SKYFLOW_HANDLER_FLAG, True)
            self.logger.addHandler(handler)

        self.set_log_level(level)

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
