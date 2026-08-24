# biblioartdis/decorators.py
from django.contrib.auth.decorators import user_passes_test
from django.core.exceptions import PermissionDenied
from django.contrib import messages
from django.shortcuts import redirect
from functools import wraps
import logging

logger = logging.getLogger(__name__)


def is_admin(user):
    """
    Retorna True si el usuario es administrador (campo tipo_usuario del perfil Usuario).
    """
    if not user.is_authenticated:
        return False
    
    try:
        # Verificar si el usuario tiene el atributo 'usuario' (relación OneToOne)
        if not hasattr(user, 'usuario'):
            logger.warning(f"Usuario {user.username} no tiene perfil Usuario asociado")
            return False
        
        # Verificar que el tipo de usuario sea Administrador
        return user.usuario.tipo_usuario == 'Administrador'
        
    except Exception as e:
        logger.error(f"Error verificando admin para usuario {user.username}: {str(e)}")
        return False


def is_active_user(user):
    """
    Verifica si el usuario está activo (no expirado y cuenta activa)
    """
    if not user.is_authenticated:
        return False
    
    try:
        if hasattr(user, 'usuario'):
            from django.utils import timezone
            
            # Verificar si la cuenta ha expirado
            if user.usuario.fecha_baja and user.usuario.fecha_baja < timezone.now():
                logger.info(f"Usuario {user.username} tiene cuenta expirada")
                return False
            
            # Verificar si está activa
            if not user.usuario.esta_activo:
                logger.info(f"Usuario {user.username} tiene cuenta inactiva")
                return False
            
        return True
        
    except Exception as e:
        logger.error(f"Error verificando usuario activo para {user.username}: {str(e)}")
        return True  # Por seguridad, asumir activo si hay error


def is_estudiante(user):
    """
    Retorna True si el usuario es estudiante
    """
    if not user.is_authenticated:
        return False
    
    try:
        if hasattr(user, 'usuario'):
            return user.usuario.tipo_usuario == 'Estudiante'
        return False
    except Exception:
        return False


def is_docente(user):
    """
    Retorna True si el usuario es docente
    """
    if not user.is_authenticated:
        return False
    
    try:
        if hasattr(user, 'usuario'):
            return user.usuario.tipo_usuario == 'Docente'
        return False
    except Exception:
        return False


# ==================== DECORADORES ====================

# Decorador para restringir vistas solo a administradores
admin_required = user_passes_test(is_admin, login_url='inicio')


# Decorador para restringir vistas solo a usuarios activos (no expirados)
def active_user_required(view_func):
    """
    Decorador que verifica que el usuario tenga cuenta activa (no expirada).
    Si la cuenta está expirada, redirige con mensaje de error.
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if request.user.is_authenticated and not is_active_user(request.user):
            messages.error(request, '❌ Tu cuenta ha expirado o está inactiva. Contacta al administrador para renovarla.')
            return redirect('home')
        return view_func(request, *args, **kwargs)
    return wrapper


# Decorador para restringir vistas a administradores activos
def admin_active_required(view_func):
    """
    Decorador que combina admin_required y active_user_required.
    Solo administradores con cuenta activa pueden acceder.
    """
    @wraps(view_func)
    @admin_required
    @active_user_required
    def wrapper(request, *args, **kwargs):
        return view_func(request, *args, **kwargs)
    return wrapper


# Decorador para restringir vistas a estudiantes
def estudiante_required(view_func):
    """
    Decorador que permite acceso solo a estudiantes
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.warning(request, 'Debes iniciar sesión para acceder.')
            return redirect('home')
        
        if not is_estudiante(request.user):
            messages.error(request, '❌ Acceso denegado. Esta sección es solo para estudiantes.')
            return redirect('inicio')
        
        return view_func(request, *args, **kwargs)
    return wrapper


# Decorador para restringir vistas a docentes
def docente_required(view_func):
    """
    Decorador que permite acceso solo a docentes
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.warning(request, 'Debes iniciar sesión para acceder.')
            return redirect('home')
        
        if not is_docente(request.user):
            messages.error(request, '❌ Acceso denegado. Esta sección es solo para docentes.')
            return redirect('inicio')
        
        return view_func(request, *args, **kwargs)
    return wrapper


# Decorador opcional: redirect si ya está autenticado
def redirect_if_authenticated(view_func, redirect_url='inicio'):
    """
    Decorador que redirige a usuarios autenticados a otra página.
    Útil para vistas de login/registro.
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if request.user.is_authenticated:
            messages.info(request, 'Ya has iniciado sesión.')
            return redirect(redirect_url)
        return view_func(request, *args, **kwargs)
    return wrapper


# Decorador para manejar excepciones en vistas
def catch_errors(view_func, redirect_url='inicio', error_message='Ha ocurrido un error. Intenta nuevamente.'):
    """
    Decorador que captura excepciones y redirige con mensaje de error.
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        try:
            return view_func(request, *args, **kwargs)
        except Exception as e:
            logger.error(f"Error en vista {view_func.__name__}: {str(e)}", exc_info=True)
            messages.error(request, f'{error_message} Error: {str(e)}')
            return redirect(redirect_url)
    return wrapper


# ==================== EJEMPLOS DE USO ====================
"""
# Ejemplos de cómo usar los decoradores:

# Vista solo para administradores
@login_required
@admin_required
def panel_admin(request):
    return render(request, 'admin_panel.html')

# Vista solo para administradores con cuenta activa
@login_required
@admin_active_required
def dashboard_admin(request):
    return render(request, 'dashboard.html')

# Vista solo para estudiantes
@login_required
@estudiante_required
def area_estudiante(request):
    return render(request, 'estudiante.html')

# Vista de login que redirige si ya está autenticado
@redirect_if_authenticated(redirect_url='inicio')
def mi_login(request):
    return render(request, 'login.html')

# Vista con manejo de errores
@login_required
@catch_errors(redirect_url='inicio', error_message='Error al procesar la solicitud')
def vista_riesgosa(request):
    # código que podría fallar
    pass
"""