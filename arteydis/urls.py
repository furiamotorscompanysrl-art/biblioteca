# arteydis/urls.py
from django.contrib import admin
from django.urls import path, include
from django.conf.urls.static import static
from django.conf import settings
from biblioartdis import views
from biblioartdis.views.auth_views import CustomLoginView

# Importar las vistas específicas de usuario_views
from biblioartdis.views.usuario_views import (
    perfil, cambiar_password_ajax, historial_visitas, registrar_visita_libro,
    inicio, novedades_libros, libros_nivel, catalogo,
    sugerir_libro, listar_sugerencias_usuario, descartar_sugerencia,
    ver_pdf, galeria_artistica, ver_imagen,
    buscar_libros, chatbot_view, obtener_novedades, chat_con_gemini
)

# Importar las vistas proxy
from biblioartdis.views.libro_views import proxy_imagen, proxy_pdf

urlpatterns = [
    # Admin
    path('admin/', admin.site.urls),
    
    # ============================================
    # PROXY PARA GOOGLE DRIVE (IMÁGENES Y PDFs)
    # ============================================
    path('proxy/imagen/', proxy_imagen, name='proxy_imagen'),
    path('proxy/pdf/', proxy_pdf, name='proxy_pdf'),
    
    # Autenticación (usando views desde auth_views)
    path('', views.home, name='home'),
    path('accounts/login/', views.home, name='login'),
    path('accounts/logout/', views.logout_view, name='logout'),
    
    # Páginas principales
    path('inicio/', inicio, name='inicio'),
    path('principal/', views.principal, name='principal'),
    
    # ============================================
    # REGISTRO CON APROBACIÓN MANUAL
    # ============================================
    path('registrar/', views.registrar_usuario, name='registrar_usuario'),
    path('solicitudes-pendientes/', views.listar_solicitudes_pendientes, name='solicitudes_pendientes'),
    path('aprobar-usuario/<int:usuario_id>/', views.aprobar_usuario, name='aprobar_usuario'),
    path('rechazar-usuario/<int:usuario_id>/', views.rechazar_usuario, name='rechazar_usuario'),
    
    # ============================================
    # GESTIÓN DE SOLICITUDES
    # ============================================
    path('solicitudes/', views.gestionar_solicitudes, name='gestionar_solicitudes'),
    path('aprobar-solicitud/<int:usuario_id>/', views.aprobar_solicitud, name='aprobar_solicitud'),
    path('rechazar-solicitud/<int:usuario_id>/', views.rechazar_solicitud, name='rechazar_solicitud'),
    path('ver-documentos/<int:usuario_id>/', views.ver_documentos_solicitud, name='ver_documentos_solicitud'),
    
    # ============================================
    # SUBIDA A DRIVE VÍA AJAX
    # ============================================
    path('upload-to-drive/', views.upload_to_drive_ajax, name='upload_to_drive_ajax'),
    
    # ============================================
    # RESTABLECER CONTRASEÑA (ADMIN)
    # ============================================
    path('restablecer-password-admin/', views.restablecer_password_admin, name='restablecer_password_admin'),
    path('restablecer-password-api/', views.restablecer_password_api, name='restablecer_password_api'),
    
    # ============================================
    # PERFIL Y USUARIOS
    # ============================================
    path('perfil/', perfil, name='perfil'),
    path('cambiar-password-ajax/', cambiar_password_ajax, name='cambiar_password_ajax'),
    
    path('agregar_usuario/', views.agregar_usuario, name='agregar_usuario'),
    path('modificar_usuario/<int:usuario_id>/', views.modificar_usuario, name='modificar_usuario'),
    path('eliminar_usuario/<int:usuario_id>/', views.eliminar_usuario, name='eliminar_usuario'),
    path('lista_usuarios/', views.lista_usuarios, name='lista_usuarios'),
    
    path('restablecer-password/', views.restablecer_password, name='restablecer_password'),
    
    # ============================================
    # GESTIÓN DE LIBROS
    # ============================================
    path('listar_libros/', views.listar_libros, name='listar_libros'),
    path('ver_pdf/<int:libro_id>/', ver_pdf, name='ver_pdf'),
    path('libro/ver_descargar/<int:libro_id>/', views.ver_descargar_libro, name='ver_descargar_libro'),
    path('libro/<int:libro_id>/editar/', views.editar_libro, name='editar_libro'),
    path('libros/<int:libro_id>/eliminar/', views.eliminar_libro, name='eliminar_libro'),
    path('libros/agregar/', views.agregar_libro, name='agregar_libro'),
    path('libros/nivel/<int:id_nivel>/', libros_nivel, name='libros_nivel'),
    path('novedades_libros/', novedades_libros, name='novedades_libros'),
    path('registrar_visita/', registrar_visita_libro, name='registrar_visita_libro'),
    path('historial_visitas/', historial_visitas, name='historial_visitas'),
    path('eliminar_autorizacion/<int:libro_id>/', views.eliminar_autorizacion, name='eliminar_autorizacion'),
    
    # ============================================
    # GESTIÓN DE SUGERENCIAS
    # ============================================
    path('sugerencias/', views.listar_sugerencias, name='listar_sugerencias'),
    path('sugerencias/descartar/<int:sugerencia_id>/', descartar_sugerencia, name='descartar_sugerencia'),
    path('sugerencias/aprobar/<int:sugerencia_id>/', views.aprobar_sugerencia, name='aprobar_sugerencia'), 
    path('sugerir_libro/', sugerir_libro, name='sugerir_libro'),
    path('listar_sugerencias_usuario/', listar_sugerencias_usuario, name='listar_sugerencias_usuario'),
    
    # ============================================
    # GESTIÓN DE CATEGORÍAS
    # ============================================
    path('agregar_categoria/', views.agregar_categoria, name='agregar_categoria'),
    path('editar_categoria/<int:id_categoria>/', views.editar_categoria, name='editar_categoria'),
    path('eliminar_categoria/<int:id_categoria>/', views.eliminar_categoria, name='eliminar_categoria'),
    
    # ============================================
    # GESTIÓN DE AUTORES
    # ============================================
    path('agregar-autor/', views.agregar_autor, name='agregar_autor'),
    path('editar_autor/<int:id_autor>/', views.editar_autor, name='editar_autor'),
    path('eliminar_autor/<int:id_autor>/', views.eliminar_autor, name='eliminar_autor'),

    # ============================================
    # GESTIÓN DE REVISTAS Y COLECCIONES
    # ============================================
    path('agregar_revista/', views.agregar_revista, name='agregar_revista'),
    path('listar_revistas/', views.listar_revistas, name='listar_revistas'),
    path('eliminar_revista/<int:id_revista>/', views.eliminar_revista, name='eliminar_revista'),
    path('modificar_revista/<int:id_revista>/', views.modificar_revista, name='modificar_revista'),
    
    path('agregar_coleccion/', views.agregar_coleccion, name='agregar_coleccion'),
    path('eliminar_coleccion/<int:id_coleccion>/', views.eliminar_coleccion, name='eliminar_coleccion'),
    path('modificar_coleccion/<int:id_coleccion>/', views.modificar_coleccion, name='modificar_coleccion'),

    # ============================================
    # GESTIÓN DE LA GALERÍA DE IMÁGENES
    # ============================================
    path('galeria_artistica/', galeria_artistica, name='galeria_artistica'),
    path('lista_imagenes/', views.listar_imagenes, name='lista_imagenes'),
    path('agregar/', views.agregar_imagen, name='agregar_imagen'),
    path('editar_imagen/<int:id_imagen>/', views.editar_imagen, name='editar_imagen'),
    path('editar_marca/<int:id_imagen>/', views.editar_marca, name='editar_marca'),
    path('eliminar/<int:pk>/', views.eliminar_imagen, name='eliminar_imagen'),
    path('ver_imagen/<int:id>/', ver_imagen, name='ver_imagen'),
    
    # ============================================
    # CATÁLOGO Y OTRAS FUNCIONALIDADES
    # ============================================
    path('catalogo/', catalogo, name='catalogo'),
    path('buscar_libros/', buscar_libros, name='buscar_libros'),
    path('chatbot/', chatbot_view, name='chatbot_view'),

    # ============================================
    # CAMBIAR ESTADO DE DESCARGA
    # ============================================
    path('libro/<int:libro_id>/cambiar_estado_descarga/', views.cambiar_estado_descarga, name='cambiar_estado_descarga'),
    path('actualizar-orden/', views.actualizar_orden_colecciones, name='actualizar_orden_colecciones'),
    path('obtener_novedades/', obtener_novedades, name='obtener_novedades'),

    # ============================================
    # MONITOREO DE USUARIOS ACTIVOS
    # ============================================
    path('usuarios-activos/', views.usuarios_activos, name='usuarios_activos'),
    path('ver-historial/<int:usuario_id>/', views.ver_historial_usuario, name='ver_historial_usuario'),
    
    # ============================================
    # CHAT CON IA
    # ============================================
    path('chat-gemini/', chat_con_gemini, name='chat_gemini'),
]

# Archivos de medios
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)