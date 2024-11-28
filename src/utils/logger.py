# src/utils/logger.py

import logging
import sys
from pathlib import Path

def setup_logger():
    """Configura el logger global de la aplicación"""
    # Crear el logger
    logger = logging.getLogger('EnlaceRural')
    logger.setLevel(logging.DEBUG)

    # Crear handlers
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.DEBUG)

    # Crear el directorio de logs si no existe
    log_dir = Path('logs')
    log_dir.mkdir(exist_ok=True)
    file_handler = logging.FileHandler('logs/app.log')
    file_handler.setLevel(logging.DEBUG)

    # Crear formatters
    console_formatter = logging.Formatter('%(levelname)s - %(name)s - %(message)s')
    file_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s'
    )

    # Asignar formatters a handlers
    console_handler.setFormatter(console_formatter)
    file_handler.setFormatter(file_formatter)

    # Agregar handlers al logger
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)

    return logger

# Crear el logger global
logger = setup_logger()