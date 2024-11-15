"""
Module for define config used by app
"""

import os
import logging
import sys


FASTAPI_CONFIG = {
    "port": 8081,
}

MONGODB_URL = os.environ["MONGODB_URL"]
MONGODB_DB = "college"
MONGODB_COLLECTION = "students"

LOG_CONFIG = {
    'name': 'fast-api-webapp',
    'level': logging.DEBUG,
    'stream_handler': logging.StreamHandler(sys.stdout),
    'format': '[%(asctime)s] [%(process)s] [%(levelname)s] %(message)s',
    'date_fmt': '%Y-%m-%d %H:%M:%S %z',
}

JAEGER_CONFIG = {
    'host': os.environ["JAEGER_EXPORTER_HOST"],
    'port': int(os.environ["JAEGER_EXPORTER_PORT"])
}
