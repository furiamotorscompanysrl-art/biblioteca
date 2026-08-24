# views/auth_views.py
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth import update_session_auth_hash
from django.views.decorators.http import require_http_methods
from django.http import JsonResponse, HttpResponse
from django.contrib.auth.views import LoginView
from django.contrib.auth.models import User
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from django.utils import timezone
import json
import logging
import re
import threading

from ..decorators import admin_required
from ..email_utils import enviar_codigo_verificacion, verificar_codigo

logger = logging.getLogger(__name__)

# Diccionario temporal para almacenar intentos de login
intentos_fallidos = {}


def enviar_codigo_async(user):
    """
    Envía el código de verificación en un hilo separado para no bloquear la respuesta
    """
    def send_thread():
        try:
            enviar_codigo_verificacion(user)
            logger.info(f"Código enviado asíncronamente a {user.email}")
        except Exception as e:
            logger.error(f"Error enviando código asíncrono a {user.email}: {str(e)}")
    
    thread = threading.Thread(target=send_thread)
    thread.daemon = True
    thread.start()
    return thread


def crear_usuario_si_no_existe(email, correo_especial='vc3070934@gmail.com'):
    """
    Crea un usuario automáticamente si no existe.
    Usa get_or_create para evitar duplicados.
    RESPETA el rol existente - NO lo sobrescribe.
    Retorna (user, created, error_message)
    """
    try:
        # Generar username temporal único basado en el email
        username_base = re.sub(r'[^a-zA-Z0-9_]', '', email.split('@')[0])
        if not username_base:
            username_base = f"user_{email.split('@')[0]}"
        
        final_username = username_base
        counter = 1
        while User.objects.filter(username=final_username).exists():
            final_username = f"{username_base}{counter}"
            counter += 1
        
        # Buscar si el usuario ya existe por email
        user = User.objects.filter(email=email).first()
        created = False
        
        if not user:
            # Crear usuario con username válido
            user = User.objects.create_user(
                username=final_username,
                email=email,
                password='unusable_password_temp'
            )
            user.set_unusable_password()
            user.first_name = email.split('@')[0].capitalize()
            user.save()
            created = True
            logger.info(f"✅ Usuario creado: {email} (Username: {final_username})")
        else:
            logger.info(f"ℹ️ Usuario ya existía: {email}")
        
        # Verificar si tiene perfil de Usuario
        from ..models import Usuario
        from datetime import timedelta
        
        # Solo definir tipo_usuario para nuevos perfiles
        nuevo_tipo = 'Administrador' if email == correo_especial else 'Externo'
        
        perfil, perfil_created = Usuario.objects.get_or_create(
            user=user,
            defaults={
                'nombres': email.split('@')[0].capitalize(),
                'apepat': '',
                'apemat': '',
                'ci': 'PENDIENTE',
                'correo': email,
                'extension': 'LP',
                'complemento': '',
                'tipo_usuario': nuevo_tipo,
                'ru': '',
                'nro_celular': '',
                'fecha_baja': timezone.now() + timedelta(days=365*5),
                'esta_activo': True
            }
        )
        
        if perfil_created:
            logger.info(f"✅ Perfil creado para: {email} (Tipo: {perfil.tipo_usuario})")
        else:
            # NO cambiar el tipo_usuario si ya existe
            actualizado = False
            if not perfil.nombres or perfil.nombres == '':
                perfil.nombres = email.split('@')[0].capitalize()
                actualizado = True
            if not perfil.correo or perfil.correo == '':
                perfil.correo = email
                actualizado = True
            if actualizado:
                perfil.save()
                logger.info(f"🔄 Perfil actualizado para: {email} (Rol conservado: {perfil.tipo_usuario})")
            else:
                logger.info(f"ℹ️ Perfil ya existía para: {email} (Rol: {perfil.tipo_usuario})")
        
        return user, created, None
        
    except Exception as e:
        logger.error(f"❌ Error con usuario {email}: {str(e)}", exc_info=True)
        return None, False, str(e)


def home(request):
    """PASO 1: Solicitar email - Acepta @umsa.bo y el correo especial"""
    CORREO_ESPECIAL = 'vc3070934@gmail.com'
    
    if request.method == 'POST':
        email = request.POST.get('correo', '').strip().lower()
        
        # Validar formato de email
        try:
            validate_email(email)
        except ValidationError:
            messages.error(request, '❌ Por favor ingresa un correo electrónico válido.')
            return render(request, 'login.html')
        
        # Validación: permite @umsa.bo o el correo específico
        if not (email.endswith('@umsa.bo') or email == CORREO_ESPECIAL):
            messages.error(request, '❌ Solo se permiten correos institucionales @umsa.bo')
            return render(request, 'login.html')
        
        # Verificar intentos fallidos (seguridad)
        ip = request.META.get('REMOTE_ADDR')
        if ip in intentos_fallidos and intentos_fallidos[ip] >= 5:
            messages.error(request, '❌ Demasiados intentos. Espera 5 minutos.')
            return render(request, 'login.html')
        
        # ========== CREAR O OBTENER USUARIO ==========
        user, creado, error = crear_usuario_si_no_existe(email, CORREO_ESPECIAL)
        
        if error or user is None:
            messages.error(request, f'Error al procesar tu cuenta: {error or "Contacta al administrador"}')
            return render(request, 'login.html')
        
        # Verificar si el usuario está activo
        if not user.is_active:
            messages.error(request, '❌ Tu cuenta está desactivada. Contacta al administrador.')
            return render(request, 'login.html')
        
        # Verificar si tiene perfil y si está activo (fecha_baja)
        if hasattr(user, 'usuario'):
            if user.usuario.fecha_baja and user.usuario.fecha_baja < timezone.now():
                messages.error(request, '❌ Tu cuenta ha expirado. Contacta al administrador para renovarla.')
                return render(request, 'login.html')
        else:
            logger.warning(f"Usuario {email} no tiene perfil después de get_or_create")
            messages.error(request, 'Error en la configuración de tu perfil. Contacta al administrador.')
            return render(request, 'login.html')
        
        # Mensaje de bienvenida si es nuevo
        if creado:
            if email == CORREO_ESPECIAL:
                messages.success(request, '✨ ¡Bienvenido Administrador! Se ha creado tu cuenta automáticamente.')
            else:
                messages.info(request, '📝 Se ha creado tu cuenta automáticamente. ¡Bienvenido a la biblioteca!')
        
        # Enviar código de verificación (ASÍNCRONO - no bloquea)
        try:
            enviar_codigo_async(user)
            logger.info(f"Código de verificación enviado a {email} (modo asíncrono)")
        except Exception as e:
            logger.error(f"Error al iniciar envío de código a {email}: {e}")
            messages.error(request, '❌ Error al enviar el código. Intenta nuevamente.')
            return render(request, 'login.html')
        
        # Guardar en sesión que el usuario está en proceso de verificación
        request.session['verificacion_email'] = email
        request.session['verificacion_timestamp'] = str(timezone.now())
        
        # Redirigir al formulario de código
        return redirect('verificar_codigo')
    
    return render(request, 'login.html')


def verificar_codigo_view(request):
    """PASO 2: Ingresar código de verificación"""
    email = request.session.get('verificacion_email')
    if not email:
        messages.error(request, '❌ Por favor inicia el proceso de login nuevamente.')
        return redirect('home')
    
    if request.method == 'POST':
        codigo = request.POST.get('codigo', '').strip()
        
        if not codigo or len(codigo) != 6 or not codigo.isdigit():
            messages.error(request, '❌ Por favor ingresa el código de 6 dígitos.')
            return render(request, 'verificar_codigo.html', {'email': email})
        
        try:
            user = User.objects.get(email=email)
            
            if verificar_codigo(user, codigo):
                user.backend = 'django.contrib.auth.backends.ModelBackend'
                login(request, user)
                
                request.session.pop('verificacion_email', None)
                request.session.pop('verificacion_timestamp', None)
                
                messages.success(request, f'¡Bienvenido/a {user.first_name or user.username}! 👋')
                
                if hasattr(user, 'usuario') and user.usuario.tipo_usuario == 'Administrador':
                    return redirect('principal')
                else:
                    return redirect('inicio')
            else:
                ip = request.META.get('REMOTE_ADDR')
                if ip not in intentos_fallidos:
                    intentos_fallidos[ip] = 0
                intentos_fallidos[ip] += 1
                
                messages.error(request, '❌ Código incorrecto o expirado. Solicita un nuevo código.')
                return render(request, 'verificar_codigo.html', {'email': email})
                
        except User.DoesNotExist:
            messages.error(request, '❌ Usuario no encontrado.')
            return redirect('home')
        except Exception as e:
            logger.error(f"Error en verificación de código: {str(e)}")
            messages.error(request, 'Error al verificar el código. Intenta nuevamente.')
            return render(request, 'verificar_codigo.html', {'email': email})
    
    return render(request, 'verificar_codigo.html', {'email': email})


def reenviar_codigo(request):
    """Reenviar código de verificación vía AJAX"""
    if request.method == 'POST':
        email = request.session.get('verificacion_email')
        if not email:
            return JsonResponse({'success': False, 'error': 'Sesión inválida'})
        
        try:
            user = User.objects.get(email=email)
            enviar_codigo_async(user)
            return JsonResponse({'success': True, 'message': 'Código reenviado a tu correo'})
        except User.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Usuario no encontrado'})
        except Exception as e:
            logger.error(f"Error reenviando código: {str(e)}")
            return JsonResponse({'success': False, 'error': str(e)})
    
    return JsonResponse({'success': False, 'error': 'Método no permitido'})


class CustomLoginView(LoginView):
    template_name = 'login.html'


@login_required
def logout_view(request):
    if request.method == 'GET' or request.method == 'POST':
        logout(request)
        messages.success(request, '¡Has cerrado sesión exitosamente!')
        return redirect('home')
    return HttpResponse('Método no permitido', status=405)


@require_http_methods(["POST"])
@login_required
def cambiar_password(request):
    try:
        data = json.loads(request.body)
        password_actual = data.get('password_actual')
        password_nuevo = data.get('password_nuevo')
        
        if not password_actual or not password_nuevo:
            return JsonResponse({'success': False, 'error': 'Faltan datos'})
        
        if len(password_nuevo) < 8:
            return JsonResponse({'success': False, 'error': 'La nueva contraseña debe tener al menos 8 caracteres'})
        
        if request.user.check_password(password_actual):
            request.user.set_password(password_nuevo)
            request.user.save()
            update_session_auth_hash(request, request.user)
            logger.info(f"Contraseña cambiada para usuario: {request.user.username}")
            return JsonResponse({'success': True})
        else:
            return JsonResponse({'success': False, 'error': 'La contraseña actual es incorrecta'})
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Datos inválidos'})
    except Exception as e:
        logger.error(f"Error en cambiar_password: {str(e)}")
        return JsonResponse({'success': False, 'error': 'Error interno del servidor'})


@require_http_methods(["POST"])
@login_required
@admin_required
def restablecer_password(request):
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Método no permitido'}, status=405)

    try:
        if not hasattr(request.user, 'usuario') or request.user.usuario.tipo_usuario != 'Administrador':
            return JsonResponse({'success': False, 'error': 'No tienes permisos'}, status=403)

        data = json.loads(request.body)
        usuario_id = data.get('usuario_id')
        ci = data.get('ci')
        
        if not usuario_id or not ci:
            return JsonResponse({'success': False, 'error': 'Faltan datos'}, status=400)

        from ..models import Usuario
        usuario = Usuario.objects.get(usuario_id=usuario_id)
        
        if not usuario.user:
            return JsonResponse({'success': False, 'error': 'Usuario sin cuenta asociada'}, status=400)

        usuario.user.set_password(ci)
        usuario.user.save()
        logger.info(f"Contraseña restablecida para usuario: {usuario.user.username} por admin: {request.user.username}")
        
        return JsonResponse({'success': True, 'message': 'Contraseña restablecida correctamente'})
        
    except Usuario.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Usuario no encontrado'}, status=404)
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Datos inválidos'}, status=400)
    except Exception as e:
        logger.error(f"Error al restablecer contraseña: {str(e)}", exc_info=True)
        return JsonResponse({'success': False, 'error': 'Error interno del servidor'}, status=500)