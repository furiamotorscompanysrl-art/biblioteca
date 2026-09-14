# biblioartdis/google_drive_utils.py
import os
import logging
import json
from google.oauth2.credentials import Credentials
from google.oauth2 import service_account
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload, MediaIoBaseDownload
from django.conf import settings
import io

logger = logging.getLogger(__name__)

SCOPES = ['https://www.googleapis.com/auth/drive.file']


class GoogleDriveService:
    """
    Servicio para interactuar con Google Drive.
    ✅ PRIORIZA OAuth (usuario real) porque las cuentas de servicio ya no tienen cuota.
    ✅ Fallback a Cuenta de Servicio si OAuth no está disponible (solo lectura).
    """
    
    def __init__(self):
        self.service = None
        self.credentials = None
        self.tipo_auth = None
        self._authenticate()
    
    def _authenticate(self):
        """
        Autentica con Google Drive.
        1º OAuth (usuario real) - TIENE CUOTA
        2º Cuenta de Servicio - NO TIENE CUOTA (solo lectura)
        """
        # ============================================
        # PRIMERO: OAuth con usuario real
        # ============================================
        try:
            creds_json = os.environ.get('GOOGLE_DRIVE_OAUTH_CREDENTIALS')
            token_json = os.environ.get('GOOGLE_DRIVE_TOKEN')
            
            if creds_json and token_json:
                token_data = json.loads(token_json)
                
                self.credentials = Credentials(
                    token=token_data.get('token'),
                    refresh_token=token_data.get('refresh_token'),
                    token_uri=token_data.get('token_uri', 'https://oauth2.googleapis.com/token'),
                    client_id=token_data.get('client_id'),
                    client_secret=token_data.get('client_secret'),
                    scopes=token_data.get('scopes', SCOPES)
                )
                
                if self.credentials.expired and self.credentials.refresh_token:
                    logger.info("🔄 Refrescando token OAuth...")
                    self.credentials.refresh(Request())
                    logger.info("✅ Token OAuth refrescado")
                
                self.service = build('drive', 'v3', credentials=self.credentials)
                self.tipo_auth = 'oauth'
                logger.info("✅ Autenticación con OAuth (usuario real) exitosa - TIENE CUOTA")
                return
        except Exception as e:
            logger.warning(f"⚠️ Error con OAuth: {e}")
        
        # ============================================
        # SEGUNDO: Cuenta de Servicio (fallback)
        # ============================================
        try:
            creds_json = os.environ.get('GOOGLE_APPLICATION_CREDENTIALS_JSON')
            
            if creds_json:
                creds_dict = json.loads(creds_json)
                
                credentials = service_account.Credentials.from_service_account_info(
                    creds_dict,
                    scopes=SCOPES
                )
                
                self.service = build('drive', 'v3', credentials=credentials)
                self.tipo_auth = 'service_account'
                logger.warning("⚠️ Autenticación con Cuenta de Servicio - NO TIENE CUOTA")
                logger.warning(f"📧 Cuenta: {creds_dict.get('client_email')}")
                return
        except Exception as e:
            logger.warning(f"⚠️ Error con Cuenta de Servicio: {e}")
        
        logger.error("❌ No se encontraron credenciales válidas de Drive")
        raise Exception("Sin credenciales de Google Drive")
    
    def get_or_create_folder(self, folder_path, parent_folder_id=None):
        """Obtener o crear una carpeta por ruta"""
        try:
            parts = folder_path.split('/')
            current_parent = parent_folder_id
            
            for part in parts:
                query = f"name='{part}' and mimeType='application/vnd.google-apps.folder' and trashed=false"
                if current_parent:
                    query += f" and '{current_parent}' in parents"
                
                results = self.service.files().list(
                    q=query,
                    spaces='drive',
                    fields='files(id, name)',
                    supportsAllDrives=True,
                    includeItemsFromAllDrives=True
                ).execute()
                
                files = results.get('files', [])
                
                if files:
                    current_parent = files[0].get('id')
                    logger.info(f"📁 Carpeta encontrada: {part} (ID: {current_parent})")
                else:
                    file_metadata = {
                        'name': part,
                        'mimeType': 'application/vnd.google-apps.folder'
                    }
                    if current_parent:
                        file_metadata['parents'] = [current_parent]
                    
                    folder = self.service.files().create(
                        body=file_metadata,
                        fields='id',
                        supportsAllDrives=True
                    ).execute()
                    
                    current_parent = folder.get('id')
                    logger.info(f"📁 Carpeta creada: {part} (ID: {current_parent})")
            
            return current_parent
            
        except Exception as e:
            logger.error(f"❌ Error con carpeta {folder_path}: {e}")
            return None
    
    def upload_file(self, file_path, file_name, folder_id, mime_type=None):
        """Subir archivo a Google Drive"""
        try:
            if not mime_type:
                ext = os.path.splitext(file_name)[1].lower()
                mime_types = {
                    '.pdf': 'application/pdf',
                    '.jpg': 'image/jpeg',
                    '.jpeg': 'image/jpeg',
                    '.png': 'image/png',
                    '.gif': 'image/gif',
                    '.doc': 'application/msword',
                    '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
                    '.xls': 'application/vnd.ms-excel',
                    '.xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                    '.txt': 'text/plain',
                    '.zip': 'application/zip',
                    '.rar': 'application/x-rar-compressed'
                }
                mime_type = mime_types.get(ext, 'application/octet-stream')
            
            file_metadata = {
                'name': file_name,
                'parents': [folder_id]
            }
            
            media = MediaFileUpload(
                file_path,
                mimetype=mime_type,
                resumable=True,
                chunksize=1024 * 1024
            )
            
            logger.info(f"📤 Subiendo archivo: {file_name} ({mime_type})")
            file = self.service.files().create(
                body=file_metadata,
                media_body=media,
                fields='id, webViewLink, size',
                supportsAllDrives=True
            ).execute()
            
            file_id = file.get('id')
            web_link = file.get('webViewLink')
            size = file.get('size', 'desconocido')
            
            logger.info(f"✅ Archivo subido: {file_name} (ID: {file_id}, Tamaño: {size} bytes)")
            
            return {
                'file_id': file_id,
                'web_link': web_link,
                'download_link': f"https://drive.google.com/uc?id={file_id}&export=download"
            }
            
        except Exception as e:
            logger.error(f"❌ Error subiendo archivo {file_name}: {e}")
            return None
    
    def delete_file(self, file_id):
        """Eliminar archivo de Google Drive"""
        try:
            if not file_id:
                logger.warning("⚠️ No se proporcionó file_id para eliminar")
                return False
            
            self.service.files().delete(
                fileId=file_id,
                supportsAllDrives=True
            ).execute()
            logger.info(f"✅ Archivo eliminado: {file_id}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error eliminando archivo {file_id}: {e}")
            return False
    
    def get_file_metadata(self, file_id):
        """Obtener metadatos de un archivo"""
        try:
            file = self.service.files().get(
                fileId=file_id,
                fields='id, name, mimeType, size, webViewLink, createdTime, modifiedTime',
                supportsAllDrives=True
            ).execute()
            
            return {
                'id': file.get('id'),
                'name': file.get('name'),
                'mime_type': file.get('mimeType'),
                'size': file.get('size'),
                'web_link': file.get('webViewLink'),
                'created': file.get('createdTime'),
                'modified': file.get('modifiedTime')
            }
            
        except Exception as e:
            logger.error(f"❌ Error obteniendo metadatos de {file_id}: {e}")
            return None
    
    def list_files_in_folder(self, folder_id, max_results=100):
        """Listar archivos en una carpeta"""
        try:
            query = f"'{folder_id}' in parents and trashed=false"
            
            results = self.service.files().list(
                q=query,
                pageSize=max_results,
                fields='files(id, name, mimeType, size, webViewLink, createdTime)',
                supportsAllDrives=True,
                includeItemsFromAllDrives=True
            ).execute()
            
            files = results.get('files', [])
            logger.info(f"📂 Encontrados {len(files)} archivos en carpeta {folder_id}")
            
            return files
            
        except Exception as e:
            logger.error(f"❌ Error listando archivos en {folder_id}: {e}")
            return []
    
    def create_initial_structure(self, main_folder_name='Biblioteca_Artes_Diseno'):
        """Crear toda la estructura de carpetas para la biblioteca"""
        try:
            main_folder = self.get_or_create_folder(main_folder_name)
            
            if not main_folder:
                logger.error("❌ No se pudo crear la carpeta principal")
                return None
            
            logger.info(f"📁 Carpeta principal: {main_folder_name} (ID: {main_folder})")
            
            folders = {
                'Documentos_Usuarios': [
                    'Carnets_Frente',
                    'Carnets_Reverso',
                    'Matriculas_PDF',
                    'Fotos_Perfil'
                ],
                'Material_Biblioteca': [
                    'Libros/Portadas',
                    'Libros/PDFs',
                    'Revistas/Portadas',
                    'Revistas/PDFs',
                    'Imagenes/Obras',
                    'Imagenes/Portadas',
                    'Autorizaciones'
                ],
                'Backup': []
            }
            
            created_folders = {'main': main_folder}
            
            for main_folder_name, subfolders in folders.items():
                main_id = self.get_or_create_folder(main_folder_name, main_folder)
                created_folders[main_folder_name] = main_id
                
                for subfolder in subfolders:
                    if '/' in subfolder:
                        parts = subfolder.split('/')
                        parent_id = main_id
                        for part in parts:
                            parent_id = self.get_or_create_folder(part, parent_id)
                    else:
                        self.get_or_create_folder(subfolder, main_id)
            
            logger.info("✅ Estructura de carpetas creada exitosamente")
            return created_folders
            
        except Exception as e:
            logger.error(f"❌ Error creando estructura de carpetas: {e}")
            return None


# ============================================
# FUNCIONES DE ALTO NIVEL
# ============================================

def get_drive_service():
    """Obtener la instancia del servicio de Google Drive"""
    try:
        return GoogleDriveService()
    except Exception as e:
        logger.error(f"❌ Error creando servicio de Google Drive: {e}")
        return None


def test_connection():
    """Probar la conexión con Google Drive"""
    try:
        service = GoogleDriveService()
        results = service.service.files().list(pageSize=1).execute()
        logger.info("✅ Conexión a Google Drive exitosa")
        return True
    except Exception as e:
        logger.error(f"❌ Error probando conexión a Google Drive: {e}")
        return False


# Instancia global del servicio
try:
    drive_service = GoogleDriveService()
    logger.info("✅ Google Drive Service inicializado correctamente")
except Exception as e:
    logger.error(f"❌ Error inicializando Google Drive Service: {e}")
    drive_service = None