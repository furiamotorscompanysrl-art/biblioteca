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
import logging
import io
import tempfile
import os
import threading

from ..decorators import admin_required
from ..models import Libro, Autor, Categoria, Revista, Coleccion, Imagen
from ..forms import RevistaForm, ColeccionForm, ImagenForm
from ..drive_utils import subir_pdf_a_drive

logger = logging.getLogger(__name__)


# ============================================
# FUNCIÓN DE SUBIDA ASÍNCRONA A GOOGLE DRIVE
# ============================================
def subir_pdf_a_drive_async(pdf_original, nombre_archivo, libro_id):
    """Sube un PDF a Google Drive en segundo plano"""
    try:
        from ..models import Libro
        
        # Subir a Drive
        drive_url = subir_pdf_a_drive(pdf_original, nombre_archivo)
        
        if drive_url:
            # Actualizar el libro con la URL de Drive
            libro = Libro.objects.get(id_libro=libro_id)
            libro.google_drive_url = drive_url
            libro.pdf = None
            libro.save()
            logger.info(f"✅ PDF subido asíncronamente a Google Drive: {drive_url} (Libro ID: {libro_id})")
        else:
            logger.error(f"❌ Falló subida asíncrona a Drive para libro {libro_id}")
    except Exception as e:
        logger.error(f"❌ Error en subida asíncrona a Drive: {str(e)}")


# ==================== CRUD Libros ====================
@login_required
@admin_required
def listar_libros(request):
    libros = Libro.objects.all()
    if request.GET.get('ordenar') == 'fecha_asc':
        libros = libros.order_by('fecha_publicacion')
    elif request.GET.get('ordenar') == 'fecha_desc':
        libros = libros.order_by('-fecha_publicacion')
    else:
        libros = libros.order_by('-id_libro')
    paginator = Paginator(libros, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return render(request, 'listar_libros.html', {'libros': page_obj, 'usuario': request.user})


@admin_required
def agregar_libro(request):
    autores = Autor.objects.all()
    categorias = Categoria.objects.all()
    
    if request.method == 'POST':
        try:
            titulo = request.POST.get('titulo')
            edicion = request.POST.get('edicion')
            tipo = request.POST.get('tipo')
            categoria = request.POST.get('categoria')
            descripcion = request.POST.get('descripcion', '').strip()
            autores_seleccionados = request.POST.getlist('autores')
            palabras_claves = request.POST.get('palabras_claves', '').split(',')
            pdf_url = request.POST.get('pdf_url')
            google_drive_url = request.POST.get('google_drive_url')
            categorias_seleccionadas = request.POST.getlist('categorias')
            
            # Crear el libro (por defecto descarga restringida)
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
            
            # Manejo de portada
            if 'portada' in request.FILES:
                nuevo_libro.img_portada = request.FILES['portada']
                logger.info(f"Portada agregada: {request.FILES['portada'].name}")
            
            # ============================================
            # MANEJO DE PDF - SUBIDA ASÍNCRONA A DRIVE
            # ============================================
            pdf_para_subir = None
            if 'pdf' in request.FILES:
                pdf_original = request.FILES['pdf']
                tamaño_mb = pdf_original.size / (1024 * 1024)
                
                if tamaño_mb > 10:
                    logger.info(f"📄 PDF grande detectado: {tamaño_mb:.1f}MB. Se subirá a Google Drive en segundo plano...")
                    # Guardar el PDF original para subirlo después
                    pdf_para_subir = pdf_original
                    messages.info(request, "✅ El PDF se está subiendo a Google Drive en segundo plano. La URL aparecerá en breve.")
                else:
                    # PDFs pequeños a Cloudinary
                    nuevo_libro.pdf = pdf_original
                    logger.info(f"📄 PDF de {tamaño_mb:.1f}MB dentro del límite de Cloudinary")
            
            # Guardar el libro primero
            nuevo_libro.save()
            libro_id = nuevo_libro.id_libro
            
            # Si hay PDF grande, subirlo en segundo plano
            if pdf_para_subir:
                thread = threading.Thread(
                    target=subir_pdf_a_drive_async,
                    args=(pdf_para_subir, titulo, libro_id)
                )
                thread.daemon = True
                thread.start()
                logger.info(f"🔄 Hilo de subida a Drive iniciado para libro ID {libro_id}")
            
            # Autorización
            if 'autorizacion' in request.FILES:
                nuevo_libro.archivo_autorizacion = request.FILES['autorizacion']
                nuevo_libro.save()
                logger.info(f"Archivo de autorización agregado: {request.FILES['autorizacion'].name}")

            # Agregar nuevo autor si se proporcionó
            nuevo_autor_nombre = request.POST.get('nombre_autor')
            if nuevo_autor_nombre and nuevo_autor_nombre.strip():
                autor_existente = Autor.objects.filter(nombre=nuevo_autor_nombre).first()
                if autor_existente:
                    nuevo_libro.autores.add(autor_existente)
                else:
                    nuevo_autor = Autor.objects.create(nombre=nuevo_autor_nombre)
                    nuevo_libro.autores.add(nuevo_autor)

            # Agregar autores seleccionados
            for autor_id in autores_seleccionados:
                try:
                    autor = Autor.objects.get(pk=autor_id)
                    nuevo_libro.autores.add(autor)
                except:
                    pass
            
            # Agregar categorías seleccionadas
            for categoria_id in categorias_seleccionadas:
                try:
                    cat = Categoria.objects.get(pk=categoria_id)
                    nuevo_libro.categorias.add(cat)
                except:
                    pass
            
            # Agregar palabras clave
            for palabra in palabras_claves:
                if palabra.strip():
                    nuevo_libro.agregar_palabras_claves(palabra.strip())
            
            logger.info(f"Libro '{titulo}' creado exitosamente por {request.user.username}")
            return JsonResponse({'success': True, 'message': 'Libro agregado', 'libro_id': nuevo_libro.id_libro})
            
        except Exception as e:
            logger.error(f"Error agregando libro: {str(e)}", exc_info=True)
            return JsonResponse({'success': False, 'error': str(e)})
    
    context = {'autores': autores, 'categorias': categorias}
    return render(request, 'agregar_libro.html', context)


@login_required
@admin_required
def editar_libro(request, libro_id):
    libro = get_object_or_404(Libro, id_libro=libro_id)
    categorias = Categoria.objects.all()
    
    if request.method == 'POST':
        try:
            libro.titulo = request.POST.get('titulo').strip()
            libro.edicion = request.POST.get('edicion', '').strip()
            libro.tipo = request.POST.get('tipo')
            libro.descripcion = request.POST.get('descripcion', '').strip()
            libro.categoria = request.POST.get('categoria')
            libro.categorias.set(request.POST.getlist('categorias'))
            
            # Actualizar URLs
            libro.pdf_url = request.POST.get('pdf_url', '').strip()
            libro.google_drive_url = request.POST.get('google_drive_url', '').strip()
            
            # Manejo de PDF en edición
            if 'pdf' in request.FILES and not libro.google_drive_url:
                pdf_original = request.FILES['pdf']
                tamaño_mb = pdf_original.size / (1024 * 1024)
                
                if tamaño_mb > 10:
                    logger.info(f"📄 PDF grande detectado en edición: {tamaño_mb:.1f}MB. Subiendo a Drive en segundo plano...")
                    # Guardar el libro primero
                    libro.save()
                    # Subir en segundo plano
                    thread = threading.Thread(
                        target=subir_pdf_a_drive_async,
                        args=(pdf_original, libro.titulo, libro.id_libro)
                    )
                    thread.daemon = True
                    thread.start()
                    messages.info(request, "✅ El PDF se está subiendo a Google Drive en segundo plano.")
                else:
                    libro.pdf = pdf_original
                    libro.pdf_url = ''
                    libro.save()
            
            if 'portada' in request.FILES:
                libro.img_portada = request.FILES['portada']
            if 'autorizacion' in request.FILES:
                libro.archivo_autorizacion = request.FILES['autorizacion']
            if 'autores' in request.POST:
                autores = request.POST.getlist('autores')
                if autores:
                    libro.autores.set(autores)
                else:
                    libro.autores.clear()
            libro.palabra_clave = request.POST.get('palabras_claves', '')
            libro.save()
            
            logger.info(f"Libro '{libro.titulo}' actualizado por {request.user.username}")
            messages.success(request, f'Libro "{libro.titulo}" actualizado')
            return JsonResponse({'success': True, 'message': 'Libro actualizado'})
        except Exception as e:
            logger.error(f"Error editando libro: {str(e)}", exc_info=True)
            return JsonResponse({'success': False, 'error': str(e)}, status=400)
    
    context = {
        'libro': libro,
        'autores': Autor.objects.all(),
        'categorias': categorias,
        'palabras_claves': libro.palabra_clave.split(',') if libro.palabra_clave else []
    }
    return render(request, 'editar_libro.html', context)


@login_required
@admin_required
def eliminar_libro(request, libro_id):
    """Elimina un libro del sistema y su PDF de Google Drive"""
    libro = get_object_or_404(Libro, pk=libro_id)
    
    if request.method == 'POST':
        titulo = libro.titulo
        
        # Eliminar PDF de Google Drive si existe
        if libro.google_drive_url:
            try:
                from ..drive_utils import eliminar_pdf_de_drive
                # Extraer el ID del archivo de la URL
                file_id = None
                if '/file/d/' in libro.google_drive_url:
                    file_id = libro.google_drive_url.split('/file/d/')[1].split('/')[0]
                elif 'id=' in libro.google_drive_url:
                    file_id = libro.google_drive_url.split('id=')[1].split('&')[0]
                
                if file_id:
                    resultado = eliminar_pdf_de_drive(file_id)
                    if resultado:
                        logger.info(f"✅ PDF eliminado de Google Drive: {file_id}")
                        messages.success(request, f"PDF eliminado de Google Drive")
                    else:
                        logger.warning(f"⚠️ No se pudo eliminar PDF de Drive: {file_id}")
                else:
                    logger.warning(f"No se pudo extraer ID de Drive URL: {libro.google_drive_url}")
            except Exception as e:
                logger.error(f"Error eliminando PDF de Drive: {e}")
        
        # Eliminar archivo de Cloudinary si existe
        if libro.pdf:
            try:
                libro.pdf.delete(save=False)
                logger.info(f"PDF eliminado de Cloudinary")
            except Exception as e:
                logger.error(f"Error eliminando PDF de Cloudinary: {e}")
        
        # Eliminar el libro de la base de datos
        libro.delete()
        logger.info(f"Libro '{titulo}' eliminado por {request.user.username}")
        messages.success(request, f'Libro "{titulo}" eliminado correctamente')
        
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
    logger.info(f"Descarga {estado} para '{libro.titulo}' por {request.user.username}")
    messages.success(request, f'Descarga {estado.lower()} para "{libro.titulo}"')
    
    return redirect('listar_libros')


@login_required
def ver_descargar_libro(request, libro_id):
    libro = get_object_or_404(Libro, id_libro=libro_id)
    
    es_admin = hasattr(request.user, 'usuario') and request.user.usuario.tipo_usuario == 'Administrador'
    es_modo_embed = request.GET.get('embed') == 'true'
    
    # Obtener URL del archivo (siempre)
    archivo_url = libro.get_pdf_display_url()
    
    # Si no hay archivo disponible
    if not archivo_url:
        return render(request, 'error_recurso.html', {'mensaje': 'No hay archivo disponible.'}, status=404)
    
    # Modo embebido - mostrar visor (siempre, independientemente de permisos)
    if es_modo_embed:
        # Formatear URL de Google Drive para embebido
        if 'drive.google.com' in archivo_url:
            file_id = None
            if '/file/d/' in archivo_url:
                file_id = archivo_url.split('/file/d/')[1].split('/')[0]
            elif 'id=' in archivo_url:
                file_id = archivo_url.split('id=')[1].split('&')[0]
            if file_id:
                archivo_url = f'https://drive.google.com/file/d/{file_id}/preview'
        
        return render(request, 'ver_libro_embed.html', {
            'libro': libro,
            'archivo_url': archivo_url,
            'permitir_descarga': libro.descarga_autorizada or es_admin
        })
    
    # Si no tiene permiso de descarga y no es modo embed, mostrar página de restricción
    if not libro.descarga_autorizada and not es_admin:
        return render(request, 'acceso_restringido.html', {
            'libro': libro,
            'mensaje': 'Este libro tiene restringida su descarga. Solo puedes leerlo dentro del sistema.'
        })
    
    # Modo normal con permiso de descarga - redirigir
    return redirect(archivo_url)


@login_required
@admin_required
def eliminar_autorizacion(request, libro_id):
    """Elimina el archivo de autorización de un libro"""
    libro = get_object_or_404(Libro, id_libro=libro_id)
    
    if request.method == 'POST':
        if libro.archivo_autorizacion:
            libro.archivo_autorizacion.delete(save=False)
            libro.archivo_autorizacion = None
            libro.save()
            logger.info(f"Autorización eliminada para '{libro.titulo}'")
            messages.success(request, f'Autorización eliminada')
            
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': True})
    
    return redirect('listar_libros')


# ==================== CRUD Revistas ====================

@login_required
@admin_required
def listar_revistas(request):
    revistas = Revista.objects.all()
    colecciones = Coleccion.objects.all()
    return render(request, 'listar_revistas.html', {'revistas': revistas, 'colecciones': colecciones})


@login_required
@admin_required
def agregar_revista(request):
    if request.method == 'POST':
        try:
            if not request.POST.get('coleccion'):
                raise ValueError('La colección es requerida')
            coleccion = Coleccion.objects.get(id_coleccion=request.POST['coleccion'])
            nro_revista = request.POST.get('nro_revista')
            nro_revista = int(nro_revista) if nro_revista else None
            if not request.FILES.get('img_portada'):
                raise ValueError('La imagen de portada es requerida')
            revista = Revista(
                nro_revista=nro_revista,
                coleccion=coleccion,
                descripcion=request.POST.get('descripcion', '').strip(),
                img_portada=request.FILES.get('img_portada'),
                pdf=request.FILES.get('pdf'),
                url=request.POST.get('url', '').strip(),
                google_drive_url=request.POST.get('google_drive_url', '').strip()
            )
            revista.save()
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': True, 'message': 'Revista agregada', 'id': revista.id_revista})
            messages.success(request, 'Revista agregada')
            return redirect('listar_revistas')
        except Exception as e:
            logger.error(f"Error agregando revista: {str(e)}")
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'message': str(e)}, status=400)
            messages.error(request, str(e))
            return redirect('agregar_revista')
    colecciones = Coleccion.objects.all().order_by('nomb_colecc')
    return render(request, 'agregar_revista.html', {'colecciones': colecciones, 'max_upload_size_mb': {'imagen': 5, 'pdf': 10}})


@login_required
@admin_required
def modificar_revista(request, id_revista):
    revista = get_object_or_404(Revista, id_revista=id_revista)
    if request.method == 'POST':
        form = RevistaForm(request.POST, request.FILES, instance=revista)
        if form.is_valid():
            try:
                revista = form.save()
                return JsonResponse({'success': True, 'message': 'Revista actualizada', 'data': {'id': revista.id_revista}})
            except Exception as e:
                logger.error(f"Error modificando revista: {str(e)}")
                return JsonResponse({'success': False, 'message': str(e)}, status=500)
        else:
            return JsonResponse({'success': False, 'message': 'Errores en formulario', 'errors': form.errors}, status=400)
    form = RevistaForm(instance=revista)
    return render(request, 'modificar_revista.html', {'form': form, 'revista': revista, 'max_upload_size_mb': {'imagen': 5, 'pdf': 10}})


@login_required
@admin_required
def eliminar_revista(request, id_revista):
    if request.method == 'POST':
        revista = get_object_or_404(Revista, id_revista=id_revista)
        revista.delete()
        return JsonResponse({'success': True})
    return JsonResponse({'success': False})


@login_required
@admin_required
def agregar_coleccion(request):
    if request.method == 'POST' and request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        try:
            nueva_coleccion = Coleccion.objects.create(
                nomb_colecc=request.POST.get('nomb_colecc'),
                descripcion=request.POST.get('descripcion')
            )
            return JsonResponse({'success': True, 'id_coleccion': nueva_coleccion.id_coleccion, 'nomb_colecc': nueva_coleccion.nomb_colecc})
        except Exception as e:
            logger.error(f"Error agregando colección: {str(e)}")
            return JsonResponse({'success': False, 'message': str(e)})
    return JsonResponse({'success': False, 'message': 'Método no permitido'})


@login_required
@admin_required
def modificar_coleccion(request, id_coleccion):
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
    if request.method == 'POST':
        coleccion = get_object_or_404(Coleccion, id_coleccion=id_coleccion)
        coleccion.delete()
        return JsonResponse({'success': True})
    return JsonResponse({'success': False})


@csrf_exempt
@admin_required
def actualizar_orden_colecciones(request):
    if request.method == 'POST':
        coleccion_ids = request.POST.getlist('coleccion_ids[]')
        for index, coleccion_id in enumerate(coleccion_ids):
            Coleccion.objects.filter(id_coleccion=coleccion_id).update(orden=index)
        return JsonResponse({'status': 'success'})
    return JsonResponse({'status': 'error'}, status=400)


# ==================== CRUD Imágenes ======================

@login_required
@admin_required
def listar_imagenes(request):
    imagenes = Imagen.objects.all().order_by('-id_Imagen')
    paginator = Paginator(imagenes, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return render(request, 'lista_imagenes.html', {'page_obj': page_obj})


@admin_required
def agregar_imagen(request):
    categorias = Categoria.objects.all()
    
    # Detectar si es una petición AJAX
    is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
    
    if request.method == 'POST':
        try:
            titulo = request.POST.get('titulo')
            descripcion = request.POST.get('descripcion', '')
            autorImg = request.POST.get('autorImg')
            
            # Validaciones
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
            
            nueva_imagen = Imagen(
                titulo=titulo,
                descripcion=descripcion,
                autorImg=autorImg,
            )
            
            # Procesar imagen
            if 'img_portada' in request.FILES:
                imagen = request.FILES['img_portada']
                # Validar tamaño (5MB)
                if imagen.size > 5 * 1024 * 1024:
                    if is_ajax:
                        return JsonResponse({'success': False, 'error': 'La imagen no puede superar los 5MB'}, status=400)
                    messages.error(request, 'La imagen no puede superar los 5MB')
                    return render(request, 'agregar_imagen.html', {'categorias': categorias})
                nueva_imagen.img_portada = imagen
            
            if 'pdf' in request.FILES:
                pdf = request.FILES['pdf']
                if pdf.size > 10 * 1024 * 1024:
                    if is_ajax:
                        return JsonResponse({'success': False, 'error': 'El PDF no puede superar los 10MB'}, status=400)
                    messages.error(request, 'El PDF no puede superar los 10MB')
                    return render(request, 'agregar_imagen.html', {'categorias': categorias})
                nueva_imagen.pdf = pdf
            
            nueva_imagen.save()
            
            # Agregar categorías
            for cat_id in request.POST.getlist('categorias'):
                try:
                    categoria = Categoria.objects.get(pk=cat_id)
                    nueva_imagen.categorias.add(categoria)
                except:
                    pass
            
            # ✅ PARA AJAX: Devolver JSON (esto es lo que espera tu JavaScript)
            if is_ajax:
                return JsonResponse({
                    'success': True, 
                    'message': 'Imagen agregada correctamente',
                    'id': nueva_imagen.id_Imagen
                })
            
            # Para peticiones normales (no AJAX)
            messages.success(request, 'Imagen agregada correctamente')
            return redirect('lista_imagenes')
            
        except Exception as e:
            logger.error(f"Error agregando imagen: {str(e)}", exc_info=True)
            if is_ajax:
                return JsonResponse({'success': False, 'error': str(e)}, status=500)
            messages.error(request, f'Error: {str(e)}')
            return render(request, 'agregar_imagen.html', {'categorias': categorias, 'error': str(e)})
    
    return render(request, 'agregar_imagen.html', {'categorias': categorias})
    
@login_required
@admin_required
def editar_imagen(request, id_imagen):
    imagen = get_object_or_404(Imagen, pk=id_imagen)
    categorias = Categoria.objects.all()
    if request.method == 'POST':
        try:
            imagen.titulo = request.POST.get('titulo')
            imagen.descripcion = request.POST.get('descripcion', '')
            imagen.autorImg = request.POST.get('autorImg')
            
            if 'img_portada' in request.FILES:
                imagen.img_portada = request.FILES['img_portada']
            if 'pdf' in request.FILES:
                imagen.pdf = request.FILES['pdf']
            
            imagen.save()
            imagen.categorias.set(request.POST.getlist('categorias'))
            messages.success(request, "Imagen actualizada")
            return redirect('lista_imagenes')
        except Exception as e:
            logger.error(f"Error editando imagen: {str(e)}")
            messages.error(request, f'Error: {str(e)}')
            return render(request, 'editar_imagen.html', {'imagen': imagen, 'categorias': categorias})
    return render(request, 'editar_imagen.html', {'imagen': imagen, 'categorias': categorias})


@admin_required
def eliminar_imagen(request, pk):
    imagen = get_object_or_404(Imagen, pk=pk)
    if request.method == 'POST':
        imagen.delete()
        messages.success(request, "Imagen eliminada")
        return redirect('lista_imagenes')
    return redirect('lista_imagenes')


@login_required
def editar_marca(request, id_imagen):
    from PIL import Image as PILImage
    import io
    from django.core.files.base import ContentFile
    
    imagen = get_object_or_404(Imagen, pk=id_imagen)
    if request.method == 'POST':
        try:
            if 'img_portada' in request.FILES:
                imagen.img_portada = request.FILES['img_portada']
            if 'marca_agua' in request.FILES:
                marca_agua_file = request.FILES['marca_agua']
                marca_agua = PILImage.open(marca_agua_file)
                img_portada = PILImage.open(imagen.img_portada)
                transparencia = 0.5
                marca_agua.putalpha(int(255 * transparencia))
                img_portada.paste(marca_agua, (0, 0), marca_agua)
                img_io = io.BytesIO()
                img_portada.save(img_io, format='PNG')
                img_file = ContentFile(img_io.getvalue(), 'imagen_con_marca_agua.png')
                imagen.img_portada = img_file
            imagen.save()
            messages.success(request, "Marca de agua aplicada")
        except Exception as e:
            logger.error(f"Error aplicando marca de agua: {str(e)}")
            messages.error(request, f'Error: {str(e)}')
        return redirect('lista_imagenes')
    return render(request, 'editar_marca.html', {'imagen': imagen})