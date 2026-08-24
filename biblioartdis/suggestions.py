# suggestions.py
from django.db.models import Q
from .models import Libro, Autor, Categoria
import logging

logger = logging.getLogger(__name__)


def generar_sugerencias(atributos, limite=5):
    """
    Genera sugerencias de libros basadas en atributos similares.
    
    Args:
        atributos (dict): Diccionario con campos de búsqueda:
            - titulo: str (opcional)
            - autor: str (opcional)
            - categoria: str (opcional)
            - palabra_clave: str (opcional)
            - tipo: str (opcional)
        limite (int): Número máximo de sugerencias a retornar
    
    Returns:
        QuerySet: Libros sugeridos
    """
    if not atributos:
        return Libro.objects.none()
    
    # Construir consulta para sugerencias basadas en similitud
    q = Q()
    
    # Sugerencias por categoría
    if atributos.get('categoria'):
        q |= Q(categoria__icontains=atributos['categoria'])
        logger.debug(f"Sugerencia por categoría: {atributos['categoria']}")
    
    # Sugerencias por autor (usando ManyToMany correctamente)
    if atributos.get('autor'):
        # Buscar autores similares
        autores_similares = Autor.objects.filter(
            nombre__icontains=atributos['autor']
        )
        if autores_similares.exists():
            q |= Q(autores__in=autores_similares)
        else:
            q |= Q(autores__nombre__icontains=atributos['autor'])
        logger.debug(f"Sugerencia por autor: {atributos['autor']}")
    
    # Sugerencias por palabra clave
    if atributos.get('palabra_clave'):
        q |= Q(palabra_clave__icontains=atributos['palabra_clave'])
        logger.debug(f"Sugerencia por palabra clave: {atributos['palabra_clave']}")
    
    # Sugerencias por tipo similar
    if atributos.get('tipo'):
        q |= Q(tipo__iexact=atributos['tipo'])
        logger.debug(f"Sugerencia por tipo: {atributos['tipo']}")
    
    # Sugerencias por título (palabras comunes)
    if atributos.get('titulo'):
        # Extraer palabras significativas del título
        palabras = [p for p in atributos['titulo'].split() if len(p) > 3]
        for palabra in palabras[:3]:  # Usar máximo 3 palabras
            q |= Q(titulo__icontains=palabra)
        logger.debug(f"Sugerencia por título: {atributos['titulo']}")
    
    # Obtener sugerencias únicas
    sugerencias = Libro.objects.filter(q).distinct()
    
    # Excluir el libro original si se proporciona un ID
    if atributos.get('excluir_id'):
        sugerencias = sugerencias.exclude(id_libro=atributos['excluir_id'])
    
    logger.info(f"Sugerencias generadas: {sugerencias.count()} resultados")
    
    return sugerencias[:limite]


def generar_sugerencias_por_historial(historial_busquedas, limite=5):
    """
    Genera sugerencias basadas en el historial de búsquedas del usuario.
    
    Args:
        historial_busquedas (list): Lista de términos de búsqueda anteriores
        limite (int): Número máximo de sugerencias
    
    Returns:
        QuerySet: Libros sugeridos
    """
    if not historial_busquedas:
        return Libro.objects.none()
    
    q = Q()
    
    for termino in historial_busquedas[:5]:  # Últimas 5 búsquedas
        q |= Q(titulo__icontains=termino)
        q |= Q(descripcion__icontains=termino)
        q |= Q(palabra_clave__icontains=termino)
        q |= Q(autores__nombre__icontains=termino)
    
    sugerencias = Libro.objects.filter(q).distinct()
    
    logger.info(f"Sugerencias por historial: {sugerencias.count()} resultados")
    
    return sugerencias[:limite]


def generar_sugerencias_populares(limite=5):
    """
    Genera sugerencias de libros populares (más visitados).
    
    Args:
        limite (int): Número máximo de sugerencias
    
    Returns:
        QuerySet: Libros populares
    """
    from django.db.models import Count
    
    libros_populares = Libro.objects.annotate(
        visitas_count=Count('visitalibro')
    ).filter(visitas_count__gt=0).order_by('-visitas_count')
    
    if not libros_populares.exists():
        # Fallback: libros más recientes
        libros_populares = Libro.objects.all().order_by('-fecha_publicacion')
    
    logger.info(f"Sugerencias populares: {libros_populares.count()} resultados")
    
    return libros_populares[:limite]


def generar_sugerencias_recientes(limite=5):
    """
    Genera sugerencias de libros recientemente agregados.
    
    Args:
        limite (int): Número máximo de sugerencias
    
    Returns:
        QuerySet: Libros recientes
    """
    libros_recientes = Libro.objects.all().order_by('-fecha_publicacion')[:limite]
    
    logger.info(f"Sugerencias recientes: {libros_recientes.count()} resultados")
    
    return libros_recientes


def generar_sugerencias_por_categoria(categoria, limite=5):
    """
    Genera sugerencias de libros de una categoría específica.
    
    Args:
        categoria (str): Nombre de la categoría
        limite (int): Número máximo de sugerencias
    
    Returns:
        QuerySet: Libros de la categoría
    """
    if not categoria:
        return Libro.objects.none()
    
    # Buscar por campo categoria (NIVEL 1, etc.)
    sugerencias = Libro.objects.filter(categoria__icontains=categoria)
    
    # También buscar por categorías ManyToMany
    from .models import Categoria
    categorias_relacionadas = Categoria.objects.filter(nom_cat__icontains=categoria)
    if categorias_relacionadas.exists():
        sugerencias = sugerencias | Libro.objects.filter(categorias__in=categorias_relacionadas)
    
    sugerencias = sugerencias.distinct()[:limite]
    
    logger.info(f"Sugerencias por categoría '{categoria}': {sugerencias.count()} resultados")
    
    return sugerencias


def generar_sugerencias_por_autor(autor_nombre, limite=5):
    """
    Genera sugerencias de libros del mismo autor.
    
    Args:
        autor_nombre (str): Nombre del autor
        limite (int): Número máximo de sugerencias
    
    Returns:
        QuerySet: Libros del autor
    """
    if not autor_nombre:
        return Libro.objects.none()
    
    autores = Autor.objects.filter(nombre__icontains=autor_nombre)
    if autores.exists():
        sugerencias = Libro.objects.filter(autores__in=autores).distinct()
    else:
        sugerencias = Libro.objects.filter(autores__nombre__icontains=autor_nombre).distinct()
    
    logger.info(f"Sugerencias por autor '{autor_nombre}': {sugerencias.count()} resultados")
    
    return sugerencias[:limite]


def formatear_sugerencias(sugerencias):
    """
    Formatea las sugerencias para mostrarlas al usuario.
    
    Args:
        sugerencias (QuerySet): Libros sugeridos
    
    Returns:
        list: Lista de diccionarios con información de sugerencias
    """
    resultados = []
    
    for libro in sugerencias:
        resultados.append({
            'id': libro.id_libro,
            'titulo': libro.titulo,
            'autores': ', '.join([a.nombre for a in libro.autores.all()]) or 'Autor no especificado',
            'tipo': libro.get_tipo_display(),
            'categoria': libro.categoria,
            'descripcion': libro.descripcion[:150] + '...' if libro.descripcion and len(libro.descripcion) > 150 else (libro.descripcion or ''),
            'url': f"/libro/{libro.id_libro}/",
            'razon': _obtener_razon_sugerencia(libro)
        })
    
    return resultados


def _obtener_razon_sugerencia(libro):
    """
    Determina una razón legible para la sugerencia.
    """
    if libro.descarga_autorizada:
        return "Disponible para descarga"
    return "Disponible para consulta en línea"


# ============================================
# FUNCIONES PARA VISTAS
# ============================================

def obtener_sugerencias_contexto(request, libro_actual=None):
    """
    Obtiene sugerencias para mostrar en el contexto de una vista.
    
    Args:
        request: HttpRequest object
        libro_actual: Libro actual (para excluirlo de sugerencias)
    
    Returns:
        dict: Contexto con diferentes tipos de sugerencias
    """
    context = {
        'sugerencias_populares': generar_sugerencias_populares(5),
        'sugerencias_recientes': generar_sugerencias_recientes(5),
    }
    
    # Sugerencias basadas en el libro actual
    if libro_actual:
        atributos = {
            'categoria': libro_actual.categoria,
            'excluir_id': libro_actual.id_libro
        }
        
        # Agregar algunos autores
        if libro_actual.autores.exists():
            atributos['autor'] = libro_actual.autores.first().nombre
        
        context['sugerencias_relacionadas'] = generar_sugerencias(atributos, 5)
    
    # Sugerencias basadas en historial del usuario (si está autenticado)
    if request.user.is_authenticated:
        from .models import HistorialBusqueda
        ultimas_busquedas = HistorialBusqueda.objects.filter(
            usuario=request.user
        ).values_list('termino_busqueda', flat=True)[:5]
        
        if ultimas_busquedas:
            context['sugerencias_historial'] = generar_sugerencias_por_historial(
                list(ultimas_busquedas), 5
            )
    
    return context


# Probar conexión (útil para diagnóstico)
def probar_sugerencias():
    """
    Prueba que las sugerencias funcionen correctamente
    """
    print("=" * 50)
    print("Probando sistema de sugerencias...")
    print("=" * 50)
    
    try:
        # Probar sugerencias populares
        populares = generar_sugerencias_populares(3)
        print(f"✅ Sugerencias populares: {populares.count()} resultados")
        
        # Probar sugerencias por categoría
        por_categoria = generar_sugerencias_por_categoria('NIVEL 1', 3)
        print(f"✅ Sugerencias por categoría: {por_categoria.count()} resultados")
        
        # Probar sugerencias por atributos
        atributos = {'categoria': 'NIVEL 1', 'tipo': 'LIBRO'}
        sugerencias = generar_sugerencias(atributos, 3)
        print(f"✅ Sugerencias por atributos: {sugerencias.count()} resultados")
        
        return True
    except Exception as e:
        print(f"❌ Error en sugerencias: {e}")
        return False


# Ejecutar prueba si se llama directamente
if __name__ == "__main__":
    probar_sugerencias()