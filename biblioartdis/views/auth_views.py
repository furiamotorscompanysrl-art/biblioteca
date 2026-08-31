from django.shortcuts import render, redirect, get_object_or_404
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
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.views.decorators.csrf import csrf_exempt
import json
import logging
import re
import threading
import os
import tempfile

from ..decorators import admin_required
from ..email_utils import enviar_codigo_verificacion, verificar_codigo
from ..forms import RegistroUsuarioForm, RestablecerPasswordForm, LoginForm
from ..google_drive_utils import drive_service
from django.conf import settings

logger = logging.getLogger(__name__)

# Diccionario temporal para almacenar intentos de login
intentos_fallidos = {}


def home(request):
    """
    Login con email y contraseña
    """
    # Si ya está autenticado, redirigir según rol
    if request.user.is_authenticated:
        if hasattr(request.user, 'usuario'):
            if request.user.usuario.tipo_usuario == 'Administrador':
                return redirect('principal')
            else:
                return redirect('inicio')
        return redirect('inicio')
    
    if request.method == 'POST':
        email = request.POST.get('email', '').strip().lower()
        password = request.POST.get('password', '')
        
        # Validar que no estén vacíos
        if not email or not password:
            messages.error(request, '❌ Por favor ingresa tu correo y contraseña.')
            return render(request, 'login.html')
        
        # Validar formato de email
        try:
            validate_email(email)
        except ValidationError:
            messages.error(request, '❌ Por favor ingresa un correo electrónico válido.')
            return render(request, 'login.html')
        
        # Validar que sea correo UMSA o el correo especial admin
        CORREO_ESPECIAL = 'vc3070934@gmail.com'
        if not (email.endswith('@umsa.bo') or email == CORREO_ESPECIAL):
            messages.error(request, '❌ Solo se permiten correos institucionales @umsa.bo')
            return render(request, 'login.html')
        
        # Buscar usuario por email
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            messages.error(request, '❌ No existe una cuenta con este correo. Por favor regístrate.')
            return render(request, 'login.html')
        
        # Verificar si el usuario está activo
        if not user.is_active:
            messages.error(request, '❌ Tu cuenta está desactivada. Contacta al administrador.')
            return render(request, 'login.html')
        
        # Verificar estado de registro
        if hasattr(user, 'usuario'):
            usuario = user.usuario
            
            if usuario.estado_registro == 'pendiente':
                messages.warning(request, 
                    '⏳ Tu solicitud está pendiente de aprobación. '
                    'El administrador revisará tus documentos y te notificará.'
                )
                return render(request, 'login.html')
            
            if usuario.estado_registro == 'rechazado':
                messages.error(request, 
                    f'❌ Tu solicitud fue rechazada. Motivo: {usuario.motivo_rechazo or "No especificado"}'
                )
                return render(request, 'login.html')
            
            # Verificar expiración
            if usuario.fecha_baja and usuario.fecha_baja < timezone.now():
                messages.error(request, '❌ Tu cuenta ha expirado. Contacta al administrador.')
                return render(request, 'login.html')
        else:
            messages.error(request, '❌ Error en la configuración de tu perfil. Contacta al administrador.')
            return render(request, 'login.html')
        
        # Verificar contraseña
        if not user.check_password(password):
            # Registrar intento fallido
            ip = request.META.get('REMOTE_ADDR')
            if ip not in intentos_fallidos:
                intentos_fallidos[ip] = 0
            intentos_fallidos[ip] += 1
            
            if intentos_fallidos[ip] >= 5:
                messages.error(request, '❌ Demasiados intentos fallidos. Espera 5 minutos.')
                return render(request, 'login.html')
            
            messages.error(request, '❌ Contraseña incorrecta.')
            return render(request, 'login.html')
        
        # Iniciar sesión
        user.backend = 'django.contrib.auth.backends.ModelBackend'
        login(request, user)
        
        messages.success(request, f'¡Bienvenido/a {user.first_name or user.username}! 👋')
        
        # Redirigir según rol
        if hasattr(user, 'usuario') and user.usuario.tipo_usuario == 'Administrador':
            return redirect('principal')
        else:
            return redirect('inicio')
    
    return render(request, 'login.html')


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


# ============================================
# REGISTRO CON APROBACIÓN MANUAL
# ============================================

def registrar_usuario(request):
    """Vista para que los usuarios soliciten acceso"""
    from django.utils import timezone
    
    if request.method == 'POST':
        form = RegistroUsuarioForm(request.POST, request.FILES)
        if form.is_valid():
            # El formulario ya se encarga de crear el User y el Usuario
            usuario = form.save()
            
            # Notificar al administrador
            notificar_admin_nuevo_registro(usuario)
            
            messages.success(request, 
                '✅ Tu solicitud ha sido enviada. '
                'El administrador revisará tus documentos y te notificará por correo.'
            )
            return redirect('login')
    else:
        form = RegistroUsuarioForm()
    
    return render(request, 'registrar_usuario.html', {'form': form})


def notificar_admin_nuevo_registro(usuario):
    """Notificar a los administradores que hay un nuevo registro pendiente"""
    try:
        admins = User.objects.filter(is_superuser=True)
        for admin in admins:
            if admin.email:
                html = render_to_string('email/nuevo_registro_admin.html', {
                    'usuario': usuario,
                    'admin': admin,
                    'domain': 'biblioteca-production-b2fa.up.railway.app'
                })
                send_mail(
                    subject='📝 Nuevo registro pendiente de aprobación',
                    message=f'El usuario {usuario.nombres} {usuario.apepat} ha solicitado acceso.',
                    html_message=html,
                    from_email='Biblioteca ARTyDIS <noreply@example.com>',
                    recipient_list=[admin.email],
                    fail_silently=True
                )
    except Exception as e:
        logger.error(f"Error notificando admin: {e}")


@login_required
@admin_required
def listar_solicitudes_pendientes(request):
    """Vista para administradores - Lista de solicitudes pendientes"""
    if not request.user.is_superuser:
        messages.error(request, 'No tienes permiso para ver esta página')
        return redirect('inicio')
    
    pendientes = Usuario.objects.filter(estado_registro='pendiente')
    return render(request, 'solicitudes_pendientes.html', {
        'pendientes': pendientes
    })


@login_required
@admin_required
def aprobar_usuario(request, usuario_id):
    """Administrador aprueba un usuario"""
    if not request.user.is_superuser:
        messages.error(request, 'No tienes permiso')
        return redirect('inicio')
    
    usuario = get_object_or_404(Usuario, usuario_id=usuario_id)
    usuario.estado_registro = 'aprobado'
    usuario.fecha_aprobacion = timezone.now()
    usuario.aprobado_por = request.user.usuario
    usuario.esta_activo = True
    usuario.save()
    
    # Activar el usuario de Django
    usuario.user.is_active = True
    usuario.user.save()
    
    # Notificar al usuario
    notificar_usuario_aprobado(usuario)
    
    messages.success(request, f'✅ Usuario {usuario.nombres} aprobado correctamente')
    return redirect('solicitudes_pendientes')


@login_required
@admin_required
def rechazar_usuario(request, usuario_id):
    """Administrador rechaza un usuario"""
    if not request.user.is_superuser:
        messages.error(request, 'No tienes permiso')
        return redirect('inicio')
    
    usuario = get_object_or_404(Usuario, usuario_id=usuario_id)
    if request.method == 'POST':
        motivo = request.POST.get('motivo', 'No especificado')
        usuario.estado_registro = 'rechazado'
        usuario.motivo_rechazo = motivo
        usuario.esta_activo = False
        usuario.save()
        
        # Desactivar usuario de Django
        usuario.user.is_active = False
        usuario.user.save()
        
        # Notificar al usuario
        notificar_usuario_rechazado(usuario, motivo)
        
        messages.success(request, f'❌ Usuario {usuario.nombres} rechazado')
        return redirect('solicitudes_pendientes')
    
    return render(request, 'rechazar_usuario.html', {'usuario': usuario})


def notificar_usuario_aprobado(usuario):
    """Notificar al usuario que fue aprobado"""
    try:
        if usuario.correo:
            send_mail(
                subject='✅ Tu cuenta ha sido aprobada',
                message=f'''
Hola {usuario.nombres},

Tu solicitud de acceso a la Biblioteca ARTyDIS ha sido APROBADA.

Ya puedes iniciar sesión en: https://biblioteca-production-b2fa.up.railway.app/

Tus credenciales son:
Usuario: {usuario.user.username}
Contraseña: La que registraste

¡Bienvenido/a!

Saludos,
Biblioteca ARTyDIS
''',
                from_email='Biblioteca ARTyDIS <noreply@example.com>',
                recipient_list=[usuario.correo],
                fail_silently=True
            )
    except Exception as e:
        logger.error(f"Error notificando usuario aprobado: {e}")


def notificar_usuario_rechazado(usuario, motivo):
    """Notificar al usuario que fue rechazado"""
    try:
        if usuario.correo:
            send_mail(
                subject='❌ Tu solicitud ha sido rechazada',
                message=f'''
Hola {usuario.nombres},

Tu solicitud de acceso a la Biblioteca ARTyDIS ha sido RECHAZADA.

Motivo: {motivo}

Si consideras que esto es un error, por favor contacta al administrador.

Saludos,
Biblioteca ARTyDIS
''',
                from_email='Biblioteca ARTyDIS <noreply@example.com>',
                recipient_list=[usuario.correo],
                fail_silently=True
            )
    except Exception as e:
        logger.error(f"Error notificando usuario rechazado: {e}")


# ============================================
# RESTABLECER CONTRASEÑA (ADMIN)
# ============================================

@login_required
@admin_required
def restablecer_password_admin(request):
    """Vista para que el administrador restablezca contraseñas"""
    if not request.user.is_superuser:
        messages.error(request, 'No tienes permiso')
        return redirect('inicio')
    
    usuario_id = request.GET.get('usuario_id')
    usuario = None
    
    if usuario_id:
        usuario = get_object_or_404(Usuario, usuario_id=usuario_id)
    
    if request.method == 'POST':
        form = RestablecerPasswordForm(request.POST)
        if form.is_valid():
            usuario_id = form.cleaned_data['usuario_id']
            nueva_password = form.cleaned_data['nueva_password']
            usuario_obj = get_object_or_404(Usuario, usuario_id=usuario_id)
            
            usuario_obj.user.set_password(nueva_password)
            usuario_obj.user.save()
            usuario_obj.puede_restablecer_password = False
            usuario_obj.save()
            
            messages.success(request, f'🔑 Contraseña restablecida para {usuario_obj.nombres}')
            return redirect('lista_usuarios')
    else:
        form = RestablecerPasswordForm(initial={'usuario_id': usuario_id})
    
    return render(request, 'restablecer_password_admin.html', {
        'form': form,
        'usuario': usuario
    })


@require_http_methods(["POST"])
@login_required
@admin_required
def restablecer_password_api(request):
    """API para restablecer contraseña vía AJAX"""
    try:
        data = json.loads(request.body)
        usuario_id = data.get('usuario_id')
        nueva_password = data.get('nueva_password')
        
        if not usuario_id or not nueva_password:
            return JsonResponse({'success': False, 'error': 'Faltan datos'})
        
        if len(nueva_password) < 9:
            return JsonResponse({'success': False, 'error': 'La contraseña debe tener al menos 9 caracteres'})
        
        usuario = get_object_or_404(Usuario, usuario_id=usuario_id)
        usuario.user.set_password(nueva_password)
        usuario.user.save()
        usuario.puede_restablecer_password = False
        usuario.save()
        
        logger.info(f"Contraseña restablecida para usuario: {usuario.user.username} por admin: {request.user.username}")
        
        return JsonResponse({'success': True, 'message': 'Contraseña restablecida correctamente'})
        
    except Usuario.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Usuario no encontrado'})
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Datos inválidos'})
    except Exception as e:
        logger.error(f"Error al restablecer contraseña: {str(e)}", exc_info=True)
        return JsonResponse({'success': False, 'error': 'Error interno del servidor'})


# ============================================
# SUBIDA A GOOGLE DRIVE VÍA AJAX
# ============================================

@csrf_exempt
def upload_to_drive_ajax(request):
    """Vista AJAX para subir archivos a Google Drive en tiempo real"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Método no permitido'}, status=405)
    
    try:
        # Obtener el archivo
        archivo = request.FILES.get('file')
        if not archivo:
            return JsonResponse({'success': False, 'error': 'No se recibió ningún archivo'})
        
        # Obtener el tipo de documento
        tipo_documento = request.POST.get('tipo', 'documento')
        
        # Mapeo de tipos a carpetas
        carpetas = {
            'matricula': 'Usuarios/Matriculas',
            'carnet_frente': 'Usuarios/Carnets/Frente',
            'carnet_reverso': 'Usuarios/Carnets/Reverso'
        }
        
        folder_path = carpetas.get(tipo_documento, 'Usuarios/General')
        
        # Guardar archivo temporalmente
        ext = os.path.splitext(archivo.name)[1]
        with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as tmp_file:
            for chunk in archivo.chunks():
                tmp_file.write(chunk)
            tmp_path = tmp_file.name
        
        try:
            # Obtener o crear la carpeta en Google Drive
            folder_id = drive_service.get_or_create_folder(
                folder_path,
                settings.GOOGLE_DRIVE_FOLDER_ID
            )
            
            if not folder_id:
                return JsonResponse({'success': False, 'error': 'No se pudo crear la carpeta en Drive'})
            
            # Generar nombre único (usamos timestamp para evitar colisiones)
            from datetime import datetime
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            nombre_archivo = f"temp_{timestamp}_{tipo_documento}{ext}"
            
            # Subir a Google Drive
            resultado = drive_service.upload_file(
                file_path=tmp_path,
                file_name=nombre_archivo,
                folder_id=folder_id
            )
            
            # Eliminar archivo temporal
            try:
                os.unlink(tmp_path)
            except:
                pass
            
            if resultado and resultado.get('download_link'):
                # Devolver la URL de descarga y el ID del archivo
                return JsonResponse({
                    'success': True,
                    'url': resultado['download_link'],
                    'file_id': resultado['file_id'],
                    'message': 'Archivo subido correctamente'
                })
            else:
                return JsonResponse({'success': False, 'error': 'Error al subir archivo a Drive'})
                
        except Exception as e:
            # Limpiar archivo temporal en caso de error
            try:
                os.unlink(tmp_path)
            except:
                pass
            return JsonResponse({'success': False, 'error': str(e)})
            
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})