# logging_config.py
LOGGING_CONFIG = {
    'version': 1,
    'disable_existing_loggers': False, # Retain existing loggers

    'formatters': {
        'simple': {
            'format': '%(levelname)s:%(name)s:%(message)s'
        },
        'standard': {
            'format': '%(asctime)s - %(name)s - %(levelname)s - %(pathname)s:%(lineno)d - %(message)s',
            'datefmt': '%Y-%m-%d %H:%M:%S'
        },
    },

    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'level': 'INFO',
            'formatter': 'simple',
            'stream': 'ext://sys.stdout', # Equivalent to args=(sys.stdout,)
        },
        'file': {
            'class': 'logging.handlers.RotatingFileHandler', # Example: Rotating file handler
            'level': 'DEBUG',
            'formatter': 'standard',
            'filename': 'rotating_app.log',
            'maxBytes': 1048576, # 1 MB
            'backupCount': 5,
            'encoding': 'utf8',
        },
        'error_file': {
            'class': 'logging.FileHandler',
            'level': 'ERROR',
            'formatter': 'standard',
            'filename': 'errors.log',
        },
    },

    'loggers': {
        '': { # This is the root logger
            'handlers': ['console'],
            'level': 'DEBUG',
            'propagate': True,
        },
        'app_module': {
            'handlers': ['console', 'file'],
            'level': 'DEBUG',
            'propagate': False, # Don't send messages to root logger's handlers
        },
        'data_processing': {
            'handlers': ['file', 'error_file'],
            'level': 'INFO',
            'propagate': True, # Propagate to root logger
        },
    },
}
