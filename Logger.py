from os import mkdir
from sys import stdout
from os.path import isdir
from datetime import datetime
from logging import getLogger, DEBUG, Formatter, StreamHandler, FileHandler

DATE_FORMAT = "%Y%m%d-%H%M%S"
LOG_FORMAT = "%(asctime)s [%(levelname)s] %(message)s"


class Logger:
    _logger = None
    _logs_dir = './logs'

    def __init__(self, to_file: bool = False):
        self._logger = getLogger(__name__)
        self._logger.setLevel(level=DEBUG)
        self.__format = Formatter(LOG_FORMAT)

        if to_file:
            if not isdir(self._logs_dir):
                mkdir(self._logs_dir)
            now = datetime.now()
            self.__file_handler = FileHandler(f"{self._logs_dir}/{now.strftime(DATE_FORMAT)}.log")
            self.__file_handler.setFormatter(self.__format)
            self._logger.addHandler(self.__file_handler)
        else:
            self.__stdout_handler = StreamHandler(stdout)
            self.__stdout_handler.setFormatter(self.__format)
            self._logger.addHandler(self.__stdout_handler)

    def get_logger(self):
        return self._logger

    def info(self, msg):
        self._logger.info(msg)

    def error(self, msg):
        self._logger.error(msg)

    def debug(self, msg):
        self._logger.debug(msg)
