# views/libro_views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.core.paginator import Paginator
from django.views.decorators.csrf import csrf_exempt
from django.db import IntegrityError
from django.core.files.base import ContentFile
from django.core.files.uploadedfile import InMemoryUploadedFile
from django.urls import reverse
from django.db import models
import logging
import io
import tempfile
import os
import threading
import re

from ..decorators import admin_required
from ..models import Libro, Autor, Categoria, Revista, Coleccion, Imagen
from ..forms import RevistaForm, ColeccionForm, ImagenForm
from ..drive_utils import (
    subir_pdf_a_drive,
    subir_pdf_a_drive_async,
    subir_portada_a_drive_async,
    subir_autorizacion_a_drive_async,
    subir_imagen_a_drive_async,
    subir_revista_pdf_a_drive_async,
    subir_imagen_revista_a_drive_async,
    eliminar_pdf_de_drive,
    eliminar_imagen_de_drive,
    extract_file_id_from_url,
    test_drive_connection
)

logger = logging.getLogger(__name__)


# ============================================
# FUNCIONES AUXILIARES
# ============================================

def extract_file_id_from_url(url):
    """Extrae el ID de archivo de una URL de Google Drive"""
    if not url:
        return None
    
    patterns = [
        r'/file/d/([^/]+)',
        r'id=([^&]+)',
        r'drive\.google\.com/open\?id=([^&]+)',
        r'drive\.google\.com/uc\?id=([^&]+)'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    
    return None


# ============================================
# CRUD LIBROS
# ============================================

@login_required
@admin_required
def listar_libros(request):
    """Lista todos los libros con paginación"""
    libros = Libro.objects.all()
    
    # Obtener el parámetro de ordenamiento
    ordenar = request.GET.get('ordenar', '')
    
    if ordenar == 'fecha_asc':
        libros = libros.order_by('fecha_publicacion')
    elif ordenar == 'fecha_desc':
        libros = libros.order_by('-fecha_publicacion')
    else:
        libros = libros.order_by('-id_libro')
    
    busqueda = request.GET.get('busqueda', '')
    if busqueda:
        libros = libros.filter(
            models.Q(titulo__icontains=busqueda) |
            models.Q(autores__nombre__icontains=busqueda) |
            models.Q(categorias__nom_cat__icontains=busqueda)
        ).distinct()
    
    paginator = Paginator(libros, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'listar_libros.html', {
        'libros': page_obj,
        'usuario': request.user,
        'busqueda': busqueda,
        'ordenar': ordenar,  # ✅ AGREGAR ESTA LÍNEA
    })


@admin_required
def agregar_libro(request):
    """Agrega un nuevo libro al sistema - TODO a Google Drive"""
    autores = Autor.objects.all()
    categorias = Categoria.objects.all()
    
    if request.method == 'POST':
        try:
            titulo = request.POST.get('titulo', '').strip()
            edicion = request.POST.get('edicion', '').strip()
            tipo = request.POST.get('tipo')
            categoria = request.POST.get('categoria')
            descripcion = request.POST.get('descripcion', '').strip()
            autores_seleccionados = request.POST.getlist('autores')
            palabras_claves = request.POST.get('palabras_claves', '').split(',')
            pdf_url = request.POST.get('pdf_url', '').strip()
            google_drive_url = request.POST.get('google_drive_url', '').strip()
            categorias_seleccionadas = request.POST.getlist('categorias')
            
            if not titulo:
                return JsonResponse({'success': False, 'error': 'El título es obligatorio'})
            
            if not tipo:
                return JsonResponse({'success': False, 'error': 'El tipo de material es obligatorio'})
            
            nuevo_libro = Libro(
                titulo=titulo,
                edicion=edicion,
                tipo=tipo,
                categoria=categoria,
                descripcion=descripcion,
                pdf_url=pdf_url,
                google_drive_url=google_drive_url,
                descarga_autorizada=False
            )
            
            nuevo_libro.save()
            libro_id = nuevo_libro.id_libro
            
            # Subir portada a Drive
            if 'portada' in request.FILES:
                portada = request.FILES['portada']
                logger.info(f"📷 Portada detectada: {portada.name}")
                thread = threading.Thread(
                    target=subir_portada_a_drive_async,
                    args=(portada, titulo, libro_id)
                )
                thread.daemon = True
                thread.start()
                messages.info(request, "✅ La portada se está subiendo a Google Drive en segundo plano.")
            
            # Subir PDF a Drive
            if 'pdf' in request.FILES:
                pdf_original = request.FILES['pdf']
                tamaño_mb = pdf_original.size / (1024 * 1024)
                logger.info(f"📄 PDF detectado: {pdf_original.name} ({tamaño_mb:.2f} MB)")
                
                if tamaño_mb > 50:
                    return JsonResponse({
                        'success': False,
                        'error': 'El PDF supera los 50MB. Por favor, comprime el archivo o usa Google Drive URL.'
                    })
                
                thread = threading.Thread(
                    target=subir_pdf_a_drive_async,
                    args=(pdf_original, titulo, libro_id)
                )
                thread.daemon = True
                thread.start()
                messages.info(request, "✅ El PDF se está subiendo a Google Drive en segundo plano.")
            
            # Subir autorización a Drive
            if 'autorizacion' in request.FILES:
                autorizacion = request.FILES['autorizacion']
                logger.info(f"📄 Autorización detectada: {autorizacion.name}")
                thread = threading.Thread(
                    target=subir_autorizacion_a_drive_async,
                    args=(autorizacion, f"{titulo}_autorizacion", libro_id)
                )
                thread.daemon = True
                thread.start()
                messages.info(request, "✅ La autorización se está subiendo a Google Drive en segundo plano.")
            
            # Agregar autores
            nuevo_autor_nombre = request.POST.get('nombre_autor', '').strip()
            if nuevo_autor_nombre:
                autor_existente = Autor.objects.filter(nombre__iexact=nuevo_autor_nombre).first()
                if autor_existente:
                    nuevo_libro.autores.add(autor_existente)
                else:
                    nuevo_autor = Autor.objects.create(nombre=nuevo_autor_nombre.title())
                    nuevo_libro.autores.add(nuevo_autor)
            
            for autor_id in autores_seleccionados:
                try:
                    autor = Autor.objects.get(pk=autor_id)
                    nuevo_libro.autores.add(autor)
                except Autor.DoesNotExist:
                    logger.warning(f"⚠️ Autor {autor_id} no encontrado")
            
            # Agregar categorías
            for categoria_id in categorias_seleccionadas:
                try:
                    cat = Categoria.objects.get(pk=categoria_id)
                    nuevo_libro.categorias.add(cat)
                except Categoria.DoesNotExist:
                    logger.warning(f"⚠️ Categoría {categoria_id} no encontrada")
            
            # Agregar palabras clave
            for palabra in palabras_claves:
                palabra = palabra.strip()
                if palabra:
                    nuevo_libro.agregar_palabras_claves(palabra)
            
            logger.info(f"✅ Libro '{titulo}' creado exitosamente por {request.user.username}")
            
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': True,
                    'message': 'Libro agregado correctamente. Los archivos se están subiendo a Google Drive.',
                    'libro_id': nuevo_libro.id_libro,
                    'redirect_url': reverse('listar_libros')
                })
            
            messages.success(request, f'Libro "{titulo}" agregado correctamente')
            return redirect('listar_libros')
            
        except Exception as e:
            logger.error(f"❌ Error agregando libro: {str(e)}", exc_info=True)
            
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'error': str(e)})
            
            messages.error(request, f'Error al agregar libro: {str(e)}')
            return render(request, 'agregar_libro.html', {'autores': autores, 'categorias': categorias})
    
    return render(request, 'agregar_libro.html', {
        'autores': autores,
        'categorias': categorias
    })


@login_required
@admin_required
def editar_libro(request, libro_id):
    """Edita un libro existente"""
    libro = get_object_or_404(Libro, id_libro=libro_id)
    categorias = Categoria.objects.all()
    autores = Autor.objects.all()
    
    if request.method == 'POST':
        try:
            libro.titulo = request.POST.get('titulo', '').strip()
            libro.edicion = request.POST.get('edicion', '').strip()
            libro.tipo = request.POST.get('tipo')
            libro.descripcion = request.POST.get('descripcion', '').strip()
            libro.categoria = request.POST.get('categoria')
            libro.categorias.set(request.POST.getlist('categorias'))
            libro.pdf_url = request.POST.get('pdf_url', '').strip()
            libro.google_drive_url = request.POST.get('google_drive_url', '').strip()
            
            # Actualizar portada
            if 'portada' in request.FILES:
                if libro.google_drive_portada_url:
                    file_id = extract_file_id_from_url(libro.google_drive_portada_url)
                    if file_id:
                        eliminar_imagen_de_drive(file_id)
                        logger.info(f"🗑️ Portada anterior eliminada de Drive: {file_id}")
                
                thread = threading.Thread(
                    target=subir_portada_a_drive_async,
                    args=(request.FILES['portada'], libro.titulo, libro.id_libro)
                )
                thread.daemon = True
                thread.start()
                messages.info(request, "✅ La nueva portada se está subiendo a Google Drive en segundo plano.")
                libro.google_drive_portada_url = ''
            
            # Actualizar PDF
            if 'pdf' in request.FILES:
                pdf_original = request.FILES['pdf']
                tamaño_mb = pdf_original.size / (1024 * 1024)
                logger.info(f"📄 PDF detectado en edición: {pdf_original.name} ({tamaño_mb:.2f} MB)")
                
                if tamaño_mb > 50:
                    messages.error(request, 'El PDF supera los 50MB. Por favor, comprime el archivo o usa Google Drive URL.')
                    return render(request, 'editar_libro.html', {
                        'libro': libro,
                        'autores': autores,
                        'categorias': categorias,
                        'palabras_claves': libro.palabra_clave.split(',') if libro.palabra_clave else []
                    })
                
                if libro.google_drive_url:
                    file_id = extract_file_id_from_url(libro.google_drive_url)
                    if file_id:
                        eliminar_pdf_de_drive(file_id)
                        logger.info(f"🗑️ PDF anterior eliminado de Drive: {file_id}")
                
                thread = threading.Thread(
                    target=subir_pdf_a_drive_async,
                    args=(pdf_original, libro.titulo, libro.id_libro)
                )
                thread.daemon = True
                thread.start()
                messages.info(request, "✅ El nuevo PDF se está subiendo a Google Drive en segundo plano.")
                libro.google_drive_url = ''
            
            # Actualizar autorización
            if 'autorizacion' in request.FILES:
                if libro.google_drive_autorizacion_url:
                    file_id = extract_file_id_from_url(libro.google_drive_autorizacion_url)
                    if file_id:
                        eliminar_pdf_de_drive(file_id)
                        logger.info(f"🗑️ Autorización anterior eliminada de Drive: {file_id}")
                
                thread = threading.Thread(
                    target=subir_autorizacion_a_drive_async,
                    args=(request.FILES['autorizacion'], f"{libro.titulo}_autorizacion", libro.id_libro)
                )
                thread.daemon = True
                thread.start()
                messages.info(request, "✅ La nueva autorización se está subiendo a Google Drive en segundo plano.")
                libro.google_drive_autorizacion_url = ''
            
            # Actualizar autores
            if 'autores' in request.POST:
                autores_ids = request.POST.getlist('autores')
                if autores_ids:
                    libro.autores.set(autores_ids)
                else:
                    libro.autores.clear()
            
            libro.palabra_clave = request.POST.get('palabras_claves', '')
            libro.save()
            
            logger.info(f"✅ Libro '{libro.titulo}' actualizado por {request.user.username}")
            messages.success(request, f'Libro "{libro.titulo}" actualizado correctamente')
            
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': True,
                    'message': 'Libro actualizado correctamente',
                    'redirect_url': reverse('listar_libros')
                })
            
            return redirect('listar_libros')
            
        except Exception as e:
            logger.error(f"❌ Error editando libro: {str(e)}", exc_info=True)
            
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'error': str(e)}, status=400)
            
            messages.error(request, f'Error al editar libro: {str(e)}')
            return render(request, 'editar_libro.html', {
                'libro': libro,
                'autores': autores,
                'categorias': categorias,
                'palabras_claves': libro.palabra_clave.split(',') if libro.palabra_clave else []
            })
    
    return render(request, 'editar_libro.html', {
        'libro': libro,
        'autores': autores,
        'categorias': categorias,
        'palabras_claves': libro.palabra_clave.split(',') if libro.palabra_clave else []
    })


@login_required
@admin_required
def eliminar_libro(request, libro_id):
    """Elimina un libro del sistema y sus archivos de Google Drive"""
    libro = get_object_or_404(Libro, pk=libro_id)
    
    if request.method == 'POST':
        titulo = libro.titulo
        
        if libro.google_drive_url:
            file_id = extract_file_id_from_url(libro.google_drive_url)
            if file_id:
                eliminar_pdf_de_drive(file_id)
        
        if libro.google_drive_portada_url:
            file_id = extract_file_id_from_url(libro.google_drive_portada_url)
            if file_id:
                eliminar_imagen_de_drive(file_id)
        
        if libro.google_drive_autorizacion_url:
            file_id = extract_file_id_from_url(libro.google_drive_autorizacion_url)
            if file_id:
                eliminar_pdf_de_drive(file_id)
        
        libro.delete()
        logger.info(f"✅ Libro '{titulo}' eliminado por {request.user.username}")
        messages.success(request, f'Libro "{titulo}" eliminado correctamente')
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': True, 'message': 'Libro eliminado'})
        
        return redirect('listar_libros')
    
    return redirect('listar_libros')


@login_required
@admin_required
def cambiar_estado_descarga(request, libro_id):
    """Cambia el estado de autorización de descarga del libro"""
    libro = get_object_or_404(Libro, id_libro=libro_id)
    
    libro.descarga_autorizada = not libro.descarga_autorizada
    libro.save()
    
    estado = "AUTORIZADA" if libro.descarga_autorizada else "RESTRINGIDA"
    logger.info(f"📥 Descarga {estado} para '{libro.titulo}' por {request.user.username}")
    messages.success(request, f'Descarga {estado.lower()} para "{libro.titulo}"')
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'success': True,
            'descarga_autorizada': libro.descarga_autorizada,
            'estado': estado
        })
    
    return redirect('listar_libros')


@login_required
def ver_descargar_libro(request, libro_id):
    """Ver o descargar un libro - Permite visualización embebida"""
    libro = get_object_or_404(Libro, id_libro=libro_id)
    
    es_admin = hasattr(request.user, 'usuario') and request.user.usuario.tipo_usuario == 'Administrador'
    es_modo_embed = request.GET.get('embed') == 'true'
    
    archivo_url = libro.get_pdf_display_url()
    
    if not archivo_url:
        return render(request, 'error_recurso.html', {
            'mensaje': 'No hay archivo disponible para este libro.',
            'libro': libro
        }, status=404)
    
    if es_modo_embed:
        if 'drive.google.com' in archivo_url:
            file_id = extract_file_id_from_url(archivo_url)
            if file_id:
                archivo_url = f'https://drive.google.com/file/d/{file_id}/preview'
        
        return render(request, 'ver_libro_embed.html', {
            'libro': libro,
            'archivo_url': archivo_url,
            'permitir_descarga': libro.descarga_autorizada or es_admin
        })
    
    if not libro.descarga_autorizada and not es_admin:
        return render(request, 'acceso_restringido.html', {
            'libro': libro,
            'mensaje': 'Este libro tiene restringida su descarga. Solo puedes leerlo dentro del sistema.',
            'puede_leer': True
        })
    
    return redirect(archivo_url)


@login_required
@admin_required
def eliminar_autorizacion(request, libro_id):
    """Elimina el archivo de autorización de un libro"""
    libro = get_object_or_404(Libro, id_libro=libro_id)
    
    if request.method == 'POST':
        if libro.google_drive_autorizacion_url:
            file_id = extract_file_id_from_url(libro.google_drive_autorizacion_url)
            if file_id:
                eliminar_pdf_de_drive(file_id)
            
            libro.google_drive_autorizacion_url = None
            libro.save()
        
        logger.info(f"✅ Autorización eliminada para '{libro.titulo}' por {request.user.username}")
        messages.success(request, 'Autorización eliminada correctamente')
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': True})
        
        return redirect('listar_libros')
    
    return redirect('listar_libros')


# ============================================
# CRUD REVISTAS
# ============================================

@login_required
@admin_required
def listar_revistas(request):
    """Lista todas las revistas"""
    revistas = Revista.objects.all().order_by('-id_revista')
    colecciones = Coleccion.objects.all().order_by('orden', 'nomb_colecc')
    return render(request, 'listar_revistas.html', {
        'revistas': revistas,
        'colecciones': colecciones
    })


@login_required
@admin_required
def agregar_revista(request):
    """Agrega una nueva revista - TODO a Google Drive"""
    if request.method == 'POST':
        try:
            if not request.POST.get('coleccion'):
                raise ValueError('La colección es requerida')
            
            coleccion = Coleccion.objects.get(id_coleccion=request.POST['coleccion'])
            nro_revista = request.POST.get('nro_revista')
            nro_revista = int(nro_revista) if nro_revista else None
            
            revista = Revista(
                nro_revista=nro_revista,
                coleccion=coleccion,
                descripcion=request.POST.get('descripcion', '').strip(),
                url=request.POST.get('url', '').strip(),
                google_drive_url='',
                google_drive_img_url=''
            )
            
            # Manejar imagen de portada
            if 'img_portada' in request.FILES:
                imagen_original = request.FILES['img_portada']
                tamaño_mb = imagen_original.size / (1024 * 1024)
                
                if tamaño_mb > 5:
                    raise ValueError('La imagen no puede superar los 5MB')
                
                logger.info(f"📷 Imagen de portada detectada: {imagen_original.name} ({tamaño_mb:.2f} MB)")
            
            # Manejar PDF
            pdf_para_subir = None
            if 'pdf' in request.FILES:
                pdf_original = request.FILES['pdf']
                tamaño_mb = pdf_original.size / (1024 * 1024)
                
                if tamaño_mb > 10:
                    raise ValueError('El PDF no puede superar los 10MB')
                
                logger.info(f"📄 PDF de revista detectado: {pdf_original.name} ({tamaño_mb:.2f} MB)")
                pdf_para_subir = pdf_original
            
            # Guardar la revista
            revista.save()
            revista_id = revista.id_revista
            
            # Subir imagen a Drive
            if 'img_portada' in request.FILES:
                imagen_original = request.FILES['img_portada']
                nombre_imagen = f"{coleccion.nomb_colecc}_{nro_revista or 'portada'}"
                thread_img = threading.Thread(
                    target=subir_imagen_revista_a_drive_async,
                    args=(imagen_original, nombre_imagen, revista_id)
                )
                thread_img.daemon = True
                thread_img.start()
                messages.info(request, "✅ La imagen se está subiendo a Google Drive en segundo plano.")
            
            # Subir PDF a Drive
            if pdf_para_subir:
                nombre_pdf = f"{coleccion.nomb_colecc}_{nro_revista or 'revista'}"
                thread_pdf = threading.Thread(
                    target=subir_revista_pdf_a_drive_async,
                    args=(pdf_para_subir, nombre_pdf, revista_id)
                )
                thread_pdf.daemon = True
                thread_pdf.start()
                messages.info(request, "✅ El PDF se está subiendo a Google Drive en segundo plano.")
            
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': True,
                    'message': 'Revista agregada correctamente',
                    'id': revista.id_revista
                })
            
            messages.success(request, 'Revista agregada correctamente')
            return redirect('listar_revistas')
            
        except Exception as e:
            logger.error(f"❌ Error agregando revista: {str(e)}")
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'message': str(e)}, status=400)
            messages.error(request, str(e))
            return redirect('agregar_revista')
    
    colecciones = Coleccion.objects.all().order_by('nomb_colecc')
    return render(request, 'agregar_revista.html', {
        'colecciones': colecciones,
        'max_upload_size_mb': {'imagen': 5, 'pdf': 10}
    })


@login_required
@admin_required
def modificar_revista(request, id_revista):
    """Modifica una revista existente"""
    revista = get_object_or_404(Revista, id_revista=id_revista)
    
    if request.method == 'POST':
        form = RevistaForm(request.POST, request.FILES, instance=revista)
        
        if form.is_valid():
            try:
                # Guardar la revista
                revista = form.save()
                
                # Si hay nueva imagen, subir a Drive
                if 'img_portada' in request.FILES:
                    # Eliminar imagen anterior
                    if revista.google_drive_img_url:
                        file_id = extract_file_id_from_url(revista.google_drive_img_url)
                        if file_id:
                            eliminar_imagen_de_drive(file_id)
                    
                    imagen_original = request.FILES['img_portada']
                    nombre_imagen = f"{revista.coleccion.nomb_colecc}_{revista.nro_revista or 'portada'}"
                    thread_img = threading.Thread(
                        target=subir_imagen_revista_a_drive_async,
                        args=(imagen_original, nombre_imagen, revista.id_revista)
                    )
                    thread_img.daemon = True
                    thread_img.start()
                    messages.info(request, "✅ La nueva imagen se está subiendo a Google Drive en segundo plano.")
                    revista.google_drive_img_url = ''
                    revista.save()
                
                # Si hay nuevo PDF, subir a Drive
                if 'pdf' in request.FILES:
                    # Eliminar PDF anterior
                    if revista.google_drive_url:
                        file_id = extract_file_id_from_url(revista.google_drive_url)
                        if file_id:
                            eliminar_pdf_de_drive(file_id)
                    
                    pdf_original = request.FILES['pdf']
                    nombre_pdf = f"{revista.coleccion.nomb_colecc}_{revista.nro_revista or 'revista'}"
                    thread_pdf = threading.Thread(
                        target=subir_revista_pdf_a_drive_async,
                        args=(pdf_original, nombre_pdf, revista.id_revista)
                    )
                    thread_pdf.daemon = True
                    thread_pdf.start()
                    messages.info(request, "✅ El nuevo PDF se está subiendo a Google Drive en segundo plano.")
                    revista.google_drive_url = ''
                    revista.save()
                
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({
                        'success': True,
                        'message': '✅ Revista actualizada correctamente',
                        'redirect_url': reverse('listar_revistas')
                    })
                
                messages.success(request, '✅ Revista actualizada correctamente')
                return redirect('listar_revistas')
                
            except Exception as e:
                logger.error(f"❌ Error al modificar revista: {e}")
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({
                        'success': False,
                        'message': f'Error: {str(e)}'
                    })
                messages.error(request, f'Error: {str(e)}')
        else:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': False,
                    'message': 'Error de validación en el formulario',
                    'errors': form.errors
                })
            messages.error(request, 'Por favor corrige los errores del formulario')
    
    form = RevistaForm(instance=revista)
    return render(request, 'modificar_revista.html', {
        'form': form,
        'revista': revista
    })


@login_required
@admin_required
def eliminar_revista(request, id_revista):
    """Elimina una revista y sus archivos de Google Drive"""
    if request.method == 'POST':
        revista = get_object_or_404(Revista, id_revista=id_revista)
        
        # Eliminar PDF de Google Drive
        if revista.google_drive_url:
            file_id = extract_file_id_from_url(revista.google_drive_url)
            if file_id:
                eliminar_pdf_de_drive(file_id)
        
        # Eliminar imagen de Google Drive
        if revista.google_drive_img_url:
            file_id = extract_file_id_from_url(revista.google_drive_img_url)
            if file_id:
                eliminar_imagen_de_drive(file_id)
        
        revista.delete()
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': True})
        messages.success(request, 'Revista eliminada correctamente')
        return redirect('listar_revistas')
    
    return JsonResponse({'success': False})


# ============================================
# CRUD COLECCIONES
# ============================================

@login_required
@admin_required
def agregar_coleccion(request):
    """Agrega una nueva colección"""
    if request.method == 'POST' and request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        try:
            nueva_coleccion = Coleccion.objects.create(
                nomb_colecc=request.POST.get('nomb_colecc'),
                descripcion=request.POST.get('descripcion')
            )
            return JsonResponse({
                'success': True,
                'id_coleccion': nueva_coleccion.id_coleccion,
                'nomb_colecc': nueva_coleccion.nomb_colecc
            })
        except Exception as e:
            logger.error(f"❌ Error agregando colección: {str(e)}")
            return JsonResponse({'success': False, 'message': str(e)})
    return JsonResponse({'success': False, 'message': 'Método no permitido'})


@login_required
@admin_required
def modificar_coleccion(request, id_coleccion):
    """Modifica una colección existente"""
    coleccion = get_object_or_404(Coleccion, id_coleccion=id_coleccion)
    
    if request.method == 'POST':
        form = ColeccionForm(request.POST, instance=coleccion)
        if form.is_valid():
            form.save()
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': True, 'message': 'Colección actualizada'})
            return redirect('listar_revistas')
        else:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'message': 'Error', 'errors': form.errors})
    else:
        form = ColeccionForm(instance=coleccion)
    
    return render(request, 'modificar_coleccion.html', {'form': form, 'coleccion': coleccion})


@login_required
@admin_required
def eliminar_coleccion(request, id_coleccion):
    """Elimina una colección"""
    if request.method == 'POST':
        coleccion = get_object_or_404(Coleccion, id_coleccion=id_coleccion)
        coleccion.delete()
        return JsonResponse({'success': True})
    return JsonResponse({'success': False})


@csrf_exempt
@admin_required
def actualizar_orden_colecciones(request):
    """Actualiza el orden de las colecciones"""
    if request.method == 'POST':
        coleccion_ids = request.POST.getlist('coleccion_ids[]')
        for index, coleccion_id in enumerate(coleccion_ids):
            Coleccion.objects.filter(id_coleccion=coleccion_id).update(orden=index)
        return JsonResponse({'status': 'success'})
    return JsonResponse({'status': 'error'}, status=400)


# ============================================
# CRUD IMÁGENES
# ============================================

@login_required
@admin_required
def listar_imagenes(request):
    """Lista todas las imágenes"""
    imagenes = Imagen.objects.all().order_by('-id_Imagen')
    paginator = Paginator(imagenes, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return render(request, 'lista_imagenes.html', {'page_obj': page_obj})


@admin_required
def agregar_imagen(request):
    """Agrega una nueva imagen - TODO a Google Drive"""
    categorias = Categoria.objects.all()
    is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
    
    if request.method == 'POST':
        try:
            titulo = request.POST.get('titulo')
            descripcion = request.POST.get('descripcion', '')
            autorImg = request.POST.get('autorImg')
            
            if not titulo:
                if is_ajax:
                    return JsonResponse({'success': False, 'error': 'El título es obligatorio'}, status=400)
                messages.error(request, 'El título es obligatorio')
                return render(request, 'agregar_imagen.html', {'categorias': categorias})
            
            if not autorImg:
                if is_ajax:
                    return JsonResponse({'success': False, 'error': 'El autor es obligatorio'}, status=400)
                messages.error(request, 'El autor es obligatorio')
                return render(request, 'agregar_imagen.html', {'categorias': categorias})
            
            if 'img_portada' not in request.FILES:
                if is_ajax:
                    return JsonResponse({'success': False, 'error': 'Debes seleccionar una imagen'}, status=400)
                messages.error(request, 'Debes seleccionar una imagen')
                return render(request, 'agregar_imagen.html', {'categorias': categorias})
            
            imagen_original = request.FILES['img_portada']
            tamaño_mb = imagen_original.size / (1024 * 1024)
            
            if tamaño_mb > 5:
                if is_ajax:
                    return JsonResponse({'success': False, 'error': 'La imagen no puede superar los 5MB'}, status=400)
                messages.error(request, 'La imagen no puede superar los 5MB')
                return render(request, 'agregar_imagen.html', {'categorias': categorias})
            
            nombre_archivo = imagen_original.name
            contenido_bytes = imagen_original.read()
            imagen_original.seek(0)
            
            nueva_imagen = Imagen(
                titulo=titulo,
                descripcion=descripcion,
                autorImg=autorImg,
            )
            
            nueva_imagen.save()
            imagen_id = nueva_imagen.id_Imagen
            
            # Subir imagen a Drive
            try:
                thread = threading.Thread(
                    target=subir_imagen_a_drive_async,
                    args=(contenido_bytes, nombre_archivo, imagen_id)
                )
                thread.daemon = True
                thread.start()
                logger.info(f"🔄 Hilo de subida a Drive iniciado para imagen ID {imagen_id}")
            except Exception as e:
                logger.error(f"⚠️ Error iniciando subida a Drive: {e}")
            
            # Agregar categorías
            for cat_id in request.POST.getlist('categorias'):
                try:
                    categoria = Categoria.objects.get(pk=cat_id)
                    nueva_imagen.categorias.add(categoria)
                except:
                    pass
            
            if is_ajax:
                return JsonResponse({
                    'success': True,
                    'message': 'Imagen agregada correctamente',
                    'id': nueva_imagen.id_Imagen
                })
            
            messages.success(request, 'Imagen agregada correctamente')
            return redirect('lista_imagenes')
            
        except Exception as e:
            logger.error(f"❌ Error agregando imagen: {str(e)}", exc_info=True)
            if is_ajax:
                return JsonResponse({'success': False, 'error': f'Error: {str(e)}'}, status=500)
            messages.error(request, f'Error: {str(e)}')
            return render(request, 'agregar_imagen.html', {'categorias': categorias, 'error': str(e)})
    
    return render(request, 'agregar_imagen.html', {'categorias': categorias})


@login_required
@admin_required
def editar_imagen(request, id_imagen):
    """Edita una imagen existente"""
    imagen = get_object_or_404(Imagen, pk=id_imagen)
    categorias = Categoria.objects.all()
    
    if request.method == 'POST':
        try:
            imagen.titulo = request.POST.get('titulo')
            imagen.descripcion = request.POST.get('descripcion', '')
            imagen.autorImg = request.POST.get('autorImg')
            
            # Subir nueva imagen a Drive
            if 'img_portada' in request.FILES:
                # Eliminar imagen anterior de Drive
                if imagen.google_drive_url:
                    file_id = extract_file_id_from_url(imagen.google_drive_url)
                    if file_id:
                        eliminar_imagen_de_drive(file_id)
                        logger.info(f"🗑️ Imagen anterior eliminada de Drive: {file_id}")
                
                imagen_original = request.FILES['img_portada']
                contenido_bytes = imagen_original.read()
                imagen_original.seek(0)
                
                thread = threading.Thread(
                    target=subir_imagen_a_drive_async,
                    args=(contenido_bytes, imagen.titulo, imagen.id_Imagen)
                )
                thread.daemon = True
                thread.start()
                messages.info(request, "✅ La nueva imagen se está subiendo a Google Drive en segundo plano.")
            
            imagen.save()
            imagen.categorias.set(request.POST.getlist('categorias'))
            messages.success(request, "Imagen actualizada correctamente")
            return redirect('lista_imagenes')
            
        except Exception as e:
            logger.error(f"❌ Error editando imagen: {str(e)}")
            messages.error(request, f'Error: {str(e)}')
            return render(request, 'editar_imagen.html', {'imagen': imagen, 'categorias': categorias})
    
    return render(request, 'editar_imagen.html', {'imagen': imagen, 'categorias': categorias})


@admin_required
def eliminar_imagen(request, pk):
    """Elimina una imagen y su archivo de Google Drive"""
    imagen = get_object_or_404(Imagen, pk=pk)
    
    if request.method == 'POST':
        # Eliminar de Google Drive
        if imagen.google_drive_url:
            file_id = extract_file_id_from_url(imagen.google_drive_url)
            if file_id:
                eliminar_imagen_de_drive(file_id)
                logger.info(f"🗑️ Imagen eliminada de Drive: {file_id}")
        
        imagen.delete()
        messages.success(request, "Imagen eliminada correctamente")
        return redirect('lista_imagenes')
    
    return redirect('lista_imagenes')


@login_required
def editar_marca(request, id_imagen):
    """Aplica marca de agua a una imagen"""
    from PIL import Image as PILImage
    import io
    from django.core.files.base import ContentFile
    
    imagen = get_object_or_404(Imagen, pk=id_imagen)
    
    if request.method == 'POST':
        try:
            if 'marca_agua' in request.FILES and imagen.google_drive_url:
                # TODO: Descargar imagen de Drive, aplicar marca, volver a subir
                messages.info(request, "Funcionalidad en desarrollo - marca de agua con Google Drive")
            else:
                messages.warning(request, 'No hay imagen para aplicar marca de agua')
        except Exception as e:
            logger.error(f"❌ Error aplicando marca de agua: {str(e)}")
            messages.error(request, f'Error: {str(e)}')
        return redirect('lista_imagenes')
    
    return render(request, 'editar_marca.html', {'imagen': imagen})


# ============================================
# FUNCIÓN DE PRUEBA
# ============================================

@login_required
@admin_required
def test_drive(request):
    """Prueba la conexión con Google Drive"""
    if not request.user.is_superuser:
        return JsonResponse({'error': 'No autorizado'}, status=403)
    
    resultado = test_drive_connection()
    return JsonResponse({
        'success': resultado,
        'message': 'Conexión exitosa a Google Drive' if resultado else 'Error conectando a Google Drive'
    })