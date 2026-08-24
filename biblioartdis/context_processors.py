# context_processors.py
from .models import Usuario
import logging

logger = logging.getLogger(__name__)

def user_info(request):
    """
    Context processor para añadir información del usuario a todas las plantillas.
    Disponible en templates como {{ usuario }}
    """
    usuario = None
    if request.user.is_authenticated:
        try:
            # CORRECCIÓN: Usar user directamente, no correo___
            # El perfil Usuario está relacionado por OneToOneField con User
            usuario = request.user.usuario  # Más eficiente que buscar por correo
        except Usuario.DoesNotExist:
            logger.warning(f"Usuario autenticado {request.user.username} no tiene perfil Usuario")
        except AttributeError:
            # Si no tiene el atributo 'usuario' (relación OneToOne no existe)
            logger.warning(f"Usuario {request.user.username} no tiene relación con Usuario")
    
    return {'usuario': usuario}