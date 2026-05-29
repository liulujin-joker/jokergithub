"""Agent log system"""
import logging
import sys
from datetime import datetime
from typing import Optional

class AgentLogger:
    def __init__(self, name: str = "VivoImagingAgent", quiet: bool = False):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.DEBUG)
        self.quiet = quiet
        if not self.logger.handlers:
            handler = logging.StreamHandler(sys.stderr)
            handler.setFormatter(logging.Formatter(
                '[%(asctime)s] [%(levelname)s] %(message)s',
                datefmt='%H:%M:%S'
            ))
            self.logger.addHandler(handler)

    def info(self, msg):
        if not self.quiet:
            self.logger.info(msg)

    def debug(self, msg):
        if not self.quiet:
            self.logger.debug(msg)

    def warning(self, msg):
        if not self.quiet:
            self.logger.warning(msg)

    def error(self, msg):
        if not self.quiet:
            self.logger.error(msg)
