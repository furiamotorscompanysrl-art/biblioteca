# admin.py - VERSIÓN CORREGIDA
from django.contrib import admin
from django.utils.html import format_html
from import_export.admin import ImportExportModelAdmin
from .models import Usuario, Autor, Libro, Sugerencia, Coleccion, Revista, VisitaLibro, Imagen, Categoria
from import_export import resources
from import_export.fields import Field
from django.urls import reverse
from django.utils.safestring import mark_safe
from django.contrib import messages
from django.db import transaction
import logging

logger = logging.getLogger(__name__)

# NO importar reversion si no lo estás usando
# from reversion.admin import VersionAdmin
# reversion.register(Libro)  # Comentar esto temporalmente

class LibroResource(resources.ModelResource):
    autores_list = Field()
    categorias_list = Field()

    class Meta:
        model = Libro
        fields = ('id_libro', 'tipo', 'titulo', 'edicion', 'categoria', 
                 'img_portada', 'archivo_autorizacion', 'autores_list',
                 'fecha_publicacion', 'descripcion', 'palabra_clave', 
                 'descarga_autorizada', 'pdf_url', 'categorias_list')
        export_order = fields

    def dehydrate_autores_list(self, libro):
        return ', '.join([autor.nombre for autor in libro.autores.all()])

    def dehydrate_categorias_list(self, libro):
        return ', '.join([cat.nom_cat for cat in libro.categorias.all()])


@admin.register(Usuario)
class UsuarioAdmin(ImportExportModelAdmin):  # Quitar VersionAdmin
    list_display = ('usuario_id', 'nombres', 'ru', 'tipo_usuario', 'correo', 'esta_activo', 'get_status_icon')
    search_fields = ('nombres', 'correo', 'ci')
    list_filter = ('tipo_usuario', 'esta_activo', 'extension')
    readonly_fields = ('fecha_alta',)
    list_per_page = 25
    
    def get_status_icon(self, obj):
        if obj.esta_activo:
            return format_html('<span style="color: green;">●</span>')
        return format_html('<span style="color: red;">●</span>')
    get_status_icon.short_description = 'Estado'
    
    def save_model(self, request, obj, form, change):
        """Guarda el usuario correctamente sin interferencias"""
        try:
            with transaction.atomic():
                super().save_model(request, obj, form, change)
                logger.info(f"Usuario {obj.nombres} guardado exitosamente desde admin")
        except Exception as e:
            logger.error(f"Error guardando usuario {obj.nombres}: {str(e)}")
            messages.error(request, f"Error al guardar: {str(e)}")
            raise


@admin.register(Libro)
class LibroAdmin(ImportExportModelAdmin):  # Quitar VersionAdmin
    resource_class = LibroResource
    list_display = ('id_libro', 'titulo', 'tipo', 'categoria', 'descarga_autorizada', 'get_autores')
    search_fields = ('titulo', 'palabra_clave', 'autores__nombre')
    list_filter = ('tipo', 'categoria', 'descarga_autorizada', 'fecha_publicacion')
    filter_horizontal = ('autores', 'categorias')
    date_hierarchy = 'fecha_publicacion'
    list_per_page = 20
    
    def get_autores(self, obj):
        return ", ".join([autor.nombre for autor in obj.autores.all()])
    get_autores.short_description = 'Autores'

    actions = ['marcar_como_autorizado', 'marcar_como_no_autorizado']
    
    def marcar_como_autorizado(self, request, queryset):
        updated = queryset.update(descarga_autorizada=True)
        self.message_user(request, f'{updated} libros marcados como autorizados.')
    marcar_como_autorizado.short_description = "Marcar libros seleccionados como autorizados"

    def marcar_como_no_autorizado(self, request, queryset):
        updated = queryset.update(descarga_autorizada=False)
        self.message_user(request, f'{updated} libros marcados como no autorizados.')
    marcar_como_no_autorizado.short_description = "Marcar libros seleccionados como no autorizados"

    readonly_fields = ('preview_portada', 'preview_pdf')

    def preview_portada(self, obj):
        if obj.img_portada:
            return mark_safe(f'<img src="{obj.img_portada.url}" width="150"/>')
        return "Sin portada"
    preview_portada.short_description = 'Vista previa de portada'

    def preview_pdf(self, obj):
        if obj.pdf_url:
            return mark_safe(f'<a href="{obj.pdf_url}" target="_blank">Ver PDF</a>')
        if obj.pdf:
            return mark_safe(f'<a href="{obj.pdf.url}" target="_blank">Ver PDF</a>')
        return "Sin PDF"
    preview_pdf.short_description = 'Vista previa de PDF'

    def save_model(self, request, obj, form, change):
        try:
            with transaction.atomic():
                super().save_model(request, obj, form, change)
                if change:
                    messages.info(request, f'El libro "{obj.titulo}" ha sido actualizado exitosamente.')
                else:
                    messages.success(request, f'El libro "{obj.titulo}" ha sido creado exitosamente.')
        except Exception as e:
            logger.error(f"Error guardando libro {obj.titulo}: {str(e)}")
            messages.error(request, f"Error al guardar: {str(e)}")


@admin.register(Autor)
class AutorAdmin(ImportExportModelAdmin):
    list_display = ('id_autor', 'nombre')
    search_fields = ('nombre',)


@admin.register(Sugerencia)
class SugerenciaAdmin(ImportExportModelAdmin):
    list_display = ('id_sugerencia', 'titulo_sugerencia', 'autor_sugerencia', 'estado_respuesta')
    list_filter = ('estado_respuesta',)


@admin.register(Revista)
class RevistaAdmin(ImportExportModelAdmin):
    list_display = ('id_revista', 'nro_revista', 'coleccion')
    search_fields = ('nro_revista',)
    list_filter = ('coleccion',)


@admin.register(Coleccion)
class ColeccionAdmin(ImportExportModelAdmin):
    list_display = ('id_coleccion', 'nomb_colecc', 'orden')
    search_fields = ('nomb_colecc',)
    list_editable = ('orden',)


@admin.register(VisitaLibro)
class VisitaLibroAdmin(ImportExportModelAdmin):
    list_display = ('visitante', 'libro_visitado', 'fecha_visualizacion')
    list_filter = ('fecha_visualizacion', 'libro_visitado')
    date_hierarchy = 'fecha_visualizacion'
    readonly_fields = ('fecha_visualizacion',)
    search_fields = ('visitante__nombres', 'libro_visitado__titulo')
    list_per_page = 50


@admin.register(Imagen)
class ImagenAdmin(ImportExportModelAdmin):
    list_display = ('id_Imagen', 'titulo', 'autorImg', 'fecha_subida')
    search_fields = ('titulo', 'autorImg')


@admin.register(Categoria)
class CategoriaAdmin(ImportExportModelAdmin):
    list_display = ('id_categoria', 'nom_cat')
    search_fields = ('nom_cat',)