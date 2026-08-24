# search.py
from django.db.models import Q
from .models import Libro, Autor
import logging

logger = logging.getLogger(__name__)


def buscar_libros_por_atributos(atributos):
    """
    Busca libros en la base de datos según los atributos proporcionados.
    
    Args:
        atributos (dict): Diccionario con campos de búsqueda:
            - titulo: str (opcional)
            - autor: str (opcional)
            - palabra_clave: str (opcional)
            - categoria: str (opcional)
            - tipo: str (opcional)
    
    Returns:
        QuerySet: Libros que coinciden con la búsqueda
    """
    if not atributos:
        return Libro.objects.none()
    
    query = Libro.objects.all()
    
    # Buscar por título
    if atributos.get('titulo'):
        query = query.filter(titulo__icontains=atributos['titulo'])
        logger.debug(f"Buscando por título: {atributos['titulo']}")
    
    # Buscar por autor (usando ManyToMany)
    if atributos.get('autor'):
        # Buscar autores que contengan el texto
        autores = Autor.objects.filter(nombre__icontains=atributos['autor'])
        if autores.exists():
            query = query.filter(autores__in=autores)
        else:
            # Si no hay autores, filtrar por nombre directamente (no devolverá nada)
            query = query.filter(autores__nombre__icontains=atributos['autor'])
        logger.debug(f"Buscando por autor: {atributos['autor']}")
    
    # Buscar por palabra clave
    if atributos.get('palabra_clave'):
        query = query.filter(palabra_clave__icontains=atributos['palabra_clave'])
        logger.debug(f"Buscando por palabra clave: {atributos['palabra_clave']}")
    
    # Buscar por categoría
    if atributos.get('categoria'):
        query = query.filter(categoria__icontains=atributos['categoria'])
        logger.debug(f"Buscando por categoría: {atributos['categoria']}")
    
    # Buscar por tipo
    if atributos.get('tipo'):
        query = query.filter(tipo__iexact=atributos['tipo'])
        logger.debug(f"Buscando por tipo: {atributos['tipo']}")
    
    return query.distinct()


def buscar_libros_avanzado(query_texto):
    """
    Búsqueda avanzada usando múltiples campos con Q objects
    
    Args:
        query_texto (str): Texto de búsqueda
    
    Returns:
        QuerySet: Libros que coinciden con la búsqueda
    """
    if not query_texto or len(query_texto.strip()) < 2:
        return Libro.objects.none()
    
    query_texto = query_texto.strip()
    
    # Construir consulta OR sobre múltiples campos
    q = Q()
    q |= Q(titulo__icontains=query_texto)
    q |= Q(descripcion__icontains=query_texto)
    q |= Q(palabra_clave__icontains=query_texto)
    q |= Q(autores__nombre__icontains=query_texto)
    q |= Q(categorias__nom_cat__icontains=query_texto)
    
    resultados = Libro.objects.filter(q).distinct()
    
    logger.info(f"Búsqueda avanzada: '{query_texto}' -> {resultados.count()} resultados")
    
    return resultados


def buscar_por_autor(nombre_autor):
    """
    Busca libros por nombre de autor
    
    Args:
        nombre_autor (str): Nombre del autor
    
    Returns:
        QuerySet: Libros del autor
    """
    if not nombre_autor:
        return Libro.objects.none()
    
    autores = Autor.objects.filter(nombre__icontains=nombre_autor)
    if autores.exists():
        return Libro.objects.filter(autores__in=autores).distinct()
    
    return Libro.objects.none()


def buscar_por_categoria(nombre_categoria):
    """
    Busca libros por categoría
    
    Args:
        nombre_categoria (str): Nombre de la categoría
    
    Returns:
        QuerySet: Libros en la categoría
    """
    if not nombre_categoria:
        return Libro.objects.none()
    
    from .models import Categoria
    
    categorias = Categoria.objects.filter(nom_cat__icontains=nombre_categoria)
    if categorias.exists():
        return Libro.objects.filter(categorias__in=categorias).distinct()
    
    # También buscar en el campo categoria (NIVEL 1, etc.)
    return Libro.objects.filter(categoria__icontains=nombre_categoria)


def buscar_por_tipo(tipo_libro):
    """
    Busca libros por tipo (LIBRO, ARTICULO, REVISTA, etc.)
    
    Args:
        tipo_libro (str): Tipo de libro
    
    Returns:
        QuerySet: Libros del tipo especificado
    """
    if not tipo_libro:
        return Libro.objects.none()
    
    return Libro.objects.filter(tipo__iexact=tipo_libro)


def formatear_resultados(libros):
    """
    Formatea los resultados de búsqueda para mostrarlos
    
    Args:
        libros (QuerySet): Libros encontrados
    
    Returns:
        list: Lista de diccionarios con información formateada
    """
    resultados = []
    
    for libro in libros[:10]:  # Limitar a 10 resultados
        resultados.append({
            'id': libro.id_libro,
            'titulo': libro.titulo,
            'autores': ', '.join([a.nombre for a in libro.autores.all()]) or 'Autor no especificado',
            'tipo': libro.get_tipo_display(),
            'categoria': libro.categoria,
            'descripcion': libro.descripcion[:200] if libro.descripcion else '',
            'pdf_url': libro.pdf_url,
            'descarga_autorizada': libro.descarga_autorizada,
        })
    
    return resultados