import re
import unicodedata

def limpiar_texto(texto):
    """
    Limpia y normaliza el texto eliminando caracteres especiales, signos de puntuación
    y normalizando espacios.
    
    Args:
        texto (str): Texto a limpiar
        
    Returns:
        str: Texto limpio y normalizado
    """
    if not texto:
        return ""
        
    # Convertir a minúsculas
    texto = texto.lower()
    
    # Normalizar caracteres (convertir acentos y caracteres especiales)
    texto = unicodedata.normalize('NFKD', texto).encode('ASCII', 'ignore').decode('utf-8')
    
    # Eliminar caracteres especiales y signos de puntuación
    # Mantiene letras, números y espacios
    texto = re.sub(r'[^a-z0-9\s]', ' ', texto)
    
    # Normalizar espacios múltiples a un solo espacio
    texto = re.sub(r'\s+', ' ', texto)
    
    # Eliminar espacios al inicio y final
    texto = texto.strip()
    
    return texto

def limpiar_busqueda(query):
    """
    Limpia y prepara una consulta de búsqueda para su procesamiento.
    
    Args:
        query (str): Consulta de búsqueda
        
    Returns:
        str: Consulta limpia y normalizada
    """
    # Preservar búsquedas por tipo (tipo:LIBRO)
    if query.startswith('tipo:'):
        return query
        
    return limpiar_texto(query)
