# biblioartdis/google_drive_utils.py
import os
import logging
import json
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload, MediaIoBaseDownload
from django.conf import settings
import io

logger = logging.getLogger(__name__)

# Alcances necesarios para Google Drive
SCOPES = ['https://www.googleapis.com/auth/drive.file']

class GoogleDriveService:
    def __init__(self):
        self.credentials = None
        self.service = None
        self._authenticate()
    
    def _authenticate(self):
        """Autenticar con Google Drive usando OAuth 2.0"""
        try:
            # Obtener credenciales OAuth desde variables de entorno
            creds_json = os.environ.get('GOOGLE_DRIVE_OAUTH_CREDENTIALS')
            token_json = os.environ.get('GOOGLE_DRIVE_TOKEN')
            
            if not creds_json:
                logger.error("❌ GOOGLE_DRIVE_OAUTH_CREDENTIALS no encontrada")
                raise Exception("Faltan credenciales OAuth")
            
            # Cargar credenciales desde JSON
            client_config = json.loads(creds_json)
            
            # Si tenemos token guardado, usarlo
            if token_json:
                try:
                    token_data = json.loads(token_json)
                    self.credentials = Credentials(
                        token=token_data.get('token'),
                        refresh_token=token_data.get('refresh_token'),
                        token_uri=token_data.get('token_uri'),
                        client_id=token_data.get('client_id'),
                        client_secret=token_data.get('client_secret'),
                        scopes=token_data.get('scopes', SCOPES)
                    )
                    logger.info("✅ Token OAuth cargado")
                except Exception as e:
                    logger.warning(f"⚠️ Error cargando token: {e}")
                    self.credentials = None
            
            # Si no hay credenciales válidas, autenticar
            if not self.credentials or not self.credentials.valid:
                if self.credentials and self.credentials.expired and self.credentials.refresh_token:
                    logger.info("🔄 Refrescando token OAuth...")
                    self.credentials.refresh(Request())
                    self._save_token()
                else:
                    # Si no hay token, necesitamos autenticación manual
                    logger.info("🔑 Iniciando flujo OAuth...")
                    flow = InstalledAppFlow.from_client_config(
                        client_config, SCOPES
                    )
                    self.credentials = flow.run_local_server(port=0)
                    self._save_token()
            
            self.service = build('drive', 'v3', credentials=self.credentials)
            logger.info("✅ Autenticación Google Drive OAuth exitosa")
            
        except Exception as e:
            logger.error(f"❌ Error autenticando Google Drive OAuth: {e}")
            raise
    
    def _save_token(self):
        """Guardar el token para usarlo después"""
        if self.credentials:
            token_data = {
                'token': self.credentials.token,
                'refresh_token': self.credentials.refresh_token,
                'token_uri': self.credentials.token_uri,
                'client_id': self.credentials.client_id,
                'client_secret': self.credentials.client_secret,
                'scopes': self.credentials.scopes
            }
            logger.info("✅ Token guardado (en memoria)")
            # Mostrar el token para copiar a Railway (solo en desarrollo)
            if os.environ.get('DEBUG', 'False') == 'True':
                print("\n" + "="*60)
                print("TOKEN GENERADO - COPIA ESTE JSON EN RAILWAY:")
                print("="*60)
                print(json.dumps(token_data, indent=2))
                print("="*60)
    
    def get_or_create_folder(self, folder_path, parent_folder_id=None):
        """Obtener o crear una carpeta por ruta (ej: Usuarios/Matriculas)"""
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
                    fields='files(id, name)'
                ).execute()
                
                files = results.get('files', [])
                
                if files:
                    current_parent = files[0].get('id')
                    logger.info(f"✅ Carpeta encontrada: {part} (ID: {current_parent})")
                else:
                    file_metadata = {
                        'name': part,
                        'mimeType': 'application/vnd.google-apps.folder'
                    }
                    if current_parent:
                        file_metadata['parents'] = [current_parent]
                    
                    folder = self.service.files().create(
                        body=file_metadata,
                        fields='id'
                    ).execute()
                    
                    current_parent = folder.get('id')
                    logger.info(f"✅ Carpeta creada: {part} (ID: {current_parent})")
            
            return current_parent
            
        except Exception as e:
            logger.error(f"❌ Error con carpeta {folder_path}: {e}")
            return None
    
    def upload_file(self, file_path, file_name, folder_id, mime_type=None):
        """Subir un archivo a Google Drive"""
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
                    '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
                }
                mime_type = mime_types.get(ext, 'application/octet-stream')
            
            file_metadata = {
                'name': file_name,
                'parents': [folder_id]
            }
            
            media = MediaFileUpload(
                file_path,
                mimetype=mime_type,
                resumable=True
            )
            
            file = self.service.files().create(
                body=file_metadata,
                media_body=media,
                fields='id, webViewLink'
            ).execute()
            
            file_id = file.get('id')
            web_link = file.get('webViewLink')
            
            logger.info(f"✅ Archivo subido: {file_name} (ID: {file_id})")
            
            return {
                'file_id': file_id,
                'web_link': web_link,
                'download_link': f"https://drive.google.com/uc?id={file_id}&export=download"
            }
        except Exception as e:
            logger.error(f"❌ Error subiendo archivo {file_name}: {e}")
            return None
    
    def delete_file(self, file_id):
        """Eliminar un archivo de Google Drive"""
        try:
            self.service.files().delete(fileId=file_id).execute()
            logger.info(f"✅ Archivo eliminado: {file_id}")
            return True
        except Exception as e:
            logger.error(f"❌ Error eliminando archivo {file_id}: {e}")
            return False
    
    def create_initial_structure(self, main_folder_id):
        """Crear toda la estructura de carpetas"""
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
        
        created_folders = {}
        
        for main_folder, subfolders in folders.items():
            main_id = self.get_or_create_folder(main_folder, main_folder_id)
            created_folders[main_folder] = main_id
            
            for subfolder in subfolders:
                if '/' in subfolder:
                    parts = subfolder.split('/')
                    parent_id = main_id
                    for part in parts:
                        parent_id = self.get_or_create_folder(part, parent_id)
                else:
                    self.get_or_create_folder(subfolder, main_id)
        
        return created_folders

# Instancia global del servicio
drive_service = GoogleDriveService()