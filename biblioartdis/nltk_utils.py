# nltk_utils.py
import nltk
import logging
import os
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer

logger = logging.getLogger(__name__)

# Configurar directorio de datos NLTK para Railway (opcional)
# En Railway, los archivos se descargan en /app/nltk_data
NLTK_DATA_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'nltk_data')
if not os.path.exists(NLTK_DATA_PATH):
    try:
        os.makedirs(NLTK_DATA_PATH, exist_ok=True)
        nltk.data.path.append(NLTK_DATA_PATH)
    except Exception as e:
        logger.warning(f"No se pudo crear directorio NLTK: {e}")


# Variables globales para evitar descargar múltiples veces
_lemmatizer = None
_stop_words = None
_nltk_inicializado = False


def inicializar_nltk():
    """
    Inicializa los recursos de NLTK (solo una vez)
    """
    global _lemmatizer, _stop_words, _nltk_inicializado
    
    if _nltk_inicializado:
        return _lemmatizer, _stop_words
    
    try:
        # Descargar recursos necesarios con manejo de errores
        recursos = ['punkt', 'wordnet', 'stopwords', 'punkt_tab']
        
        for recurso in recursos:
            try:
                nltk.download(recurso, quiet=True, download_dir=NLTK_DATA_PATH if os.path.exists(NLTK_DATA_PATH) else None)
            except Exception as e:
                logger.warning(f"Error descargando {recurso}: {e}")
                # Intentar sin directorio personalizado
                try:
                    nltk.download(recurso, quiet=True)
                except Exception as e2:
                    logger.error(f"No se pudo descargar {recurso}: {e2}")
        
        _lemmatizer = WordNetLemmatizer()
        
        # Stopwords en inglés y español
        try:
            stop_words_en = set(stopwords.words('english'))
            stop_words_es = set(stopwords.words('spanish'))
            _stop_words = stop_words_en.union(stop_words_es)
        except Exception as e:
            logger.error(f"Error cargando stopwords: {e}")
            _stop_words = set()  # Vacío como fallback
        
        _nltk_inicializado = True
        logger.info("NLTK inicializado correctamente")
        
    except Exception as e:
        logger.error(f"Error inicializando NLTK: {str(e)}")
        _lemmatizer = WordNetLemmatizer()
        _stop_words = set()
        _nltk_inicializado = True
    
    return _lemmatizer, _stop_words


def procesar_texto(texto, lemmatizer=None, stop_words=None):
    """
    Procesa el texto y devuelve tokens útiles
    """
    if not texto or not isinstance(texto, str):
        return []
    
    # Inicializar NLTK si es necesario
    if lemmatizer is None or stop_words is None:
        lemmatizer, stop_words = inicializar_nltk()
    
    try:
        # Convertir a minúsculas
        texto = texto.lower()
        
        # Tokenización (con manejo de errores)
        try:
            tokens = word_tokenize(texto, language='spanish')
        except:
            try:
                tokens = word_tokenize(texto)
            except:
                tokens = texto.split()  # Fallback simple
        
        # Filtrar tokens y lematizar
        tokens_filtrados = []
        for token in tokens:
            if token.isalnum() and len(token) > 2 and token not in stop_words:
                try:
                    token_lemmatizado = lemmatizer.lemmatize(token)
                    tokens_filtrados.append(token_lemmatizado)
                except:
                    tokens_filtrados.append(token)
        
        return tokens_filtrados
        
    except Exception as e:
        logger.error(f"Error procesando texto: {str(e)}")
        return texto.lower().split()  # Fallback básico


def contiene_palabras(texto, lista_palabras):
    """
    Verifica si el texto contiene alguna de las palabras de la lista
    """
    if not texto or not lista_palabras:
        return False
    
    texto = texto.lower()
    return any(palabra.lower() in texto for palabra in lista_palabras)


def limpiar_texto(texto):
    """
    Limpia el texto eliminando caracteres especiales
    """
    if not texto:
        return ""
    
    import re
    # Eliminar caracteres especiales pero mantener letras, números y espacios
    texto_limpio = re.sub(r'[^\w\s]', ' ', texto)
    # Eliminar espacios múltiples
    texto_limpio = re.sub(r'\s+', ' ', texto_limpio)
    return texto_limpio.strip()


# Probar conexión (útil para diagnóstico)
def probar_nltk():
    """
    Prueba que NLTK funcione correctamente
    """
    print("=" * 50)
    print("Probando NLTK...")
    print("=" * 50)
    
    try:
        lemmatizer, stop_words = inicializar_nltk()
        texto_prueba = "Los libros de arte son muy interesantes"
        tokens = procesar_texto(texto_prueba, lemmatizer, stop_words)
        print(f"✅ NLTK funciona correctamente")
        print(f"   Texto original: '{texto_prueba}'")
        print(f"   Tokens procesados: {tokens}")
        return True
    except Exception as e:
        print(f"❌ Error en NLTK: {e}")
        return False


# Ejecutar prueba si se llama directamente
if __name__ == "__main__":
    probar_nltk()