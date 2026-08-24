# config.py
import logging
import os
from django.conf import settings


def configurar_logger():
    """
    Configura el logger para la aplicación
    """
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)
    
    # Verificar si hay una configuración de logging existente
    if not logger.handlers:
        # Crear directorio de logs si no existe
        log_dir = os.path.join(settings.BASE_DIR, 'logs')
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)
        
        # Handler para archivo de errores
        file_handler = logging.FileHandler(
            os.path.join(log_dir, 'chatbot_errors.log'),
            encoding='utf-8'
        )
        file_handler.setLevel(logging.ERROR)
        
        # Handler para consola (útil en desarrollo)
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        
        # Formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        # Agregar handlers
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)
    
    return logger


# Logger por defecto para la aplicación
default_logger = configurar_logger()