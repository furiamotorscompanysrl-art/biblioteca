# views/admin_views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from django.db.models import Count, Q
from django.http import JsonResponse, HttpResponse
from django.urls import reverse
from django.utils import timezone
from datetime import datetime, timedelta
from django.core.paginator import Paginator
from django.contrib.auth.models import User
import logging
import re

from ..decorators import admin_required
from ..models import (
    Usuario, Sugerencia, Categoria, Autor, VisitaLibro, Libro, Revista, Imagen
)
from ..forms import VisitaFilterForm, UsuarioForm, AutorForm

logger = logging.getLogger(__name__)


def generar_username_unico(correo, ci):
    """Genera un username único para el usuario de Django"""
    correo_limpio = correo.split('@')[0]
    correo_limpio = re.sub(r'[^a-zA-Z0-9_]', '', correo_limpio)
    base = f"{ci}_{correo_limpio}"
    base = re.sub(r'[^a-zA-Z0-9_]', '', base)
    if len(base) > 140:
        base = base[:140]
    return base


# ==================== Gestión de Usuarios ====================
@login_required
@admin_required
def lista_usuarios(request):
    usuarios = Usuario.objects.all().order_by('-usuario_id')
    paginator = Paginator(usuarios, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return render(request, 'lista_usuarios.html', {'page_obj': page_obj})


@login_required
@admin_required
def agregar_usuario(request):
    if request.method == 'GET':
        fecha_baja_default = timezone.now() + timedelta(days=5*365)
        return render(request, 'agregar_usuario.html', {'fecha_baja_default': fecha_baja_default})

    if request.method == 'POST':
        try:
            nombres = request.POST.get('nombres', '').strip()
            apepat = request.POST.get('apepat', '').strip()
            apemat = request.POST.get('apemat', '').strip()
            ci = request.POST.get('ci', '').strip()
            correo = request.POST.get('correo', '').strip().lower()
            extension = request.POST.get('extension', 'LP')
            complemento = request.POST.get('complemento', '').strip()
            tipo_usuario = request.POST.get('tipo_usuario', 'Externo')
            ru = request.POST.get('ru', '').strip()
            nro_celular = request.POST.get('nro_celular', '').strip()
            fecha_baja = request.POST.get('fecha_baja', '')

            if not nombres:
                return render(request, 'agregar_usuario.html', {'mensaje': 'El nombre es obligatorio.'})
            if not ci or len(ci) < 5:
                return render(request, 'agregar_usuario.html', {'mensaje': 'El CI debe tener al menos 5 dígitos.'})
            if not nro_celular or len(nro_celular) != 8:
                return render(request, 'agregar_usuario.html', {'mensaje': 'El número de celular debe tener 8 dígitos.'})
            if tipo_usuario == 'Estudiante' and (not ru or len(ru) < 5):
                return render(request, 'agregar_usuario.html', {'mensaje': 'Para estudiantes, el RU es obligatorio y debe tener al menos 5 dígitos.'})
            if '@' not in correo:
                return render(request, 'agregar_usuario.html', {'mensaje': 'Ingrese un correo electrónico válido.'})
            if Usuario.objects.filter(ci=ci).exists():
                return render(request, 'agregar_usuario.html', {'mensaje': f'El CI {ci} ya está registrado.'})
            if ru and Usuario.objects.filter(ru=ru).exists():
                return render(request, 'agregar_usuario.html', {'mensaje': 'El RU ya está registrado.'})

            logger.info(f"Creando usuario: {nombres}, CI: {ci}, Correo: {correo}, Tipo: {tipo_usuario}")

            with transaction.atomic():
                username_unico = generar_username_unico(correo, ci)
                
                django_user, user_created = User.objects.get_or_create(
                    email=correo,
                    defaults={
                        'username': username_unico,
                        'password': ci,
                    }
                )
                
                if not user_created:
                    if django_user.username != username_unico:
                        django_user.username = username_unico
                        django_user.save()
                    logger.info(f"Usuario Django ya existía: {correo}")
                
                usuario, perfil_created = Usuario.objects.get_or_create(
                    user=django_user,
                    defaults={
                        'nombres': nombres,
                        'apepat': apepat,
                        'apemat': apemat,
                        'ci': ci,
                        'correo': correo,
                        'extension': extension,
                        'complemento': complemento,
                        'tipo_usuario': tipo_usuario,
                        'ru': ru if tipo_usuario == 'Estudiante' else '',
                        'nro_celular': nro_celular,
                        'fecha_baja': fecha_baja if fecha_baja else timezone.now() + timedelta(days=5*365),
                        'esta_activo': True
                    }
                )
                
                if not perfil_created:
                    usuario.nombres = nombres
                    usuario.apepat = apepat
                    usuario.apemat = apemat
                    usuario.ci = ci
                    usuario.correo = correo
                    usuario.extension = extension
                    usuario.complemento = complemento
                    usuario.tipo_usuario = tipo_usuario
                    usuario.ru = ru if tipo_usuario == 'Estudiante' else ''
                    usuario.nro_celular = nro_celular
                    usuario.fecha_baja = fecha_baja if fecha_baja else timezone.now() + timedelta(days=5*365)
                    usuario.save()
                    logger.info(f"Perfil Usuario actualizado para: {correo}")
                else:
                    logger.info(f"Perfil Usuario creado exitosamente para: {correo}")
            
            return render(request, 'aviso.html', {
                'cabeza': 'Agregación de Usuario',
                'cuerpo': f"Se ha agregado el usuario: {nombres} ({tipo_usuario}). El acceso es con su correo institucional y código de verificación."
            })
                
        except Exception as e:
            logger.error(f"Error general en agregar_usuario: {str(e)}", exc_info=True)
            return render(request, 'agregar_usuario.html', {'mensaje': f'Error: {str(e)}'})

    return render(request, 'agregar_usuario.html')


@login_required
@admin_required
def modificar_usuario(request, usuario_id):
    usuario = get_object_or_404(Usuario, usuario_id=usuario_id)
    if request.method == 'POST':
        try:
            form = UsuarioForm(request.POST, instance=usuario)
            if form.is_valid():
                with transaction.atomic():
                    usuario = form.save(commit=False)
                    nuevo_correo = form.cleaned_data['correo']
                    if usuario.user:
                        usuario.user.email = nuevo_correo
                        usuario.user.save()
                    usuario.correo = nuevo_correo
                    usuario.save()
                return JsonResponse({
                    'status': 'success',
                    'message': f'Usuario {usuario.nombres} actualizado',
                    'redirect_url': reverse('lista_usuarios')
                })
            else:
                errores = [f"{field}: {', '.join(errors)}" for field, errors in form.errors.items()]
                return JsonResponse({'status': 'error', 'message': '; '.join(errores)})
        except Exception as e:
            logger.error(f"Error modificando usuario: {str(e)}")
            return JsonResponse({'status': 'error', 'message': str(e)})

    context = {
        'form': UsuarioForm(instance=usuario),
        'usuario': usuario,
        'opciones_usuarios': Usuario.opciones_usuarios,
        'opciones_extensiones': Usuario.opciones_extensiones,
        'titulo': f'Modificar Usuario: {usuario.nombres}'
    }
    return render(request, 'modificar_usuario.html', context)


@login_required
def eliminar_usuario(request, usuario_id):
    if request.method == 'POST':
        usuario = get_object_or_404(Usuario, usuario_id=usuario_id)
        nombre = usuario.nombres
        usuario.delete()
        return redirect('lista_usuarios')
    return redirect('lista_usuarios')


# ==================== Panel Principal / Dashboard ====================
@login_required
@admin_required
def principal(request):
    try:
        form = VisitaFilterForm()
        visitas_agrupadas_nivel = {}
        visitas_agrupadas_unitarias = {}
        vista_opcion = None

        if request.method == 'POST':
            form = VisitaFilterForm(request.POST)
            if form.is_valid():
                mes = form.cleaned_data['mes']
                año = form.cleaned_data['año']
                vista_opcion = form.cleaned_data['vista_opcion']
                visitas = VisitaLibro.objects.filter(fecha_consulta__year=año, fecha_consulta__month=mes)
                if visitas.exists():
                    visitas_unitarias = visitas.values('libro_visitado__titulo').annotate(total=Count('id')).order_by('-total')
                    for v in visitas_unitarias:
                        visitas_agrupadas_unitarias[v['libro_visitado__titulo']] = v['total']
                    visitas_nivel = visitas.values('libro_visitado__categoria').annotate(total=Count('id')).order_by('-total')
                    for v in visitas_nivel:
                        visitas_agrupadas_nivel[v['libro_visitado__categoria']] = v['total']
                else:
                    messages.info(request, f'No se encontraron visitas para {mes}/{año}.')
            else:
                messages.error(request, 'El formulario contiene errores.')

        total_usuarios = Usuario.objects.count()
        total_sugerencias = Sugerencia.objects.count()
        from ..models import Libro, Revista, Imagen
        total_libros = Libro.objects.count()
        total_revistas = Revista.objects.count()
        total_imagenes = Imagen.objects.count()

        datos = {
            'total_usuarios': total_usuarios,
            'total_sugerencias': total_sugerencias,
            'total_libros': total_libros,
            'total_revistas': total_revistas,
            'total_imagenes': total_imagenes,
            'form': form,
            'visitas_agrupadas_nivel': visitas_agrupadas_nivel,
            'visitas_agrupadas_unitarias': visitas_agrupadas_unitarias,
            'vista_opcion': vista_opcion,
            'usuario': request.user.usuario if hasattr(request.user, 'usuario') else None
        }

        estadisticas = {
            'usuarios_activos': Usuario.objects.filter(esta_activo=True).count(),
            'usuarios_nuevos_mes': Usuario.objects.filter(
                fecha_alta__month=datetime.now().month,
                fecha_alta__year=datetime.now().year
            ).count(),
            'libros_por_categoria': Categoria.objects.annotate(num_libros=Count('libro')).values('nom_cat', 'num_libros'),
            'imagenes_por_categoria': Categoria.objects.annotate(num_imagenes=Count('imagen')).values('nom_cat', 'num_imagenes'),
            'total_visitas_mes': VisitaLibro.objects.filter(
                fecha_visualizacion__month=datetime.now().month,
                fecha_visualizacion__year=datetime.now().year
            ).count(),
        }

        datos.update({'estadisticas': estadisticas})
        return render(request, 'principal.html', datos)
        
    except Exception as e:
        logger.error(f"Error en principal: {str(e)}", exc_info=True)
        messages.error(request, 'Error al cargar el dashboard')
        return render(request, 'principal.html', {'form': VisitaFilterForm()})


# ==================== Categorías ====================
@login_required
@admin_required
def agregar_categoria(request):
    if request.method == 'POST':
        try:
            nombre = request.POST.get('nombre_categoria')
            if not nombre:
                raise ValueError('El nombre es requerido')
            categoria, created = Categoria.objects.get_or_create(nom_cat=nombre)
            return JsonResponse({'success': True, 'id_categoria': categoria.id_categoria, 'nombre': categoria.nom_cat})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=400)


@login_required
def editar_categoria(request, id_categoria):
    try:
        categoria = get_object_or_404(Categoria, id_categoria=id_categoria)
        if request.method == 'POST':
            nombre = request.POST.get('nombre_categoria')
            if not nombre:
                raise ValueError('El nombre es requerido')
            categoria.nom_cat = nombre
            categoria.save()
            return JsonResponse({'success': True, 'id_categoria': categoria.id_categoria, 'nombre': categoria.nom_cat})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


@login_required
def eliminar_categoria(request, id_categoria):
    try:
        categoria = get_object_or_404(Categoria, id_categoria=id_categoria)
        nombre = categoria.nom_cat
        categoria.delete()
        return JsonResponse({'success': True, 'message': f'Categoría "{nombre}" eliminada'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


# ==================== Autores ====================
@login_required
def agregar_autor(request):
    if request.method == 'POST':
        form = AutorForm(request.POST)
        if form.is_valid():
            nombre = form.cleaned_data['nombre']
            autor, created = Autor.objects.get_or_create(nombre=nombre)
            return JsonResponse({'id_autor': autor.id_autor, 'nombre': str(autor), 'success': True})
        return JsonResponse({'error': 'Formulario inválido.', 'errors': form.errors}, status=400)
    form = AutorForm()
    return render(request, 'agregar_autor.html', {'form': form})


@login_required
def editar_autor(request, id_autor):
    autor = get_object_or_404(Autor, id_autor=id_autor)
    if request.method == 'POST':
        form = AutorForm(request.POST, instance=autor)
        if form.is_valid():
            autor = form.save()
            return JsonResponse({'success': True, 'id_autor': autor.id_autor, 'nombre': autor.nombre})
        return JsonResponse({'success': False, 'errors': form.errors}, status=400)


@login_required
def eliminar_autor(request, id_autor):
    autor = get_object_or_404(Autor, id_autor=id_autor)
    if request.method == 'POST':
        autor.delete()
        return JsonResponse({'success': True})
    return JsonResponse({'success': False, 'error': 'Método no permitido'}, status=405)


# ==================== Sugerencias (Admin) ====================
@login_required
@admin_required
def listar_sugerencias(request):
    sugerencias = Sugerencia.objects.all().order_by('-fecha_sugerencia')
    paginator = Paginator(sugerencias, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return render(request, 'listar_sugerencias.html', {'sugerencias': page_obj})


@login_required
@admin_required
def aprobar_sugerencia(request, sugerencia_id):
    if request.method == 'POST':
        sugerencia = get_object_or_404(Sugerencia, pk=sugerencia_id)
        sugerencia.estado_respuesta = 'Aprobado'
        sugerencia.save()
        return redirect('listar_sugerencias')
    return redirect('listar_sugerencias')


# ==================== Monitoreo de Usuarios Activos ====================
@login_required
@admin_required
def usuarios_activos(request):
    from datetime import date, timedelta
    from django.db.models import Count
    
    usuarios = Usuario.objects.filter(esta_activo=True).prefetch_related('visitalibro_set')
    
    stats = {
        'total_usuarios': Usuario.objects.count(),
        'usuarios_activos': Usuario.objects.filter(esta_activo=True).count(),
        'total_visitas_hoy': VisitaLibro.objects.filter(fecha_consulta=date.today()).count(),
        'total_visitas_semana': VisitaLibro.objects.filter(
            fecha_consulta__gte=date.today() - timedelta(days=7)
        ).count(),
        'libros_mas_leidos': Libro.objects.annotate(
            visitas_count=Count('visitalibro')
        ).order_by('-visitas_count')[:10],
        'usuarios_mas_activos': Usuario.objects.annotate(
            visitas_count=Count('visitalibro')
        ).order_by('-visitas_count')[:10]
    }
    
    ultimas_visitas = VisitaLibro.objects.select_related(
        'visitante', 'libro_visitado'
    ).order_by('-fecha_visualizacion')[:50]
    
    context = {
        'usuarios': usuarios,
        'stats': stats,
        'ultimas_visitas': ultimas_visitas,
    }
    
    return render(request, 'usuarios_activos.html', context)


@login_required
@admin_required
def ver_historial_usuario(request, usuario_id):
    from django.core.paginator import Paginator
    
    usuario = get_object_or_404(Usuario, usuario_id=usuario_id)
    
    visitas = VisitaLibro.objects.filter(
        visitante=usuario
    ).select_related('libro_visitado').order_by('-fecha_visualizacion')
    
    stats = {
        'total_visitas': visitas.count(),
        'libros_distintos': visitas.values('libro_visitado').distinct().count(),
        'ultima_visita': visitas.first().fecha_visualizacion if visitas.exists() else None,
        'ultimo_libro': visitas.first().libro_visitado.titulo if visitas.exists() else 'Ninguno',
    }
    
    paginator = Paginator(visitas, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'usuario': usuario,
        'visitas': page_obj,
        'stats': stats,
    }
    
    return render(request, 'historial_usuario.html', context)