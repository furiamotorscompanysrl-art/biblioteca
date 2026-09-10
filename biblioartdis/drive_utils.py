# biblioartdis/drive_utils.py
import os
import io
import json
import base64
import pickle
import logging
import tempfile
import threading
import re
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload, MediaFileUpload
from googleapiclient.errors import HttpError
from django.conf import settings
from django.apps import apps

logger = logging.getLogger(__name__)


# ============================================
# SERVICIO Y CARPETAS
# ============================================

def get_drive_service():
    """Obtiene el servicio de Google Drive autenticado con OAuth"""
    try:
        # PRIMERO: OAuth estándar
        creds_json = os.environ.get('GOOGLE_DRIVE_OAUTH_CREDENTIALS')
        token_json = os.environ.get('GOOGLE_DRIVE_TOKEN')
        
        if creds_json and token_json:
            try:
                token_data = json.loads(token_json)
                
                credentials = Credentials(
                    token=token_data.get('token'),
                    refresh_token=token_data.get('refresh_token'),
                    token_uri=token_data.get('token_uri', 'https://oauth2.googleapis.com/token'),
                    client_id=token_data.get('client_id'),
                    client_secret=token_data.get('client_secret'),
                    scopes=token_data.get('scopes', ['https://www.googleapis.com/auth/drive.file'])
                )
                
                if credentials.expired and credentials.refresh_token:
                    logger.info("Refrescando token de Drive...")
                    credentials.refresh(Request())
                    logger.info("Token de Drive refrescado")
                
                service = build('drive', 'v3', credentials=credentials)
                logger.info("Servicio Google Drive inicializado (OAuth estandar)")
                return service
                
            except Exception as e:
                logger.warning(f"Error con OAuth estandar: {e}")
        
        # SEGUNDO: base64
        token_base64 = os.environ.get('DRIVE_TOKEN_BASE64')
        creds_base64 = os.environ.get('DRIVE_CREDENTIALS_BASE64')
        
        if token_base64 and creds_base64:
            try:
                token_data = base64.b64decode(token_base64)
                creds = pickle.loads(token_data)
                
                if creds.expired and creds.refresh_token:
                    creds.refresh(Request())
                
                service = build('drive', 'v3', credentials=creds)
                logger.info("Servicio Google Drive inicializado (base64)")
                return service
            except Exception as e:
                logger.warning(f"Error con base64: {e}")
        
        # TERCERO: google_drive_utils (cuenta de servicio)
        try:
            from .google_drive_utils import drive_service
            if drive_service and hasattr(drive_service, 'service') and drive_service.service:
                logger.info("Servicio Google Drive desde google_drive_utils")
                return drive_service.service
        except Exception as e:
            logger.warning(f"Error usando google_drive_utils: {e}")
        
        logger.error("No se encontraron credenciales validas de Drive")
        return None
        
    except Exception as e:
        logger.error(f"Error obteniendo servicio Drive: {e}")
        return None


def get_main_folder_id():
    """Obtiene el ID de la carpeta principal de Google Drive"""
    folder_id = os.environ.get('GOOGLE_DRIVE_FOLDER_ID')
    if not folder_id:
        logger.error("GOOGLE_DRIVE_FOLDER_ID no configurada")
        return None
    return folder_id


def get_or_create_folder(service, folder_path, parent_folder_id=None):
    """Obtiene o crea una carpeta en Google Drive por ruta"""
    try:
        if not service:
            logger.error("Servicio de Drive no disponible")
            return None
        
        parts = folder_path.split('/')
        current_parent = parent_folder_id
        
        for part in parts:
            query = f"name='{part}' and mimeType='application/vnd.google-apps.folder' and trashed=false"
            if current_parent:
                query += f" and '{current_parent}' in parents"
            
            results = service.files().list(
                q=query,
                spaces='drive',
                fields='files(id, name)'
            ).execute()
            
            files = results.get('files', [])
            
            if files:
                current_parent = files[0].get('id')
                logger.debug(f"Carpeta encontrada: {part} (ID: {current_parent})")
            else:
                file_metadata = {
                    'name': part,
                    'mimeType': 'application/vnd.google-apps.folder'
                }
                if current_parent:
                    file_metadata['parents'] = [current_parent]
                
                folder = service.files().create(
                    body=file_metadata,
                    fields='id'
                ).execute()
                
                current_parent = folder.get('id')
                logger.info(f"Carpeta creada: {part} (ID: {current_parent})")
        
        return current_parent
        
    except HttpError as e:
        logger.error(f"Error HTTP con carpeta {folder_path}: {e}")
        return None
    except Exception as e:
        logger.error(f"Error con carpeta {folder_path}: {e}")
        return None


def extract_file_id_from_url(url):
    """Extrae el ID de archivo de una URL de Google Drive"""
    if not url:
        return None
    
    patterns = [
        r'/file/d/([^/]+)',
        r'id=([^&]+)',
        r'drive\.google\.com/open\?id=([^&]+)',
        r'drive\.google\.com/uc\?id=([^&]+)'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    
    return None


# ============================================
# SUBIDA DE PDF (SINCRONA)
# ============================================

def subir_pdf_a_drive(archivo_pdf, nombre_archivo=None, folder_path='Material_Biblioteca/Libros/PDFs'):
    """
    Sube un PDF a Google Drive (versión síncrona).
    Hace el PDF público para que se pueda ver en iframe.
    """
    try:
        service = get_drive_service()
        if not service:
            logger.error("No se pudo obtener servicio de Drive")
            return None
        
        main_folder_id = get_main_folder_id()
        if not main_folder_id:
            return None
        
        folder_id = get_or_create_folder(service, folder_path, main_folder_id)
        if not folder_id:
            logger.error(f"No se pudo obtener/crear carpeta: {folder_path}")
            return None
        
        if not nombre_archivo:
            if hasattr(archivo_pdf, 'name'):
                nombre_archivo = archivo_pdf.name
            else:
                nombre_archivo = 'documento.pdf'
        
        nombre_limpio = ''.join(c for c in nombre_archivo if c.isalnum() or c in ' ._-')
        if not nombre_limpio:
            nombre_limpio = 'documento'
        
        if not nombre_limpio.lower().endswith('.pdf'):
            nombre_limpio += '.pdf'
        
        if hasattr(archivo_pdf, 'read'):
            contenido = archivo_pdf.read()
            archivo_pdf.seek(0)
        else:
            with open(archivo_pdf, 'rb') as f:
                contenido = f.read()
        
        if not contenido:
            logger.error("El archivo PDF esta vacio")
            return None
        
        media = MediaIoBaseUpload(
            io.BytesIO(contenido),
            mimetype='application/pdf',
            resumable=True,
            chunksize=1024 * 1024
        )
        
        file_metadata = {
            'name': nombre_limpio,
            'parents': [folder_id]
        }
        
        logger.info(f"Subiendo PDF a Google Drive: {nombre_limpio} ({len(contenido) / 1024:.1f} KB)")
        file = service.files().create(
            body=file_metadata,
            media_body=media,
            fields='id, webViewLink'
        ).execute()
        
        file_id = file.get('id')
        
        # ✅ HACER PÚBLICO EL PDF
        try:
            permission = {
                'type': 'anyone',
                'role': 'reader'
            }
            service.permissions().create(
                fileId=file_id,
                body=permission
            ).execute()
            logger.info(f"Permiso público otorgado a PDF: {file_id}")
        except Exception as e:
            logger.warning(f"No se pudo hacer público el PDF: {e}")
        
        preview_url = f"https://drive.google.com/file/d/{file_id}/preview"
        
        logger.info(f"PDF subido a Google Drive: {preview_url}")
        return preview_url
        
    except HttpError as e:
        logger.error(f"Error HTTP subiendo PDF: {e}")
        return None
    except Exception as e:
        logger.error(f"Error subiendo PDF: {str(e)}")
        return None


# ============================================
# SUBIDA DE PDF DESDE BYTES
# ============================================

def subir_pdf_a_drive_from_bytes(contenido_bytes, nombre_archivo, folder_path='Material_Biblioteca/Libros/PDFs'):
    """
    Sube un PDF a Google Drive desde bytes (sin archivo físico).
    Hace el PDF público para que se pueda ver en iframe.
    """
    try:
        service = get_drive_service()
        if not service:
            logger.error("No se pudo obtener servicio de Drive")
            return None
        
        main_folder_id = get_main_folder_id()
        if not main_folder_id:
            return None
        
        folder_id = get_or_create_folder(service, folder_path, main_folder_id)
        if not folder_id:
            logger.error(f"No se pudo obtener/crear carpeta: {folder_path}")
            return None
        
        nombre_limpio = ''.join(c for c in nombre_archivo if c.isalnum() or c in ' ._-')
        if not nombre_limpio:
            nombre_limpio = 'documento'
        if not nombre_limpio.lower().endswith('.pdf'):
            nombre_limpio += '.pdf'
        
        if not contenido_bytes:
            logger.error("El contenido del PDF esta vacio")
            return None
        
        media = MediaIoBaseUpload(
            io.BytesIO(contenido_bytes),
            mimetype='application/pdf',
            resumable=True,
            chunksize=1024 * 1024
        )
        
        file_metadata = {
            'name': nombre_limpio,
            'parents': [folder_id]
        }
        
        logger.info(f"Subiendo PDF: {nombre_limpio} ({len(contenido_bytes) / 1024:.1f} KB)")
        file = service.files().create(
            body=file_metadata,
            media_body=media,
            fields='id, webViewLink'
        ).execute()
        
        file_id = file.get('id')
        
        # ✅ HACER PÚBLICO EL PDF
        try:
            permission = {
                'type': 'anyone',
                'role': 'reader'
            }
            service.permissions().create(
                fileId=file_id,
                body=permission
            ).execute()
            logger.info(f"Permiso público otorgado a PDF: {file_id}")
        except Exception as e:
            logger.warning(f"No se pudo hacer público el PDF: {e}")
        
        preview_url = f"https://drive.google.com/file/d/{file_id}/preview"
        
        logger.info(f"PDF subido: {preview_url}")
        return preview_url
        
    except HttpError as e:
        logger.error(f"Error HTTP subiendo PDF: {e}")
        return None
    except Exception as e:
        logger.error(f"Error subiendo PDF: {str(e)}")
        return None

# ============================================
# SUBIDA DE IMAGEN DESDE BYTES
# ============================================

def subir_imagen_a_drive_from_bytes(contenido_bytes, nombre_archivo, folder_path='Material_Biblioteca/Libros/Portadas'):
    """
    Sube una imagen a Google Drive desde bytes (sin archivo físico).
    Hace la imagen pública para que se pueda mostrar en <img>.
    Usa lh3.googleusercontent.com para mostrar imágenes.
    """
    try:
        service = get_drive_service()
        if not service:
            logger.error("No se pudo obtener servicio de Drive")
            return None
        
        main_folder_id = get_main_folder_id()
        if not main_folder_id:
            return None
        
        folder_id = get_or_create_folder(service, folder_path, main_folder_id)
        if not folder_id:
            logger.error(f"No se pudo obtener/crear carpeta: {folder_path}")
            return None
        
        nombre_limpio = ''.join(c for c in nombre_archivo if c.isalnum() or c in ' ._-')
        if not nombre_limpio:
            nombre_limpio = 'imagen'
        
        ext = os.path.splitext(nombre_limpio)[1].lower()
        mime_types = {
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.png': 'image/png',
            '.gif': 'image/gif',
            '.webp': 'image/webp',
            '.bmp': 'image/bmp'
        }
        mime_type = mime_types.get(ext, 'image/jpeg')
        
        if not ext or ext not in mime_types:
            nombre_limpio += '.jpg'
        
        if not contenido_bytes:
            logger.error("El contenido de la imagen esta vacio")
            return None
        
        media = MediaIoBaseUpload(
            io.BytesIO(contenido_bytes),
            mimetype=mime_type,
            resumable=True,
            chunksize=1024 * 1024
        )
        
        file_metadata = {
            'name': nombre_limpio,
            'parents': [folder_id]
        }
        
        logger.info(f"Subiendo imagen: {nombre_limpio} ({len(contenido_bytes) / 1024:.1f} KB)")
        file = service.files().create(
            body=file_metadata,
            media_body=media,
            fields='id, webViewLink'
        ).execute()
        
        file_id = file.get('id')
        
        # ✅ HACER PÚBLICA LA IMAGEN (permiso: cualquiera con el enlace puede ver)
        try:
            permission = {
                'type': 'anyone',
                'role': 'reader'
            }
            service.permissions().create(
                fileId=file_id,
                body=permission
            ).execute()
            logger.info(f"Permiso público otorgado a imagen: {file_id}")
        except Exception as e:
            logger.warning(f"No se pudo hacer pública la imagen: {e}")
        
        # ✅ FORMATO QUE SÍ FUNCIONA EN <img>
        image_url = f"https://lh3.googleusercontent.com/d/{file_id}"
        
        logger.info(f"Imagen subida: {image_url}")
        return image_url
        
    except Exception as e:
        logger.error(f"Error subiendo imagen a Drive: {e}")
        return None


# ============================================
# SUBIDA DE IMAGEN (SINCRONA, ARCHIVO FISICO)
# ============================================

def subir_imagen_a_drive(archivo_imagen, nombre_archivo=None, folder_path='Material_Biblioteca/Libros/Portadas'):
    """
    Sube una imagen a Google Drive (versión síncrona).
    Hace la imagen pública para que se pueda mostrar en <img>.
    """
    try:
        service = get_drive_service()
        if not service:
            logger.error("No se pudo obtener servicio de Drive")
            return None
        
        main_folder_id = get_main_folder_id()
        if not main_folder_id:
            return None
        
        folder_id = get_or_create_folder(service, folder_path, main_folder_id)
        if not folder_id:
            logger.error(f"No se pudo obtener/crear carpeta: {folder_path}")
            return None
        
        if not nombre_archivo:
            if hasattr(archivo_imagen, 'name'):
                nombre_archivo = archivo_imagen.name
            else:
                nombre_archivo = 'imagen.jpg'
        
        nombre_limpio = ''.join(c for c in nombre_archivo if c.isalnum() or c in ' ._-')
        if not nombre_limpio:
            nombre_limpio = 'imagen'
        
        ext = os.path.splitext(nombre_limpio)[1].lower()
        mime_types = {
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.png': 'image/png',
            '.gif': 'image/gif',
            '.webp': 'image/webp',
            '.bmp': 'image/bmp',
            '.svg': 'image/svg+xml'
        }
        mime_type = mime_types.get(ext, 'image/jpeg')
        
        if not ext or ext not in mime_types:
            nombre_limpio += '.jpg'
        
        if hasattr(archivo_imagen, 'read'):
            contenido = archivo_imagen.read()
            archivo_imagen.seek(0)
        else:
            with open(archivo_imagen, 'rb') as f:
                contenido = f.read()
        
        if not contenido:
            logger.error("El archivo de imagen esta vacio")
            return None
        
        media = MediaIoBaseUpload(
            io.BytesIO(contenido),
            mimetype=mime_type,
            resumable=True,
            chunksize=1024 * 1024
        )
        
        file_metadata = {
            'name': nombre_limpio,
            'parents': [folder_id]
        }
        
        logger.info(f"Subiendo imagen a Google Drive: {nombre_limpio} ({len(contenido) / 1024:.1f} KB)")
        file = service.files().create(
            body=file_metadata,
            media_body=media,
            fields='id, webViewLink'
        ).execute()
        
        file_id = file.get('id')
        
        # ✅ HACER PÚBLICA LA IMAGEN
        try:
            permission = {
                'type': 'anyone',
                'role': 'reader'
            }
            service.permissions().create(
                fileId=file_id,
                body=permission
            ).execute()
            logger.info(f"Permiso público otorgado a imagen: {file_id}")
        except Exception as e:
            logger.warning(f"No se pudo hacer pública la imagen: {e}")
        
        # ✅ FORMATO QUE SÍ FUNCIONA EN <img>
        image_url = f"https://lh3.googleusercontent.com/d/{file_id}"
        
        logger.info(f"Imagen subida a Google Drive: {image_url}")
        return image_url
        
    except Exception as e:
        logger.error(f"Error subiendo imagen a Drive: {e}")
        return None

# ============================================
# FUNCIONES ASÍNCRONAS (LEEN ANTES DE CREAR HILO)
# ============================================

def subir_pdf_a_drive_async(pdf_original, nombre_archivo, libro_id, folder_path='Material_Biblioteca/Libros/PDFs', campo='google_drive_url'):
    """Sube un PDF a Google Drive en segundo plano"""
    try:
        if hasattr(pdf_original, 'read'):
            contenido_bytes = pdf_original.read()
            pdf_original.seek(0)
        else:
            with open(pdf_original, 'rb') as f:
                contenido_bytes = f.read()
    except Exception as e:
        logger.error(f"Error leyendo PDF antes de subir: {e}")
        return None

    def upload_thread():
        try:
            Libro = apps.get_model('biblioartdis', 'Libro')
            
            drive_url = subir_pdf_a_drive_from_bytes(contenido_bytes, nombre_archivo, folder_path)
            
            if drive_url:
                libro = Libro.objects.get(id_libro=libro_id)
                setattr(libro, campo, drive_url)
                libro.save(update_fields=[campo])
                logger.info(f"PDF subido a Google Drive: {drive_url} (Libro ID: {libro_id})")
            else:
                logger.error(f"Fallo subida a Drive para libro {libro_id}")
        except Exception as e:
            logger.error(f"Error en subida asincrona de PDF: {str(e)}")
    
    thread = threading.Thread(target=upload_thread, daemon=True)
    thread.start()
    return thread


def subir_portada_a_drive_async(imagen_original, nombre_archivo, libro_id, folder_path='Material_Biblioteca/Libros/Portadas'):
    """Sube una portada a Google Drive en segundo plano"""
    try:
        contenido_bytes = imagen_original.read()
        imagen_original.seek(0)
        nombre_original = imagen_original.name if hasattr(imagen_original, 'name') else 'portada.jpg'
    except Exception as e:
        logger.error(f"Error leyendo portada antes de subir: {e}")
        return None

    def upload_thread():
        try:
            Libro = apps.get_model('biblioartdis', 'Libro')
            
            drive_url = subir_imagen_a_drive_from_bytes(contenido_bytes, nombre_original, folder_path)
            
            if drive_url:
                libro = Libro.objects.get(id_libro=libro_id)
                libro.google_drive_portada_url = drive_url
                libro.save(update_fields=['google_drive_portada_url'])
                logger.info(f"Portada subida a Google Drive: {drive_url} (Libro ID: {libro_id})")
            else:
                logger.error(f"Fallo subida de portada para libro {libro_id}")
        except Exception as e:
            logger.error(f"Error en subida asincrona de portada: {str(e)}")
    
    thread = threading.Thread(target=upload_thread, daemon=True)
    thread.start()
    return thread


def subir_autorizacion_a_drive_async(archivo, nombre_archivo, libro_id, folder_path='Material_Biblioteca/Autorizaciones'):
    """Sube una autorizacion a Google Drive en segundo plano"""
    try:
        contenido_bytes = archivo.read()
        archivo.seek(0)
        nombre_original = archivo.name if hasattr(archivo, 'name') else f'{nombre_archivo}.pdf'
    except Exception as e:
        logger.error(f"Error leyendo autorizacion antes de subir: {e}")
        return None

    def upload_thread():
        try:
            Libro = apps.get_model('biblioartdis', 'Libro')
            
            drive_url = subir_pdf_a_drive_from_bytes(contenido_bytes, nombre_original, folder_path)
            
            if drive_url:
                libro = Libro.objects.get(id_libro=libro_id)
                libro.google_drive_autorizacion_url = drive_url
                libro.save(update_fields=['google_drive_autorizacion_url'])
                logger.info(f"Autorizacion subida a Google Drive: {drive_url} (Libro ID: {libro_id})")
            else:
                logger.error(f"Fallo subida de autorizacion para libro {libro_id}")
        except Exception as e:
            logger.error(f"Error en subida asincrona de autorizacion: {str(e)}")
    
    thread = threading.Thread(target=upload_thread, daemon=True)
    thread.start()
    return thread


def subir_imagen_a_drive_async(imagen_original, nombre_archivo, imagen_id, folder_path='Material_Biblioteca/Imagenes/Obras'):
    """Sube una imagen de la galeria a Google Drive en segundo plano"""
    try:
        contenido_bytes = imagen_original.read()
        imagen_original.seek(0)
        nombre_original = imagen_original.name if hasattr(imagen_original, 'name') else nombre_archivo
    except Exception as e:
        logger.error(f"Error leyendo imagen antes de subir: {e}")
        return None

    def upload_thread():
        try:
            Imagen = apps.get_model('biblioartdis', 'Imagen')
            
            drive_url = subir_imagen_a_drive_from_bytes(contenido_bytes, nombre_original, folder_path)
            
            if drive_url:
                imagen = Imagen.objects.get(id_Imagen=imagen_id)
                if hasattr(imagen, 'google_drive_url'):
                    imagen.google_drive_url = drive_url
                imagen.save()
                logger.info(f"Imagen subida a Google Drive: {drive_url} (Imagen ID: {imagen_id})")
            else:
                logger.error(f"Fallo subida de imagen para ID {imagen_id}")
        except Exception as e:
            logger.error(f"Error en subida asincrona de imagen: {str(e)}")
    
    thread = threading.Thread(target=upload_thread, daemon=True)
    thread.start()
    return thread


def subir_revista_pdf_a_drive_async(pdf_original, nombre_archivo, revista_id, folder_path='Material_Biblioteca/Revistas/PDFs'):
    """Sube un PDF de revista a Google Drive en segundo plano"""
    try:
        contenido_bytes = pdf_original.read()
        pdf_original.seek(0)
        nombre_original = pdf_original.name if hasattr(pdf_original, 'name') else f'{nombre_archivo}.pdf'
    except Exception as e:
        logger.error(f"Error leyendo PDF de revista antes de subir: {e}")
        return None

    def upload_thread():
        try:
            Revista = apps.get_model('biblioartdis', 'Revista')
            
            drive_url = subir_pdf_a_drive_from_bytes(contenido_bytes, nombre_original, folder_path)
            
            if drive_url:
                revista = Revista.objects.get(id_revista=revista_id)
                revista.google_drive_url = drive_url
                revista.save(update_fields=['google_drive_url'])
                logger.info(f"PDF de revista subido a Google Drive: {drive_url} (Revista ID: {revista_id})")
            else:
                logger.error(f"Fallo subida a Drive para revista {revista_id}")
        except Exception as e:
            logger.error(f"Error en subida de revista a Drive: {str(e)}")
    
    thread = threading.Thread(target=upload_thread, daemon=True)
    thread.start()
    return thread


def subir_imagen_revista_a_drive_async(imagen_original, nombre_archivo, revista_id, folder_path='Material_Biblioteca/Revistas/Portadas'):
    """Sube una portada de revista a Google Drive en segundo plano"""
    try:
        contenido_bytes = imagen_original.read()
        imagen_original.seek(0)
        nombre_original = imagen_original.name if hasattr(imagen_original, 'name') else f'{nombre_archivo}.jpg'
    except Exception as e:
        logger.error(f"Error leyendo imagen de revista antes de subir: {e}")
        return None

    def upload_thread():
        try:
            Revista = apps.get_model('biblioartdis', 'Revista')
            
            drive_url = subir_imagen_a_drive_from_bytes(contenido_bytes, nombre_original, folder_path)
            
            if drive_url:
                revista = Revista.objects.get(id_revista=revista_id)
                revista.google_drive_img_url = drive_url
                revista.save(update_fields=['google_drive_img_url'])
                logger.info(f"Imagen de revista subida a Google Drive: {drive_url} (Revista ID: {revista_id})")
            else:
                logger.error(f"Fallo subida de imagen para revista {revista_id}")
        except Exception as e:
            logger.error(f"Error en subida de imagen de revista a Drive: {str(e)}")
    
    thread = threading.Thread(target=upload_thread, daemon=True)
    thread.start()
    return thread


# ============================================
# ELIMINAR ARCHIVOS
# ============================================

def eliminar_pdf_de_drive(file_id):
    """Elimina un archivo de Google Drive por su ID"""
    if not file_id:
        logger.warning("No se proporciono file_id para eliminar")
        return False
        
    try:
        service = get_drive_service()
        if not service:
            logger.error("No se pudo obtener servicio de Drive")
            return False
        
        service.files().delete(fileId=file_id).execute()
        logger.info(f"Archivo de Drive eliminado: {file_id}")
        return True
        
    except HttpError as e:
        if e.resp.status == 404:
            logger.warning(f"Archivo no encontrado en Drive: {file_id}")
            return True
        logger.error(f"Error HTTP eliminando archivo de Drive: {e}")
        return False
    except Exception as e:
        logger.error(f"Error eliminando archivo de Drive: {e}")
        return False


def eliminar_imagen_de_drive(file_id):
    """Elimina una imagen de Google Drive por su ID"""
    return eliminar_pdf_de_drive(file_id)


# ============================================
# TEST
# ============================================

def test_drive_connection():
    """Prueba la conexion con Google Drive"""
    print("=" * 50)
    print("Probando conexion con Google Drive...")
    print("=" * 50)
    
    service = get_drive_service()
    if not service:
        print("No se pudo conectar a Google Drive")
        return False
    
    try:
        about = service.about().get(fields="storageQuota").execute()
        storage = about.get('storageQuota', {})
        used = int(storage.get('usage', 0)) / (1024**3)
        total = int(storage.get('limit', 0)) / (1024**3)
        
        print(f"Conexion a Drive exitosa")
        print(f"   Espacio usado: {used:.2f} GB")
        print(f"   Espacio total: {total:.2f} GB")
        print(f"   Disponible: {total - used:.2f} GB")
        
        folder_id = get_main_folder_id()
        if folder_id:
            try:
                folder = service.files().get(fileId=folder_id).execute()
                print(f"   Folder configurado: {folder.get('name')}")
                print(f"   Folder ID: {folder_id}")
            except Exception as e:
                print(f"   No se pudo verificar el folder: {e}")
        else:
            print("   GOOGLE_DRIVE_FOLDER_ID no configurada")
        
        return True
        
    except Exception as e:
        print(f"Error en prueba: {e}")
        return False