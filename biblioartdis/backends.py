# backends.py
from django.contrib.auth.backends import BaseBackend
from django.contrib.auth.models import User
from django.db import IntegrityError
import logging

logger = logging.getLogger(__name__)


class CIAuthBackend(BaseBackend):
    """
    Backend de autenticación por CI (Carnet de Identidad)
    NOTA: Este backend no se está usando actualmente porque el login es por código de verificación
    """
    
    def authenticate(self, request, username=None, password=None, **kwargs):
        """
        Autentica al usuario usando CI como username y CI como password
        """
        if not username or not password:
            return None
            
        try:
            # Buscar usuario por CI
            usuario = Usuario.objects.get(ci=username)
            
            # Verificar que el password coincide con el CI
            if usuario.ci == password:
                # Verificar que el usuario tiene cuenta de Django
                if usuario.user:
                    user = usuario.user
                    
                    # Verificar que la cuenta está activa
                    if user.is_active and usuario.esta_activo:
                        logger.info(f"Usuario autenticado por CI: {usuario.correo}")
                        return user
                    else:
                        logger.warning(f"Intento de login con cuenta inactiva: {usuario.correo}")
                        return None
                else:
                    # Crear usuario de Django si no existe
                    try:
                        from datetime import timedelta
                        from django.utils import timezone
                        
                        user, created = User.objects.get_or_create(
                            email=usuario.correo,
                            defaults={
                                'username': usuario.correo,
                                'first_name': usuario.nombres,
                            }
                        )
                        
                        if created:
                            user.set_unusable_password()  # Sin contraseña porque usamos 2FA
                            user.save()
                            usuario.user = user
                            usuario.save()
                            logger.info(f"Usuario Django creado para: {usuario.correo}")
                        
                        return user
                    except IntegrityError as e:
                        logger.error(f"Error creando usuario Django: {e}")
                        return None
                        
        except Usuario.DoesNotExist:
            logger.warning(f"Intento de login con CI no registrado: {username}")
            return None
        except Exception as e:
            logger.error(f"Error en CIAuthBackend: {str(e)}")
            return None

    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None