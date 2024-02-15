import logging
__all__ = ['logger', 'logging']

format = "%(asctime)s: %(thread)d: %(levelname)s: %(module)s: %(name)s: %(message)s"
logging.basicConfig(format=format, level=logging.INFO, datefmt="%H:%M:%S")
logger = logging.getLogger(__name__)
