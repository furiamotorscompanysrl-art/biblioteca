# views/usuario_views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, Count
from django.http import JsonResponse, HttpResponse
from django.utils import timezone
from datetime import date
from django.core.paginator import Paginator
from django.contrib.auth.hashers import check_password
import random
import logging
import json


from ..models import (
    Usuario, Libro, Autor, Categoria, Sugerencia, Coleccion, Revista,
    VisitaLibro, Imagen, HistorialBusqueda
)
from ..utils.text_cleaner import limpiar_busqueda
from ..utils.chat_responses import ChatResponses
from ..groq_config import get_ai_response

try:
    import spacy
    nlp = spacy.load("es_core_news_sm")
except:
    nlp = None

logger = logging.getLogger(__name__)


# ==================== Perfil e Historial ====================
@login_required
def perfil(request):
    try:
        usuario = request.user.usuario
        usando_ci_como_password = check_password(usuario.ci, usuario.user.password)
        return render(request, 'perfil.html', {'usuario': usuario, 'usando_ci_como_password': usando_ci_como_password})
    except Usuario.DoesNotExist:
        messages.error(request, "Tu cuenta no está configurada correctamente.")
        return redirect('inicio')


@login_required
def historial_visitas(request):
    try:
        usuario = request.user.usuario
        visitas = VisitaLibro.objects.filter(visitante=usuario).order_by('-fecha_visualizacion')
        return render(request, 'historial_visitas.html', {'visitas': visitas})
    except Usuario.DoesNotExist:
        messages.error(request, "Error con tu perfil.")
        return redirect('inicio')


@login_required
def registrar_visita_libro(request):
    if request.method == 'POST':
        try:
            libro_id = request.POST.get('libro_id')
            usuario = request.user.usuario
            visita, created = VisitaLibro.objects.get_or_create(
                visitante=usuario,
                libro_visitado_id=libro_id,
                fecha_consulta=date.today(),
                defaults={'fecha_visualizacion': timezone.now()}
            )
            if not created:
                visita.fecha_visualizacion = timezone.now()
                visita.save()
            return JsonResponse({'mensaje': 'Visita registrada'})
        except Exception as e:
            logger.error(f"Error registrando visita: {e}")
            return JsonResponse({'error': str(e)}, status=500)
    return JsonResponse({'error': 'Método no permitido'}, status=405)


# ==================== Catálogo y Búsqueda ====================
@login_required
def inicio(request):
    libros = Libro.objects.prefetch_related('autores', 'categorias')
    buscar_por = request.GET.get('q', '')
    filtro = request.GET.get('filtro', '')
    categoria = request.GET.get('categoria', '')

    if buscar_por:
        libros = libros.filter(
            Q(titulo__icontains=buscar_por) |
            Q(autores__nombre__icontains=buscar_por) |
            Q(palabra_clave__icontains=buscar_por)
        ).distinct()
    if categoria:
        libros = libros.filter(categorias__id_categoria=categoria)
    if filtro == 'populares':
        libros = libros.annotate(visitas_count=Count('visitalibro')).order_by('-visitas_count')
    else:
        libros = libros.order_by('-fecha_publicacion')

    paginator = Paginator(libros, 8)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)

    return render(request, 'inicio.html', {
        'libros': page_obj,
        'buscar_por': buscar_por,
        'filtro_actual': filtro,
        'categoria_id': categoria,
    })


@login_required
def novedades_libros(request):
    libros_base = Libro.objects.all().prefetch_related('autores', 'categorias')
    imagenes_base = Imagen.objects.prefetch_related('categorias').all()
    
    filtros = {
        'categoria': request.GET.get('categoria'),
        'tipo': request.GET.get('tipo'),
        'autor': request.GET.get('autor'),
        'descarga': request.GET.get('descarga')
    }
    
    libros_filtered = libros_base
    imagenes_filtered = imagenes_base
    if filtros['categoria']:
        libros_filtered = libros_filtered.filter(categorias__id_categoria=filtros['categoria'])
        imagenes_filtered = imagenes_filtered.filter(categorias__id_categoria=filtros['categoria'])
    if filtros['tipo']:
        libros_filtered = libros_filtered.filter(tipo=filtros['tipo'])
    if filtros['autor']:
        libros_filtered = libros_filtered.filter(autores__id_autor=filtros['autor'])
    if filtros['descarga'] is not None:
        libros_filtered = libros_filtered.filter(descarga_autorizada=filtros['descarga'] == '1')
    
    categorias = Categoria.objects.all()
    categoria_counts = {
        str(cat.id_categoria): {
            'libros': libros_base.filter(categorias__id_categoria=cat.id_categoria, tipo='LIBRO').distinct().count(),
            'imagenes': imagenes_base.filter(categorias__id_categoria=cat.id_categoria).distinct().count()
        } for cat in categorias
    }
    autores = Autor.objects.all()
    autor_counts = {
        str(autor.id_autor): libros_base.filter(autores__id_autor=autor.id_autor, tipo='LIBRO').distinct().count()
        for autor in autores
    }
    tipos = []
    for tipo_choice in Libro._meta.get_field('tipo').choices:
        count = libros_base.filter(tipo=tipo_choice[0])
        if filtros['categoria']:
            count = count.filter(categorias__id_categoria=filtros['categoria'])
        if filtros['autor']:
            count = count.filter(autores__id_autor=filtros['autor'])
        tipos.append((tipo_choice[0], tipo_choice[1], count.distinct().count()))
    
    descarga_counts = {
        'autorizada': libros_base.filter(descarga_autorizada=True, tipo='LIBRO').distinct().count(),
        'no_autorizada': libros_base.filter(descarga_autorizada=False, tipo='LIBRO').distinct().count()
    }
    
    context = {
        'libros': libros_filtered.distinct(),
        'imagenes': imagenes_filtered.distinct(),
        'categorias': categorias,
        'categoria_counts': categoria_counts,
        'autores': autores,
        'autor_counts': autor_counts,
        'tipos': tipos,
        'descarga_counts': descarga_counts,
        'filtros_activos': filtros,
        'total_libros': libros_base.distinct().count(),
        'total_imagenes': imagenes_base.distinct().count()
    }
    return render(request, 'novedades_libros.html', context)


@login_required
def libros_nivel(request, id_nivel):
    niveles = {1: 'NIVEL 1', 2: 'NIVEL 2', 3: 'NIVEL 3', 4: 'NIVEL 4'}
    nomb_nivel = {1: "PRIMER AÑO", 2: "SEGUNDO AÑO", 3: "TERCERO AÑO", 4: "CUARTO AÑO", 5: "OTRAS SECCIONES"}
    categoria = niveles.get(id_nivel, 'OTRO')
    libros = Libro.objects.filter(categoria=categoria)
    return render(request, 'nivel.html', {'libros': libros, 'nivel': categoria, 'nomb_nivel': nomb_nivel.get(id_nivel, 'OTRO')})


def catalogo(request):
    colecciones = Coleccion.objects.prefetch_related('revista_set').all()
    return render(request, 'catalogo.html', {'colecciones': colecciones})


# ==================== Sugerencias de Usuario ====================
@login_required
def sugerir_libro(request):
    # Verificar que el usuario tiene un perfil
    if not hasattr(request.user, 'usuario'):
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'error': 'Perfil de usuario no encontrado'}, status=400)
        messages.error(request, 'Tu perfil no está completo. Contacta al administrador.')
        return redirect('inicio')
    
    if request.method == 'POST':
        try:
            autor_sugerencia = request.POST.get('autor_sugerencia')
            titulo_sugerencia = request.POST.get('titulo_sugerencia')
            edicion = request.POST.get('edicion')
            descripcion = request.POST.get('descripcion')
            
            # Validaciones básicas
            if not autor_sugerencia or not titulo_sugerencia or not descripcion:
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({'success': False, 'error': 'Todos los campos obligatorios deben ser completados'}, status=400)
                messages.error(request, 'Todos los campos obligatorios deben ser completados')
                return render(request, 'sugerir_libro.html')
            
            # Crear la sugerencia
            nueva_sugerencia = Sugerencia(
                solicitante=request.user.usuario,
                autor_sugerencia=autor_sugerencia,
                titulo_sugerencia=titulo_sugerencia,
                edicion=edicion or '',
                estado_respuesta='Pendiente',
                descripcion=descripcion
            )
            nueva_sugerencia.save()
            
            # Respuesta para AJAX
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': True, 'message': 'Sugerencia enviada correctamente'})
            
            messages.success(request, 'Sugerencia enviada correctamente')
            return redirect('listar_sugerencias_usuario')
            
        except Exception as e:
            logger.error(f"Error al guardar sugerencia: {e}")
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'error': str(e)}, status=500)
            messages.error(request, f'Error al enviar sugerencia: {str(e)}')
            return render(request, 'sugerir_libro.html')
    
    # GET request - mostrar formulario
    return render(request, 'sugerir_libro.html')


@login_required
def listar_sugerencias_usuario(request):
    try:
        usuario = get_object_or_404(Usuario, user=request.user)
        sugerencias = Sugerencia.objects.filter(solicitante=usuario)
        return render(request, 'listar_sugerencias_usuario.html', {'sugerencias': sugerencias})
    except Exception as e:
        logger.error(f"Error listando sugerencias: {e}")
        messages.error(request, "Error al acceder a su perfil.")
        return redirect('inicio')


@login_required
def descartar_sugerencia(request, sugerencia_id):
    sugerencia = get_object_or_404(Sugerencia, pk=sugerencia_id)
    sugerencia.estado_respuesta = 'Descartado'
    sugerencia.save()
    return redirect('listar_sugerencias')


# ==================== Visualización de PDF ====================
@login_required
def ver_pdf(request, libro_id):
    libro = get_object_or_404(Libro, id_libro=libro_id)
    return HttpResponse(libro.pdf, content_type='application/pdf')


# ==================== Galería de Imágenes ====================
def galeria_artistica(request):
    imagenes = Imagen.objects.all()
    categorias = Categoria.objects.all()
    return render(request, 'galeria_artistica.html', {'imagenes': imagenes, 'categorias': categorias})


def ver_imagen(request, id):
    imagen = get_object_or_404(Imagen, id=id)
    return render(request, 'ver_imagen.html', {'imagen': imagen})


# ==================== Búsqueda Inteligente y Chatbot ====================
def obtener_recomendaciones_personalizadas(usuario):
    historial = HistorialBusqueda.objects.filter(usuario=usuario).order_by('-fecha_busqueda')[:5]
    terminos_busqueda = [b.termino_busqueda for b in historial]
    libros_recomendados = Libro.objects.filter(
        Q(titulo__icontains=' '.join(terminos_busqueda)) |
        Q(descripcion__icontains=' '.join(terminos_busqueda)) |
        Q(palabra_clave__icontains=' '.join(terminos_busqueda))
    ).distinct()[:5]
    recomendaciones = []
    for libro in libros_recomendados:
        recomendaciones.append({
            'titulo': libro.titulo,
            'autores': ', '.join([a.nombre for a in libro.autores.all()]) or 'Autor desconocido',
            'img_portada': libro.img_portada.url if libro.img_portada else '',
            'descripcion': libro.descripcion or '',
            'pdf': libro.pdf.url if libro.pdf else '',
            'pdf_url': libro.pdf_url or '',
            'descarga_autorizada': libro.descarga_autorizada,
            'palabra_clave': libro.palabra_clave or '',
            'categoria': libro.categoria or '',
            'categorias': [cat.nom_cat for cat in libro.categorias.all()],
            'edicion': libro.edicion or '',
        })
    return recomendaciones


def buscar_libros(request):
    query = request.GET.get('q', '').strip()
    try:
        if not query:
            if request.user.is_authenticated:
                return JsonResponse(obtener_recomendaciones_personalizadas(request.user), safe=False)
            return JsonResponse([{'mensaje': "Introduce un término de búsqueda."}], safe=False)

        if request.user.is_authenticated:
            try:
                HistorialBusqueda.objects.create(usuario=request.user, termino_busqueda=query)
            except Exception as e:
                logger.warning(f"Error guardando historial: {e}")

        # Búsqueda por tipo
        if query.startswith('tipo:'):
            tipo = query.split(':', 1)[1].upper()
            if tipo == 'TODOS':
                libros = Libro.objects.all()
            else:
                libros = Libro.objects.filter(tipo__iexact=tipo)
            if libros.exists():
                respuesta = [{'mensaje': f"Aquí tienes los {tipo.lower()}s disponibles:"}]
                for libro in libros:
                    respuesta.append({
                        'titulo': libro.titulo,
                        'autores': ', '.join([a.nombre for a in libro.autores.all()]) or 'Autor desconocido',
                        'img_portada': libro.img_portada.url if libro.img_portada else '',
                        'descripcion': libro.descripcion or '',
                        'pdf': libro.pdf.url if libro.pdf else '',
                        'pdf_url': libro.pdf_url or '',
                        'descarga_autorizada': libro.descarga_autorizada,
                        'tipo': libro.tipo,
                        'categorias': [cat.nom_cat for cat in libro.categorias.all()],
                        'edicion': libro.edicion or '',
                    })
                return JsonResponse(respuesta, safe=False)
            else:
                return JsonResponse([{'mensaje': f"No encontré {tipo.lower()}s disponibles."}], safe=False)

        # Respuestas conversacionales
        respuesta_chat = ChatResponses.procesar_mensaje(query)
        if respuesta_chat.get("mensaje"):
            if respuesta_chat.get("accion") == "novedades":
                # ✅ CORREGIDO: usar fecha_publicacion en lugar de fecha_registro
                ultimos_libros = Libro.objects.prefetch_related('autores', 'categorias').order_by('-fecha_publicacion')[:10]
                if ultimos_libros:
                    resultados = [{
                        'titulo': l.titulo,
                        'autores': ', '.join([a.nombre for a in l.autores.all()]) or 'Autor desconocido',
                        'tipo': l.tipo,
                        'fecha': l.fecha_publicacion.strftime('%d/%m/%Y'),
                        'img_portada': l.img_portada.url if l.img_portada else '',
                        'descripcion': l.descripcion or '',
                        'pdf': l.pdf.url if l.pdf else '',
                        'pdf_url': l.pdf_url or '',
                        'descarga_autorizada': l.descarga_autorizada,
                        'categorias': [cat.nom_cat for cat in l.categorias.all()],
                        'edicion': l.edicion or '',
                    } for l in ultimos_libros]
                    return JsonResponse(resultados, safe=False)
                else:
                    return JsonResponse([{'mensaje': "No hay novedades disponibles."}], safe=False)
            else:
                return JsonResponse([respuesta_chat], safe=False)

        # Búsqueda normal
        query_limpia = limpiar_busqueda(query)
        es_busqueda_autor = 'autor' in query.lower() or 'del autor' in query.lower()
        if es_busqueda_autor:
            nombre_autor = query_limpia.replace('autor', '').replace('del', '').strip()
            if not nombre_autor:
                return JsonResponse([{'mensaje': "¿Podrías decirme el nombre del autor?"}], safe=False)
            libros = Libro.objects.filter(autores__nombre__icontains=nombre_autor).distinct()
        else:
            terminos = query_limpia.split()
            q_titulo_desc = Q()
            q_otros = Q()
            q_titulo_desc |= Q(titulo__icontains=query_limpia) | Q(descripcion__icontains=query_limpia)
            for termino in terminos:
                if len(termino) > 2:
                    q_titulo_desc |= Q(titulo__icontains=termino) | Q(descripcion__icontains=termino)
                    q_otros |= Q(palabra_clave__icontains=termino) | Q(autores__nombre__icontains=termino) | Q(categoria__icontains=termino) | Q(categorias__nom_cat__icontains=termino)
            libros = (Libro.objects.filter(q_titulo_desc) | Libro.objects.filter(q_otros)).distinct()

        if libros.exists():
            respuesta = [{'mensaje': f"Encontré estos documentos relacionados con '{query}':", 'tipo': 'success'}]
            for libro in libros:
                respuesta.append({
                    'titulo': libro.titulo,
                    'autores': ', '.join([a.nombre for a in libro.autores.all()]) or 'Autor desconocido',
                    'img_portada': libro.img_portada.url if libro.img_portada else '',
                    'descripcion': libro.descripcion or '',
                    'pdf': libro.pdf.url if libro.pdf else '',
                    'pdf_url': libro.pdf_url or '',
                    'descarga_autorizada': libro.descarga_autorizada,
                    'tipo': libro.tipo,
                    'categorias': [cat.nom_cat for cat in libro.categorias.all()],
                    'edicion': libro.edicion or '',
                })
            return JsonResponse(respuesta, safe=False)
        else:
            return JsonResponse([{'mensaje': f"No encontré resultados para '{query}'.", 'tipo': 'info'}], safe=False)
    except Exception as e:
        logger.error(f"Error en buscar_libros: {e}")
        return JsonResponse([{'mensaje': "Error en la búsqueda.", 'tipo': 'error'}], safe=False)


def chatbot_view(request):
    return render(request, 'chatbot.html')


@login_required
def obtener_novedades(request):
    try:
        ultimos_libros = Libro.objects.all().order_by('-fecha_publicacion')[:3]
        novedades = []
        for libro in ultimos_libros:
            # ✅ CORREGIDO: categoria es un CharField, no tiene atributo nombre
            categoria_nombre = libro.categoria if libro.categoria else 'Sin categoría'
            novedades.append({
                'titulo': libro.titulo,
                'autores': ', '.join([a.nombre for a in libro.autores.all()]) or 'Autor desconocido',
                'categoria': categoria_nombre,
                'descripcion': libro.descripcion,
                'pdf': libro.pdf.url if libro.pdf else '',
                'descarga_autorizada': libro.descarga_autorizada,
                'img_portada': libro.img_portada.url if libro.img_portada else None,
                'pdf_url': libro.pdf_url,
                'edicion': libro.edicion,
            })
        return JsonResponse({'status': 'success', 'mensaje': 'Últimos libros añadidos:', 'libros': novedades})
    except Exception as e:
        logger.error(f"Error en obtener_novedades: {e}")
        return JsonResponse({'status': 'error', 'mensaje': str(e)})


# ==================== Chat con Groq API y Acceso a BD ====================
def chat_con_gemini(request):
    """Endpoint para chat con Groq API con acceso a base de datos"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            mensaje = data.get('message', '')
            
            if not mensaje:
                return JsonResponse({'error': 'Mensaje vacío', 'success': False}, status=400)
            
            # Verificar si la pregunta es sobre libros disponibles
            palabras_clave_libros = ['libro', 'título', 'autor', 'tiene', 'hay', 'existe', 
                                      'buscar', 'encuentra', 'óleo', 'pintura', 'arte', 
                                      'dibujo', 'escultura', 'diseño', 'recomienda', 'sugiere']
            
            es_pregunta_libro = any(palabra in mensaje.lower() for palabra in palabras_clave_libros)
            
            if es_pregunta_libro:
                # Buscar en la base de datos local
                from django.db.models import Q
                
                terminos = mensaje.lower().split()
                palabras_utiles = [p for p in terminos if len(p) > 2 and p not in ['para', 'por', 'con', 'sin', 'del', 'la', 'los', 'las', 'el', 'un', 'una']]
                
                resultados = []
                
                if palabras_utiles:
                    # Construir consulta
                    q = Q()
                    for palabra in palabras_utiles:
                        q |= Q(titulo__icontains=palabra)
                        q |= Q(descripcion__icontains=palabra)
                        q |= Q(palabra_clave__icontains=palabra)
                        q |= Q(autores__nombre__icontains=palabra)
                        q |= Q(categorias__nom_cat__icontains=palabra)
                    
                    libros = Libro.objects.filter(q).distinct()[:5]
                    
                    if libros.exists():
                        respuesta = "📚 **Encontré estos libros en nuestra biblioteca:**\n\n"
                        for libro in libros:
                            respuesta += f"• **{libro.titulo}**\n"
                            autores = ', '.join([a.nombre for a in libro.autores.all()])
                            if autores:
                                respuesta += f"  ✍️ Autor: {autores}\n"
                            if libro.descripcion:
                                respuesta += f"  📝 {libro.descripcion[:120]}...\n"
                            respuesta += f"  🏷️ Tipo: {libro.get_tipo_display()}\n\n"
                        
                        respuesta += "¿Te gustaría ver más detalles de algún libro?"
                        return JsonResponse({'response': respuesta, 'success': True})
            
            # Si no es pregunta de libro o no hay resultados, usar Groq
            respuesta = get_ai_response(mensaje)
            
            # Guardar en historial
            if request.user.is_authenticated:
                try:
                    HistorialBusqueda.objects.create(
                        usuario=request.user,
                        termino_busqueda=f"[CHAT] {mensaje[:100]}"
                    )
                except Exception as e:
                    logger.warning(f"Error guardando historial de chat: {e}")
            
            return JsonResponse({'response': respuesta, 'success': True})
            
        except json.JSONDecodeError:
            return JsonResponse({'error': 'JSON inválido', 'success': False}, status=400)
        except Exception as e:
            logger.error(f"Error en chat_con_gemini: {e}")
            return JsonResponse({'error': str(e), 'success': False}, status=500)
    
    return JsonResponse({'error': 'Método no permitido'}, status=405)