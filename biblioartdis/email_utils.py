# email_utils.py
import random
import logging
import base64
import pickle
import os
from email.message import EmailMessage
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from django.conf import settings
from django.utils import timezone
from datetime import timedelta
from .models import CodigoVerificacion

logger = logging.getLogger(__name__)


def get_gmail_service():
    """
    Obtiene el servicio de Gmail API usando credenciales desde variables de entorno de Railway
    Con autorefresco automático de token
    """
    try:
        # Obtener credenciales desde variables de entorno de Railway
        creds_base64 = os.environ.get('GMAIL_CREDENTIALS_BASE64')
        token_base64 = os.environ.get('GMAIL_TOKEN_BASE64')
        
        if not creds_base64 or not token_base64:
            logger.error("❌ Credenciales de Gmail no encontradas en variables de entorno")
            return None
        
        # Decodificar credenciales
        creds_json = base64.b64decode(creds_base64).decode('utf-8')
        token_data = base64.b64decode(token_base64)
        
        # Cargar credenciales
        creds = pickle.loads(token_data)
        
        # Verificar si el token ha expirado y tiene refresh_token
        if creds.expired:
            if creds.refresh_token:
                logger.info("🔄 Token de Gmail expirado. Refrescando automáticamente...")
                creds.refresh(Request())
                logger.info("✅ Token refrescado exitosamente")
                
                # Opcional: Guardar el token refrescado (si quieres persistencia)
                # Pero como está en memoria, el próximo ciclo se refrescará de nuevo si es necesario
            else:
                logger.error("❌ No hay refresh_token disponible. El token expiró permanentemente.")
                logger.error("   Debes regenerar el token ejecutando generate_gmail_token.py")
                return None
        
        # Construir servicio
        service = build('gmail', 'v1', credentials=creds)
        logger.info("✅ Servicio Gmail API inicializado correctamente")
        return service
        
    except pickle.UnpicklingError as e:
        logger.error(f"❌ Error al decodificar el token pickle: {e}")
        return None
    except Exception as e:
        logger.error(f"❌ Error obteniendo servicio Gmail: {e}")
        return None


def generar_codigo_verificacion():
    """Genera un código aleatorio de 6 dígitos"""
    return f"{random.randint(100000, 999999)}"


def obtener_url_sitio():
    """Obtiene la URL base del sitio según el entorno"""
    if settings.DEBUG:
        return 'http://127.0.0.1:8000'
    else:
        return 'https://bibliotecaartdisumsa-production.up.railway.app'


def enviar_codigo_verificacion(usuario):
    """
    Envía un código de verificación usando Gmail API
    Retorna el objeto CodigoVerificacion o None si hay error
    """
    try:
        # Eliminar códigos anteriores no usados y expirados
        CodigoVerificacion.objects.filter(
            usuario=usuario,
            usado=False,
            expira_en__lt=timezone.now()
        ).delete()

        # Generar nuevo código
        codigo = generar_codigo_verificacion()
        expiracion = timezone.now() + timedelta(minutes=10)

        # Guardar en base de datos
        codigo_obj = CodigoVerificacion.objects.create(
            usuario=usuario,
            codigo=codigo,
            expira_en=expiracion
        )

        # Obtener servicio Gmail
        service = get_gmail_service()
        if not service:
            logger.error("❌ No se pudo obtener servicio Gmail. El código se guardó pero no se envió.")
            # Devolvemos el código aunque no se haya enviado (se puede reenviar después)
            return codigo_obj

        sitio_url = obtener_url_sitio()
        nombre_usuario = usuario.first_name or usuario.username or "Usuario"

        asunto = "🔐 Código de verificación - Biblioteca ARTyDIS"
        
        # Versión HTML del mensaje
        mensaje_html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Código de verificación</title>
    <style>
        body {{
            font-family: 'Segoe UI', Arial, sans-serif;
            background-color: #f0f4f8;
            margin: 0;
            padding: 20px;
        }}
        .container {{
            max-width: 550px;
            margin: 0 auto;
            background: white;
            border-radius: 16px;
            overflow: hidden;
            box-shadow: 0 4px 20px rgba(0,0,0,0.1);
        }}
        .header {{
            background: linear-gradient(135deg, #0F2B3D 0%, #1A3A4F 100%);
            color: white;
            padding: 30px 20px;
            text-align: center;
        }}
        .header h2 {{
            margin: 0;
            font-size: 24px;
        }}
        .header p {{
            margin: 8px 0 0;
            opacity: 0.9;
        }}
        .content {{
            padding: 30px;
        }}
        .greeting {{
            font-size: 18px;
            font-weight: 600;
            color: #1F2937;
            margin-bottom: 20px;
        }}
        .message {{
            color: #6B7280;
            line-height: 1.6;
            margin-bottom: 25px;
        }}
        .code-container {{
            background: #F8FAFC;
            border-radius: 12px;
            padding: 20px;
            text-align: center;
            margin: 20px 0;
            border: 1px solid #E5E7EB;
        }}
        .code-label {{
            font-size: 12px;
            text-transform: uppercase;
            letter-spacing: 2px;
            color: #F59E0B;
            font-weight: 600;
            margin-bottom: 10px;
        }}
        .code-value {{
            font-size: 36px;
            font-weight: 800;
            letter-spacing: 5px;
            color: #0F2B3D;
            background: white;
            padding: 12px 20px;
            border-radius: 10px;
            display: inline-block;
            font-family: monospace;
        }}
        .expiry-info {{
            background: #FEF3C7;
            border-radius: 8px;
            padding: 10px;
            text-align: center;
            margin: 20px 0;
            color: #D97706;
            font-size: 13px;
        }}
        .btn {{
            display: inline-block;
            background: #0F2B3D;
            color: white;
            padding: 12px 24px;
            border-radius: 8px;
            text-decoration: none;
            font-weight: 600;
            margin-top: 15px;
        }}
        .footer {{
            background: #F8FAFC;
            padding: 20px;
            text-align: center;
            font-size: 11px;
            color: #9CA3AF;
            border-top: 1px solid #E5E7EB;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h2>📚 Biblioteca ARTyDIS</h2>
            <p>Verificación de acceso</p>
        </div>
        <div class="content">
            <div class="greeting">
                ¡Hola, {nombre_usuario}! 👋
            </div>
            <div class="message">
                Has solicitado acceder a la Biblioteca Digital ARTyDIS. 
                Para completar tu ingreso, utiliza el siguiente código de verificación:
            </div>
            <div class="code-container">
                <div class="code-label">TU CÓDIGO DE ACCESO</div>
                <div class="code-value">{codigo}</div>
            </div>
            <div class="expiry-info">
                ⏰ Este código es válido por <strong>10 minutos</strong>
            </div>
            <div style="text-align: center;">
                <a href="{sitio_url}" class="btn">🔐 Ir a la biblioteca</a>
            </div>
        </div>
        <div class="footer">
            <p>Biblioteca Digital ARTyDIS - Carrera de Artes y Diseño Gráfico</p>
            <p>Universidad Mayor de San Andrés</p>
            <p>Si no solicitaste este código, ignora este mensaje.</p>
        </div>
    </div>
</body>
</html>
        """

        # Versión texto plano (fallback)
        mensaje_texto = f"""
Hola {nombre_usuario},

Has solicitado acceder a la Biblioteca Digital ARTyDIS.

Tu código de verificación es: {codigo}

Este código es válido por 10 minutos.

Accede a: {sitio_url}

Si no solicitaste este código, ignora este mensaje.

---
Biblioteca ARTyDIS - UMSA
"""

        # Crear mensaje MIME
        message = EmailMessage()
        message.set_content(mensaje_texto)
        message.add_alternative(mensaje_html, subtype='html')
        message['To'] = usuario.email
        message['From'] = 'Biblioteca ARTyDIS <biblioteca.artesdis.umsa@gmail.com>'
        message['Subject'] = asunto

        # Codificar mensaje en base64
        encoded_message = base64.urlsafe_b64encode(message.as_bytes()).decode()

        # Enviar usando Gmail API
        send_message = {
            'raw': encoded_message
        }
        
        service.users().messages().send(
            userId='me',
            body=send_message
        ).execute()

        logger.info(f"✅ Código enviado exitosamente a {usuario.email} via Gmail API")
        return codigo_obj

    except Exception as e:
        logger.error(f"❌ Error al enviar código a {usuario.email}: {str(e)}", exc_info=True)
        return None


def verificar_codigo(usuario, codigo_ingresado):
    """
    Verifica si el código ingresado es válido
    Retorna True si es válido, False en caso contrario
    """
    try:
        codigo_obj = CodigoVerificacion.objects.filter(
            usuario=usuario,
            codigo=codigo_ingresado,
            usado=False,
            expira_en__gt=timezone.now()
        ).latest('creado_en')

        codigo_obj.usado = True
        codigo_obj.save()

        logger.info(f"✅ Código verificado exitosamente para {usuario.email}")
        return True

    except CodigoVerificacion.DoesNotExist:
        logger.warning(f"⚠️ Código inválido o expirado para {usuario.email}")
        return False
    except Exception as e:
        logger.error(f"❌ Error verificando código para {usuario.email}: {e}")
        return False


def test_gmail_connection():
    """
    Función de prueba para verificar la conexión con Gmail API
    Ejecutar desde Django shell: from biblioartdis.email_utils import test_gmail_connection; test_gmail_connection()
    """
    print("=" * 50)
    print("Probando conexión con Gmail API...")
    print("=" * 50)
    
    service = get_gmail_service()
    if service:
        print("✅ Servicio Gmail API inicializado correctamente")
        
        # Probar enviar un correo de prueba (opcional)
        try:
            from django.contrib.auth.models import User
            user = User.objects.filter(email__endswith='@gmail.com').first()
            if user:
                print(f"📧 Enviando correo de prueba a {user.email}...")
                enviar_codigo_verificacion(user)
                print("✅ Correo de prueba enviado")
            else:
                print("ℹ️ No se encontró usuario con correo Gmail para prueba")
        except Exception as e:
            print(f"❌ Error enviando correo de prueba: {e}")
    else:
        print("❌ No se pudo inicializar el servicio Gmail API")
        print("   Verifica que GMAIL_CREDENTIALS_BASE64 y GMAIL_TOKEN_BASE64 estén configurados")

    return service is not None