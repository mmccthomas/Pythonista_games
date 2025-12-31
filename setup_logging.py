import logging
logging.basicConfig(
    level=logging.INFO, 
    format='[%(levelname)s]: %(message)s'
    )
logger = logging.getLogger(__name__)
#logger.setLevel(logging.DEBUG) # Set root logger level to DEBUG

def is_debug_level():
    return logging.getLevelName(logger.getEffectiveLevel()) == 'DEBUG'
