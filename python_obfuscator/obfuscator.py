import logging
from .techniques import obfuscate


class obfuscator:
    def __init__(self, logging_level=logging.error):
        pass

    def obfuscate(self, code, remove_techniques=[]):
        return obfuscate(code, remove_techniques)
