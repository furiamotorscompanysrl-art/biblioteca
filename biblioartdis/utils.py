# biblioartdis/utils.py

from django.db import connection
from .models import Libro, Revista, Imagen
import logging

logger = logging.getLogger(__name__)

def get_system_status():
    """
    Obtiene el estado del sistema: cantidad de archivos y espacio usado
    """
    try:
        # Contar archivos
        total_libros = Libro.objects.count()
        total_revistas = Revista.objects.count()
        total_imagenes = Imagen.objects.count()
        
        # Calcular espacio (aproximado desde Cloudinary o base de datos)
        # Esto es un placeholder - ajusta según cómo manejes tus archivos
        espacio_total = {
            'pdfs': 0,
            'imagenes': 0,
            'portadas': 0,
            'total': 0
        }
        
        archivos_totales = {
            'pdfs': total_libros + total_revistas,
            'imagenes': total_imagenes,
            'portadas': total_libros + total_revistas + total_imagenes
        }
        
        return {
            'totales': {
                'archivos_totales': archivos_totales,
                'espacio_total': espacio_total
            },
            'libros': {
                'total': total_libros,
                'archivos': {
                    'pdfs': total_libros,
                    'portadas': total_libros
                },
                'espacio': {
                    'pdfs': 0,
                    'portadas': 0
                }
            },
            'revistas': {
                'total': total_revistas,
                'archivos': {
                    'pdfs': total_revistas,
                    'portadas': total_revistas
                },
                'espacio': {
                    'pdfs': 0,
                    'portadas': 0
                }
            },
            'imagenes': {
                'total': total_imagenes,
                'archivos': {
                    'imagenes': total_imagenes,
                    'pdfs': 0
                },
                'espacio': {
                    'imagenes': 0,
                    'pdfs': 0
                }
            }
        }
    except Exception as e:
        logger.error(f"Error obteniendo estado del sistema: {e}")
        return {
            'totales': {
                'archivos_totales': {'pdfs': 0, 'imagenes': 0, 'portadas': 0},
                'espacio_total': {'pdfs': 0, 'imagenes': 0, 'portadas': 0, 'total': 0}
            },
            'libros': {'total': 0, 'archivos': {'pdfs': 0, 'portadas': 0}, 'espacio': {'pdfs': 0, 'portadas': 0}},
            'revistas': {'total': 0, 'archivos': {'pdfs': 0, 'portadas': 0}, 'espacio': {'pdfs': 0, 'portadas': 0}},
            'imagenes': {'total': 0, 'archivos': {'imagenes': 0, 'pdfs': 0}, 'espacio': {'imagenes': 0, 'pdfs': 0}}
        }