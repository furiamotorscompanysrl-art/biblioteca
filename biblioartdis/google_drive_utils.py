# biblioartdis/google_drive_utils.py
import os
import logging
import json
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload, MediaIoBaseDownload
from django.conf import settings
import io

logger = logging.getLogger(__name__)

# Alcances necesarios para Google Drive
SCOPES = ['https://www.googleapis.com/auth/drive.file']


class GoogleDriveService:
    """
    Servicio para interactuar con Google Drive usando Cuenta de Servicio
    ✅ NUNCA EXPIRA - Ideal para producción en Railway
    ✅ No requiere interacción manual
    ✅ Seguro y fácil de configurar
    """
    
    def __init__(self):
        self.service = None
        self._authenticate()
    
    def _authenticate(self):
        """
        Autenticar con Google Drive usando Cuenta de Servicio
        Las credenciales se obtienen de GOOGLE_APPLICATION_CREDENTIALS_JSON
        """
        try:
            # Obtener credenciales desde variable de entorno
            creds_json = os.environ.get('GOOGLE_APPLICATION_CREDENTIALS_JSON')
            
            if not creds_json:
                logger.error("❌ GOOGLE_APPLICATION_CREDENTIALS_JSON no encontrada")
                logger.error("⚠️ Debes configurar esta variable en Railway con el JSON de la cuenta de servicio")
                raise Exception("Faltan credenciales de cuenta de servicio")
            
            # Cargar credenciales desde JSON
            try:
                creds_dict = json.loads(creds_json)
            except json.JSONDecodeError as e:
                logger.error(f"❌ Error parseando GOOGLE_APPLICATION_CREDENTIALS_JSON: {e}")
                raise Exception("Credenciales JSON inválidas")
            
            # Validar que tenga los campos necesarios
            required_fields = ['type', 'project_id', 'private_key', 'client_email']
            for field in required_fields:
                if field not in creds_dict:
                    logger.error(f"❌ Falta campo '{field}' en las credenciales")
                    raise Exception(f"Credenciales incompletas: falta {field}")
            
            # Crear credenciales de cuenta de servicio
            credentials = service_account.Credentials.from_service_account_info(
                creds_dict,
                scopes=SCOPES
            )
            
            # Construir servicio de Google Drive
            self.service = build('drive', 'v3', credentials=credentials)
            
            logger.info("✅ Autenticación con Cuenta de Servicio exitosa")
            logger.info(f"📧 Cuenta de servicio: {creds_dict.get('client_email')}")
            logger.info("🔒 Token NUNCA expira - Perfecto para producción")
            
        except Exception as e:
            logger.error(f"❌ Error autenticando con Cuenta de Servicio: {e}")
            raise
    
    def get_or_create_folder(self, folder_path, parent_folder_id=None):
        """
        Obtener o crear una carpeta por ruta (ej: Material_Biblioteca/Libros/PDFs)
        
        Args:
            folder_path: Ruta de la carpeta (ej: 'Material_Biblioteca/Libros/PDFs')
            parent_folder_id: ID de la carpeta padre (opcional)
        
        Returns:
            ID de la carpeta o None si falla
        """
        try:
            parts = folder_path.split('/')
            current_parent = parent_folder_id
            
            for part in parts:
                # Buscar carpeta existente
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
                    # Carpeta existe
                    current_parent = files[0].get('id')
                    logger.info(f"📁 Carpeta encontrada: {part} (ID: {current_parent})")
                else:
                    # Crear carpeta
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
                    logger.info(f"📁 Carpeta creada: {part} (ID: {current_parent})")
            
            return current_parent
            
        except Exception as e:
            logger.error(f"❌ Error con carpeta {folder_path}: {e}")
            return None
    
    def upload_file(self, file_path, file_name, folder_id, mime_type=None):
        """
        Subir un archivo a Google Drive
        
        Args:
            file_path: Ruta del archivo local
            file_name: Nombre del archivo en Drive
            folder_id: ID de la carpeta donde subir
            mime_type: Tipo MIME (opcional, se detecta automáticamente)
        
        Returns:
            Dict con file_id, web_link, download_link o None si falla
        """
        try:
            # Determinar MIME type si no se proporciona
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
            
            # Preparar metadatos del archivo
            file_metadata = {
                'name': file_name,
                'parents': [folder_id]
            }
            
            # Crear media upload
            media = MediaFileUpload(
                file_path,
                mimetype=mime_type,
                resumable=True,
                chunksize=1024 * 1024  # 1MB chunks
            )
            
            # Subir archivo
            logger.info(f"📤 Subiendo archivo: {file_name} ({mime_type})")
            file = self.service.files().create(
                body=file_metadata,
                media_body=media,
                fields='id, webViewLink, size'
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
        """
        Eliminar un archivo de Google Drive
        
        Args:
            file_id: ID del archivo a eliminar
        
        Returns:
            True si se eliminó correctamente, False si falla
        """
        try:
            if not file_id:
                logger.warning("⚠️ No se proporcionó file_id para eliminar")
                return False
            
            self.service.files().delete(fileId=file_id).execute()
            logger.info(f"✅ Archivo eliminado: {file_id}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error eliminando archivo {file_id}: {e}")
            return False
    
    def get_file_metadata(self, file_id):
        """
        Obtener metadatos de un archivo
        
        Args:
            file_id: ID del archivo
        
        Returns:
            Dict con metadatos o None si falla
        """
        try:
            file = self.service.files().get(
                fileId=file_id,
                fields='id, name, mimeType, size, webViewLink, createdTime, modifiedTime'
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
        """
        Listar archivos en una carpeta
        
        Args:
            folder_id: ID de la carpeta
            max_results: Número máximo de resultados
        
        Returns:
            Lista de archivos
        """
        try:
            query = f"'{folder_id}' in parents and trashed=false"
            
            results = self.service.files().list(
                q=query,
                pageSize=max_results,
                fields='files(id, name, mimeType, size, webViewLink, createdTime)'
            ).execute()
            
            files = results.get('files', [])
            logger.info(f"📂 Encontrados {len(files)} archivos en carpeta {folder_id}")
            
            return files
            
        except Exception as e:
            logger.error(f"❌ Error listando archivos en {folder_id}: {e}")
            return []
    
    def create_initial_structure(self, main_folder_name='Biblioteca_Artes_Diseno'):
        """
        Crear toda la estructura de carpetas para la biblioteca
        
        Args:
            main_folder_name: Nombre de la carpeta principal
        
        Returns:
            Dict con los IDs de las carpetas creadas
        """
        try:
            # Crear carpeta principal
            main_folder = self.get_or_create_folder(main_folder_name)
            
            if not main_folder:
                logger.error("❌ No se pudo crear la carpeta principal")
                return None
            
            logger.info(f"📁 Carpeta principal: {main_folder_name} (ID: {main_folder})")
            
            # Estructura de carpetas
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
                        # Carpetas anidadas
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
# FUNCIONES DE ALTO NIVEL PARA USAR EN LA APP
# ============================================

def get_drive_service():
    """
    Obtener la instancia del servicio de Google Drive
    
    Returns:
        GoogleDriveService o None si falla
    """
    try:
        return GoogleDriveService()
    except Exception as e:
        logger.error(f"❌ Error creando servicio de Google Drive: {e}")
        return None


def test_connection():
    """
    Probar la conexión con Google Drive
    
    Returns:
        True si la conexión es exitosa, False si falla
    """
    try:
        service = GoogleDriveService()
        # Intentar listar archivos para probar
        results = service.service.files().list(pageSize=1).execute()
        logger.info("✅ Conexión a Google Drive exitosa")
        return True
    except Exception as e:
        logger.error(f"❌ Error probando conexión a Google Drive: {e}")
        return False


# Instancia global del servicio (se crea al importar)
try:
    drive_service = GoogleDriveService()
    logger.info("✅ Google Drive Service inicializado correctamente")
except Exception as e:
    logger.error(f"❌ Error inicializando Google Drive Service: {e}")
    drive_service = None