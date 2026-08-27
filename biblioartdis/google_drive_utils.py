# biblioartdis/google_drive_utils.py
import os
import logging
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload, MediaIoBaseDownload
from django.conf import settings
import io

logger = logging.getLogger(__name__)

class GoogleDriveService:
    def __init__(self):
        self.credentials = None
        self.service = None
        self._authenticate()
    
    def _authenticate(self):
        """Autenticar con Google Drive usando credenciales de service account"""
        try:
            import json
            creds_json = json.loads(settings.GOOGLE_DRIVE_CREDENTIALS_JSON)
            
            self.credentials = service_account.Credentials.from_service_account_info(
                creds_json,
                scopes=['https://www.googleapis.com/auth/drive']
            )
            self.service = build('drive', 'v3', credentials=self.credentials)
            logger.info("✅ Autenticación Google Drive exitosa")
        except Exception as e:
            logger.error(f"❌ Error autenticando Google Drive: {e}")
            raise
    
    def create_folder(self, folder_name, parent_folder_id=None):
        """Crear una carpeta en Google Drive"""
        try:
            file_metadata = {
                'name': folder_name,
                'mimeType': 'application/vnd.google-apps.folder'
            }
            if parent_folder_id:
                file_metadata['parents'] = [parent_folder_id]
            
            folder = self.service.files().create(
                body=file_metadata,
                fields='id'
            ).execute()
            
            folder_id = folder.get('id')
            logger.info(f"✅ Carpeta creada: {folder_name} (ID: {folder_id})")
            return folder_id
        except Exception as e:
            logger.error(f"❌ Error creando carpeta {folder_name}: {e}")
            return None
    
    def get_or_create_folder(self, folder_name, parent_folder_id=None):
        """Obtener o crear una carpeta"""
        try:
            # Buscar si la carpeta ya existe
            query = f"name='{folder_name}' and mimeType='application/vnd.google-apps.folder'"
            if parent_folder_id:
                query += f" and '{parent_folder_id}' in parents"
            
            results = self.service.files().list(
                q=query,
                spaces='drive',
                fields='files(id, name)'
            ).execute()
            
            files = results.get('files', [])
            
            if files:
                folder_id = files[0].get('id')
                logger.info(f"✅ Carpeta encontrada: {folder_name} (ID: {folder_id})")
                return folder_id
            else:
                # Crear si no existe
                return self.create_folder(folder_name, parent_folder_id)
        except Exception as e:
            logger.error(f"❌ Error buscando carpeta {folder_name}: {e}")
            return self.create_folder(folder_name, parent_folder_id)
    
    def upload_file(self, file_path, file_name, folder_id, mime_type=None):
        """Subir un archivo a Google Drive"""
        try:
            if not mime_type:
                # Detectar MIME type por extensión
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
                # Manejar subcarpetas anidadas (ej: Libros/Portadas)
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