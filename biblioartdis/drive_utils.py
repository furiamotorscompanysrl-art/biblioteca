# biblioartdis/drive_utils.py
import os
import io
import json
import base64
import pickle
import logging
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload
from googleapiclient.errors import HttpError

logger = logging.getLogger(__name__)


def get_drive_service():
    """
    Obtiene el servicio de Google Drive autenticado con OAuth
    Usa las mismas variables que Gmail: DRIVE_TOKEN_BASE64 y DRIVE_CREDENTIALS_BASE64
    """
    try:
        # Obtener token y credenciales desde variables de entorno
        token_base64 = os.environ.get('DRIVE_TOKEN_BASE64')
        creds_base64 = os.environ.get('DRIVE_CREDENTIALS_BASE64')
        
        # Si no existen, intentar con el formato antiguo (compatibilidad)
        if not token_base64 or not creds_base64:
            logger.warning("⚠️ Usando formato antiguo de credenciales de Drive")
            creds_json = os.environ.get('GOOGLE_DRIVE_OAUTH_CREDENTIALS')
            if creds_json:
                creds_info = json.loads(creds_json)
                credentials = Credentials(
                    token=creds_info.get('token'),
                    refresh_token=creds_info.get('refresh_token'),
                    token_uri=creds_info.get('token_uri', 'https://oauth2.googleapis.com/token'),
                    client_id=creds_info.get('client_id'),
                    client_secret=creds_info.get('client_secret'),
                    scopes=creds_info.get('scopes', ['https://www.googleapis.com/auth/drive.file'])
                )
                service = build('drive', 'v3', credentials=credentials)
                logger.info("✅ Servicio Google Drive inicializado (formato antiguo)")
                return service
            else:
                logger.error("❌ No se encontraron credenciales de Drive")
                return None
        
        # Decodificar token
        token_data = base64.b64decode(token_base64)
        creds = pickle.loads(token_data)
        
        # Verificar si el token ha expirado y tiene refresh_token
        if creds.expired:
            if creds.refresh_token:
                logger.info("🔄 Token de Drive expirado. Refrescando automáticamente...")
                creds.refresh(Request())
                logger.info("✅ Token de Drive refrescado exitosamente")
            else:
                logger.error("❌ No hay refresh_token disponible para Drive.")
                return None
        
        # Construir servicio
        service = build('drive', 'v3', credentials=creds)
        logger.info("✅ Servicio Google Drive inicializado correctamente")
        return service
        
    except pickle.UnpicklingError as e:
        logger.error(f"❌ Error al decodificar token pickle de Drive: {e}")
        return None
    except Exception as e:
        logger.error(f"❌ Error obteniendo servicio Drive: {e}")
        return None


def subir_pdf_a_drive(archivo_pdf, nombre_archivo=None, folder_id=None):
    """Sube un PDF a Google Drive usando OAuth"""
    try:
        service = get_drive_service()
        if not service:
            logger.error("❌ No se pudo obtener servicio de Drive")
            return None
        
        # Obtener folder_id de variables de entorno si no se proporciona
        folder_id = folder_id or os.environ.get('GOOGLE_DRIVE_FOLDER_ID')
        
        if not folder_id:
            logger.error("❌ GOOGLE_DRIVE_FOLDER_ID no configurada")
            return None
        
        if not nombre_archivo:
            nombre_archivo = archivo_pdf.name
        
        # Leer el contenido del archivo
        if hasattr(archivo_pdf, 'read'):
            contenido = archivo_pdf.read()
            archivo_pdf.seek(0)
        else:
            # Si es una ruta de archivo
            with open(archivo_pdf, 'rb') as f:
                contenido = f.read()
        
        media = MediaIoBaseUpload(
            io.BytesIO(contenido),
            mimetype='application/pdf',
            resumable=True
        )
        
        file_metadata = {
            'name': nombre_archivo,
            'parents': [folder_id]
        }
        
        logger.info(f"📤 Subiendo PDF a Google Drive: {nombre_archivo}")
        file = service.files().create(
            body=file_metadata,
            media_body=media,
            fields='id, webViewLink'
        ).execute()
        
        file_id = file.get('id')
        preview_url = f"https://drive.google.com/file/d/{file_id}/preview"
        
        logger.info(f"✅ PDF subido a Google Drive: {preview_url}")
        return preview_url
        
    except HttpError as e:
        logger.error(f"❌ Error HTTP subiendo PDF: {e}")
        return None
    except Exception as e:
        logger.error(f"❌ Error subiendo PDF: {str(e)}")
        return None


def eliminar_pdf_de_drive(file_id):
    """Elimina un archivo de Google Drive por su ID"""
    try:
        service = get_drive_service()
        if not service:
            return False
        
        service.files().delete(fileId=file_id).execute()
        logger.info(f"✅ Archivo de Drive eliminado: {file_id}")
        return True
        
    except HttpError as e:
        if e.resp.status == 404:
            logger.warning(f"⚠️ Archivo no encontrado en Drive: {file_id}")
            return True  # Ya no existe
        logger.error(f"❌ Error eliminando archivo de Drive: {e}")
        return False
    except Exception as e:
        logger.error(f"❌ Error eliminando archivo de Drive: {e}")
        return False


def test_drive_connection():
    """Prueba la conexión con Google Drive"""
    print("=" * 50)
    print("🧪 Probando conexión con Google Drive...")
    print("=" * 50)
    
    service = get_drive_service()
    if not service:
        print("❌ No se pudo conectar a Google Drive")
        return False
    
    try:
        # Verificar espacio disponible
        about = service.about().get(fields="storageQuota").execute()
        storage = about.get('storageQuota', {})
        used = int(storage.get('usage', 0)) / (1024**3)
        total = int(storage.get('limit', 0)) / (1024**3)
        
        print(f"✅ Conexión a Drive exitosa")
        print(f"   📁 Espacio usado: {used:.2f} GB")
        print(f"   💾 Espacio total: {total:.2f} GB")
        print(f"   📊 Disponible: {total - used:.2f} GB")
        
        # Verificar folder
        folder_id = os.environ.get('GOOGLE_DRIVE_FOLDER_ID')
        if folder_id:
            try:
                folder = service.files().get(fileId=folder_id).execute()
                print(f"   📂 Folder configurado: {folder.get('name')}")
            except Exception as e:
                print(f"   ⚠️ No se pudo verificar el folder: {e}")
        else:
            print("   ⚠️ GOOGLE_DRIVE_FOLDER_ID no configurada")
        
        return True
        
    except Exception as e:
        print(f"❌ Error en prueba: {e}")
        return False


# ============================================
# FUNCIÓN DE SUBIDA ASÍNCRONA A GOOGLE DRIVE
# ============================================
def subir_pdf_a_drive_async(pdf_original, nombre_archivo, libro_id):
    """Sube un PDF a Google Drive en segundo plano"""
    import threading
    
    def upload_thread():
        try:
            from ..models import Libro
            
            # Subir a Drive
            drive_url = subir_pdf_a_drive(pdf_original, nombre_archivo)
            
            if drive_url:
                # Actualizar el libro con la URL de Drive
                libro = Libro.objects.get(id_libro=libro_id)
                libro.google_drive_url = drive_url
                libro.pdf = None
                libro.save()
                logger.info(f"✅ PDF subido asíncronamente a Google Drive: {drive_url} (Libro ID: {libro_id})")
            else:
                logger.error(f"❌ Falló subida asíncrona a Drive para libro {libro_id}")
        except Exception as e:
            logger.error(f"❌ Error en subida asíncrona a Drive: {str(e)}")
    
    thread = threading.Thread(target=upload_thread)
    thread.daemon = True
    thread.start()
    return thread