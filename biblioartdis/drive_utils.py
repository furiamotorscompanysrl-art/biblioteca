# biblioartdis/drive_utils.py
import os
import io
import json
import base64
import pickle
import logging
import tempfile
import threading
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload, MediaFileUpload
from googleapiclient.errors import HttpError
from django.conf import settings

logger = logging.getLogger(__name__)


def get_drive_service():
    """
    Obtiene el servicio de Google Drive autenticado con OAuth
    Usa las mismas variables que el google_drive_utils.py
    """
    try:
        # ============================================
        # PRIMERO: Intentar con las variables OAuth estándar
        # ============================================
        creds_json = os.environ.get('GOOGLE_DRIVE_OAUTH_CREDENTIALS')
        token_json = os.environ.get('GOOGLE_DRIVE_TOKEN')
        
        if creds_json and token_json:
            try:
                # Cargar token
                token_data = json.loads(token_json)
                
                credentials = Credentials(
                    token=token_data.get('token'),
                    refresh_token=token_data.get('refresh_token'),
                    token_uri=token_data.get('token_uri', 'https://oauth2.googleapis.com/token'),
                    client_id=token_data.get('client_id'),
                    client_secret=token_data.get('client_secret'),
                    scopes=token_data.get('scopes', ['https://www.googleapis.com/auth/drive.file'])
                )
                
                # Verificar si expiró
                if credentials.expired and credentials.refresh_token:
                    logger.info("🔄 Refrescando token de Drive...")
                    credentials.refresh(Request())
                    logger.info("✅ Token de Drive refrescado")
                
                service = build('drive', 'v3', credentials=credentials)
                logger.info("✅ Servicio Google Drive inicializado (OAuth estándar)")
                return service
                
            except Exception as e:
                logger.warning(f"⚠️ Error con OAuth estándar: {e}")
        
        # ============================================
        # SEGUNDO: Intentar con formato base64 (compatibilidad)
        # ============================================
        token_base64 = os.environ.get('DRIVE_TOKEN_BASE64')
        creds_base64 = os.environ.get('DRIVE_CREDENTIALS_BASE64')
        
        if token_base64 and creds_base64:
            try:
                token_data = base64.b64decode(token_base64)
                creds = pickle.loads(token_data)
                
                if creds.expired and creds.refresh_token:
                    logger.info("🔄 Refrescando token de Drive (base64)...")
                    creds.refresh(Request())
                
                service = build('drive', 'v3', credentials=creds)
                logger.info("✅ Servicio Google Drive inicializado (base64)")
                return service
                
            except Exception as e:
                logger.warning(f"⚠️ Error con base64: {e}")
        
        # ============================================
        # TERCERO: Intentar con google_drive_utils (compatibilidad)
        # ============================================
        try:
            from .google_drive_utils import drive_service
            if drive_service and drive_service.service:
                logger.info("✅ Servicio Google Drive desde google_drive_utils")
                return drive_service.service
        except Exception as e:
            logger.warning(f"⚠️ Error usando google_drive_utils: {e}")
        
        logger.error("❌ No se encontraron credenciales válidas de Drive")
        return None
        
    except Exception as e:
        logger.error(f"❌ Error obteniendo servicio Drive: {e}")
        return None


def get_or_create_folder(service, folder_path, parent_folder_id=None):
    """
    Obtiene o crea una carpeta en Google Drive por ruta
    
    Args:
        service: Servicio de Google Drive
        folder_path: Ruta de la carpeta (ej: 'Material_Biblioteca/Libros/PDFs')
        parent_folder_id: ID de la carpeta padre (opcional)
    
    Returns:
        str: ID de la carpeta o None si falla
    """
    try:
        if not service:
            logger.error("❌ Servicio de Drive no disponible")
            return None
        
        parts = folder_path.split('/')
        current_parent = parent_folder_id
        
        for part in parts:
            # Buscar si la carpeta existe
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
                logger.info(f"✅ Carpeta encontrada: {part} (ID: {current_parent})")
            else:
                # Crear carpeta
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
                logger.info(f"✅ Carpeta creada: {part} (ID: {current_parent})")
        
        return current_parent
        
    except HttpError as e:
        logger.error(f"❌ Error HTTP con carpeta {folder_path}: {e}")
        return None
    except Exception as e:
        logger.error(f"❌ Error con carpeta {folder_path}: {e}")
        return None


def subir_pdf_a_drive(archivo_pdf, nombre_archivo=None, folder_path='Material_Biblioteca/Libros/PDFs'):
    """
    Sube un PDF a Google Drive usando OAuth
    
    Args:
        archivo_pdf: Archivo subido (InMemoryUploadedFile) o ruta de archivo
        nombre_archivo: Nombre para guardar en Drive (opcional)
        folder_path: Ruta de la carpeta en Drive (por defecto: Material_Biblioteca/Libros/PDFs)
    
    Returns:
        str: URL de vista previa o None si falla
    """
    try:
        service = get_drive_service()
        if not service:
            logger.error("❌ No se pudo obtener servicio de Drive")
            return None
        
        # Obtener folder principal
        main_folder_id = os.environ.get('GOOGLE_DRIVE_FOLDER_ID')
        if not main_folder_id:
            logger.error("❌ GOOGLE_DRIVE_FOLDER_ID no configurada")
            return None
        
        # Obtener o crear la carpeta
        folder_id = get_or_create_folder(service, folder_path, main_folder_id)
        if not folder_id:
            logger.error(f"❌ No se pudo obtener/crear carpeta: {folder_path}")
            return None
        
        # Nombre del archivo
        if not nombre_archivo:
            if hasattr(archivo_pdf, 'name'):
                nombre_archivo = archivo_pdf.name
            else:
                nombre_archivo = 'documento.pdf'
        
        # Limpiar nombre (solo caracteres alfanuméricos, espacios, guiones y puntos)
        nombre_limpio = ''.join(c for c in nombre_archivo if c.isalnum() or c in ' ._-')
        if not nombre_limpio:
            nombre_limpio = 'documento'
        
        # Asegurar extensión .pdf
        if not nombre_limpio.lower().endswith('.pdf'):
            nombre_limpio += '.pdf'
        
        # Leer el contenido del archivo
        if hasattr(archivo_pdf, 'read'):
            # Es un archivo subido (InMemoryUploadedFile)
            contenido = archivo_pdf.read()
            archivo_pdf.seek(0)
        else:
            # Es una ruta de archivo
            with open(archivo_pdf, 'rb') as f:
                contenido = f.read()
        
        # Verificar que no esté vacío
        if not contenido:
            logger.error("❌ El archivo PDF está vacío")
            return None
        
        # Verificar que sea un PDF (mínimo validación)
        if not contenido.startswith(b'%PDF'):
            logger.warning(f"⚠️ El archivo no parece ser un PDF válido: {nombre_limpio}")
            # Intentamos subir de todas formas
        
        # Subir a Google Drive
        media = MediaIoBaseUpload(
            io.BytesIO(contenido),
            mimetype='application/pdf',
            resumable=True,
            chunksize=1024 * 1024  # 1MB chunks
        )
        
        file_metadata = {
            'name': nombre_limpio,
            'parents': [folder_id]
        }
        
        logger.info(f"📤 Subiendo PDF a Google Drive: {nombre_limpio} ({len(contenido) / 1024:.1f} KB)")
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


def subir_pdf_a_drive_async(pdf_original, nombre_archivo, libro_id, folder_path='Material_Biblioteca/Libros/PDFs'):
    """
    Sube un PDF a Google Drive en segundo plano
    
    Args:
        pdf_original: Archivo subido (InMemoryUploadedFile)
        nombre_archivo: Nombre del archivo
        libro_id: ID del libro para actualizar
        folder_path: Ruta de la carpeta en Drive
    """
    def upload_thread():
        try:
            from ..models import Libro
            
            # Subir a Drive
            drive_url = subir_pdf_a_drive(pdf_original, nombre_archivo, folder_path)
            
            if drive_url:
                # Actualizar el libro con la URL de Drive
                libro = Libro.objects.get(id_libro=libro_id)
                libro.google_drive_url = drive_url
                libro.pdf = None  # Liberar espacio en Cloudinary
                libro.save(update_fields=['google_drive_url', 'pdf'])
                logger.info(f"✅ PDF subido asíncronamente a Google Drive: {drive_url} (Libro ID: {libro_id})")
            else:
                logger.error(f"❌ Falló subida asíncrona a Drive para libro {libro_id}")
        except Libro.DoesNotExist:
            logger.error(f"❌ Libro {libro_id} no encontrado para actualizar URL de Drive")
        except Exception as e:
            logger.error(f"❌ Error en subida asíncrona a Drive: {str(e)}")
    
    thread = threading.Thread(target=upload_thread)
    thread.daemon = True
    thread.start()
    return thread


def eliminar_pdf_de_drive(file_id):
    """
    Elimina un archivo de Google Drive por su ID
    
    Args:
        file_id: ID del archivo en Google Drive
    
    Returns:
        bool: True si se eliminó correctamente
    """
    try:
        service = get_drive_service()
        if not service:
            logger.error("❌ No se pudo obtener servicio de Drive")
            return False
        
        service.files().delete(fileId=file_id).execute()
        logger.info(f"✅ Archivo de Drive eliminado: {file_id}")
        return True
        
    except HttpError as e:
        if e.resp.status == 404:
            logger.warning(f"⚠️ Archivo no encontrado en Drive: {file_id}")
            return True  # Ya no existe
        logger.error(f"❌ Error HTTP eliminando archivo de Drive: {e}")
        return False
    except Exception as e:
        logger.error(f"❌ Error eliminando archivo de Drive: {e}")
        return False


def test_drive_connection():
    """
    Prueba la conexión con Google Drive y muestra información de espacio
    """
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
        
        # Verificar folder principal
        folder_id = os.environ.get('GOOGLE_DRIVE_FOLDER_ID')
        if folder_id:
            try:
                folder = service.files().get(fileId=folder_id).execute()
                print(f"   📂 Folder configurado: {folder.get('name')}")
                print(f"   📂 Folder ID: {folder_id}")
            except HttpError as e:
                if e.resp.status == 404:
                    print(f"   ❌ Folder no encontrado: {folder_id}")
                else:
                    print(f"   ⚠️ No se pudo verificar el folder: {e}")
            except Exception as e:
                print(f"   ⚠️ No se pudo verificar el folder: {e}")
        else:
            print("   ⚠️ GOOGLE_DRIVE_FOLDER_ID no configurada")
        
        return True
        
    except Exception as e:
        print(f"❌ Error en prueba: {e}")
        return False


# ============================================
# FUNCIÓN PARA SUBIR REVISTAS A DRIVE
# ============================================
def subir_revista_a_drive(archivo_pdf, nombre_archivo=None):
    """
    Sube una revista a Google Drive en la carpeta de Revistas/PDFs
    """
    return subir_pdf_a_drive(
        archivo_pdf, 
        nombre_archivo, 
        folder_path='Material_Biblioteca/Revistas/PDFs'
    )


# ============================================
# FUNCIÓN PARA SUBIR IMÁGENES A DRIVE
# ============================================
def subir_imagen_a_drive(archivo_imagen, nombre_archivo=None):
    """
    Sube una imagen a Google Drive en la carpeta de Imagenes/Obras
    """
    try:
        service = get_drive_service()
        if not service:
            logger.error("❌ No se pudo obtener servicio de Drive")
            return None
        
        # Obtener folder principal
        main_folder_id = os.environ.get('GOOGLE_DRIVE_FOLDER_ID')
        if not main_folder_id:
            logger.error("❌ GOOGLE_DRIVE_FOLDER_ID no configurada")
            return None
        
        # Obtener o crear la carpeta
        folder_id = get_or_create_folder(service, 'Material_Biblioteca/Imagenes/Obras', main_folder_id)
        if not folder_id:
            logger.error("❌ No se pudo obtener/crear carpeta para imágenes")
            return None
        
        # Nombre del archivo
        if not nombre_archivo:
            if hasattr(archivo_imagen, 'name'):
                nombre_archivo = archivo_imagen.name
            else:
                nombre_archivo = 'imagen'
        
        # Limpiar nombre
        nombre_limpio = ''.join(c for c in nombre_archivo if c.isalnum() or c in ' ._-')
        if not nombre_limpio:
            nombre_limpio = 'imagen'
        
        # Leer el contenido
        if hasattr(archivo_imagen, 'read'):
            contenido = archivo_imagen.read()
            archivo_imagen.seek(0)
        else:
            with open(archivo_imagen, 'rb') as f:
                contenido = f.read()
        
        if not contenido:
            logger.error("❌ El archivo de imagen está vacío")
            return None
        
        # Detectar MIME type por extensión
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
        
        # Subir a Google Drive
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
        
        logger.info(f"📤 Subiendo imagen a Google Drive: {nombre_limpio}")
        file = service.files().create(
            body=file_metadata,
            media_body=media,
            fields='id, webViewLink'
        ).execute()
        
        file_id = file.get('id')
        preview_url = f"https://drive.google.com/file/d/{file_id}/preview"
        
        logger.info(f"✅ Imagen subida a Google Drive: {preview_url}")
        return preview_url
        
    except Exception as e:
        logger.error(f"❌ Error subiendo imagen a Drive: {e}")
        return None

# biblioartdis/drive_utils.py

# biblioartdis/drive_utils.py

def subir_imagen_a_drive_async(imagen_original, nombre_archivo, imagen_id, folder_path='Material_Biblioteca/Imagenes/Obras'):
    """
    Sube una imagen a Google Drive en segundo plano
    
    Args:
        imagen_original: Archivo subido (InMemoryUploadedFile)
        nombre_archivo: Nombre del archivo
        imagen_id: ID de la imagen para actualizar
        folder_path: Ruta de la carpeta en Drive
    """
    import threading
    
    def upload_thread():
        try:
            from ..models import Imagen
            
            # Subir a Drive
            drive_url = subir_imagen_a_drive(imagen_original, nombre_archivo, folder_path)
            
            if drive_url:
                # Actualizar la imagen con la URL de Drive
                imagen = Imagen.objects.get(id_Imagen=imagen_id)
                if hasattr(imagen, 'google_drive_url'):
                    imagen.google_drive_url = drive_url
                # Limpiar la imagen de Cloudinary (opcional, para ahorrar espacio)
                # if imagen.img_portada:
                #     try:
                #         imagen.img_portada.delete(save=False)
                #     except Exception as e:
                #         logger.warning(f"⚠️ No se pudo eliminar imagen de Cloudinary: {e}")
                #     imagen.img_portada = None
                imagen.save()
                logger.info(f"✅ Imagen subida a Google Drive: {drive_url} (Imagen ID: {imagen_id})")
            else:
                logger.error(f"❌ Falló subida a Drive para imagen {imagen_id}")
                # Fallback: mantener en Cloudinary
                
        except Imagen.DoesNotExist:
            logger.error(f"❌ Imagen {imagen_id} no encontrada")
        except Exception as e:
            logger.error(f"❌ Error en subida de imagen a Drive: {str(e)}")
    
    thread = threading.Thread(target=upload_thread)
    thread.daemon = True
    thread.start()
    return thread
    
def subir_imagen_a_drive(archivo_imagen, nombre_archivo=None, folder_path='Material_Biblioteca/Imagenes/Obras'):
    """
    Sube una imagen a Google Drive
    
    Args:
        archivo_imagen: Archivo subido (InMemoryUploadedFile) o ruta de archivo
        nombre_archivo: Nombre para guardar en Drive (opcional)
        folder_path: Ruta de la carpeta en Drive (por defecto: Material_Biblioteca/Imagenes/Obras)
    
    Returns:
        str: URL de vista previa o None si falla
    """
    try:
        service = get_drive_service()
        if not service:
            logger.error("❌ No se pudo obtener servicio de Drive")
            return None
        
        # Obtener folder principal
        main_folder_id = os.environ.get('GOOGLE_DRIVE_FOLDER_ID')
        if not main_folder_id:
            logger.error("❌ GOOGLE_DRIVE_FOLDER_ID no configurada")
            return None
        
        # Obtener o crear la carpeta
        folder_id = get_or_create_folder(service, folder_path, main_folder_id)
        if not folder_id:
            logger.error(f"❌ No se pudo obtener/crear carpeta: {folder_path}")
            return None
        
        # Nombre del archivo
        if not nombre_archivo:
            if hasattr(archivo_imagen, 'name'):
                nombre_archivo = archivo_imagen.name
            else:
                nombre_archivo = 'imagen.jpg'
        
        # Limpiar nombre
        nombre_limpio = ''.join(c for c in nombre_archivo if c.isalnum() or c in ' ._-')
        if not nombre_limpio:
            nombre_limpio = 'imagen'
        
        # Detectar MIME type por extensión
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
        
        # Asegurar extensión
        if not ext or ext not in mime_types:
            nombre_limpio += '.jpg'
        
        # Leer el contenido del archivo
        if hasattr(archivo_imagen, 'read'):
            contenido = archivo_imagen.read()
            archivo_imagen.seek(0)
        else:
            with open(archivo_imagen, 'rb') as f:
                contenido = f.read()
        
        if not contenido:
            logger.error("❌ El archivo de imagen está vacío")
            return None
        
        # Subir a Google Drive
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
        
        logger.info(f"📤 Subiendo imagen a Google Drive: {nombre_limpio} ({len(contenido) / 1024:.1f} KB)")
        file = service.files().create(
            body=file_metadata,
            media_body=media,
            fields='id, webViewLink'
        ).execute()
        
        file_id = file.get('id')
        preview_url = f"https://drive.google.com/file/d/{file_id}/preview"
        
        logger.info(f"✅ Imagen subida a Google Drive: {preview_url}")
        return preview_url
        
    except Exception as e:
        logger.error(f"❌ Error subiendo imagen a Drive: {e}")
        return None