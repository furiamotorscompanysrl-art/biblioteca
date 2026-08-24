from django.contrib import admin
from django.urls import path, include
from django.conf.urls.static import static
from django.conf import settings
from biblioartdis import views
from biblioartdis.views import CustomLoginView

urlpatterns = [
    # Página principal y autenticación
    path('admin/', admin.site.urls),
    path('', views.home, name='home'),
    path('accounts/login/', views.home, name='login'),
    path('inicio/', views.inicio, name='inicio'),
    path('principal/', views.principal, name='principal'),
    path('accounts/logout/', views.logout_view, name='logout'),
    
    # Verificación de dos factores (2FA)
    path('verificar-codigo/', views.verificar_codigo_view, name='verificar_codigo'),
    path('reenviar-codigo/', views.reenviar_codigo, name='reenviar_codigo'),
    
    # Perfil y usuarios
    path('perfil/', views.perfil, name='perfil'),
    path('agregar_usuario/', views.agregar_usuario, name='agregar_usuario'),
    path('modificar_usuario/<int:usuario_id>/', views.modificar_usuario, name='modificar_usuario'),
    path('eliminar_usuario/<int:usuario_id>/', views.eliminar_usuario, name='eliminar_usuario'),
    path('lista_usuarios/', views.lista_usuarios, name='lista_usuarios'),
    path('restablecer_password/', views.restablecer_password, name='restablecer_password'),
    path('cambiar-password/', views.cambiar_password, name='cambiar_password'),

    # Gestión de libros
    path('listar_libros/', views.listar_libros, name='listar_libros'),
    path('ver_pdf/<int:libro_id>/', views.ver_pdf, name='ver_pdf'),
    path('libro/ver_descargar/<int:libro_id>/', views.ver_descargar_libro, name='ver_descargar_libro'),  # ⭐ NUEVA LÍNEA
    path('libro/<int:libro_id>/editar/', views.editar_libro, name='editar_libro'),
    path('libros/<int:libro_id>/eliminar/', views.eliminar_libro, name='eliminar_libro'),
    path('libros/agregar/', views.agregar_libro, name='agregar_libro'),
    path('libros/nivel/<int:id_nivel>/', views.libros_nivel, name='libros_nivel'),
    path('novedades_libros/', views.novedades_libros, name='novedades_libros'),
    path('registrar_visita/', views.registrar_visita_libro, name='registrar_visita_libro'),
    path('historial_visitas/', views.historial_visitas, name='historial_visitas'),
    path('eliminar_autorizacion/<int:libro_id>/', views.eliminar_autorizacion, name='eliminar_autorizacion'),

    # Gestión de sugerencias
    path('sugerencias/', views.listar_sugerencias, name='listar_sugerencias'),
    path('sugerencias/descartar/<int:sugerencia_id>/', views.descartar_sugerencia, name='descartar_sugerencia'),
    path('sugerencias/aprobar/<int:sugerencia_id>/', views.aprobar_sugerencia, name='aprobar_sugerencia'), 
    path('sugerir_libro/', views.sugerir_libro, name='sugerir_libro'),
    path('listar_sugerencias_usuario/', views.listar_sugerencias_usuario, name='listar_sugerencias_usuario'),
    
    # Gestión de categorías
    path('agregar_categoria/', views.agregar_categoria, name='agregar_categoria'),
    path('editar_categoria/<int:id_categoria>/', views.editar_categoria, name='editar_categoria'),
    path('eliminar_categoria/<int:id_categoria>/', views.eliminar_categoria, name='eliminar_categoria'),
    
    # Gestión de autores
    path('agregar-autor/', views.agregar_autor, name='agregar_autor'),
    path('editar_autor/<int:id_autor>/', views.editar_autor, name='editar_autor'),
    path('eliminar_autor/<int:id_autor>/', views.eliminar_autor, name='eliminar_autor'),

    # Gestión de revistas y colecciones
    path('agregar_revista/', views.agregar_revista, name='agregar_revista'),
    path('listar_revistas/', views.listar_revistas, name='listar_revistas'),
    path('eliminar_revista/<int:id_revista>/', views.eliminar_revista, name='eliminar_revista'),
    path('modificar_revista/<int:id_revista>/', views.modificar_revista, name='modificar_revista'),
    
    path('agregar_coleccion/', views.agregar_coleccion, name='agregar_coleccion'),
    path('eliminar_coleccion/<int:id_coleccion>/', views.eliminar_coleccion, name='eliminar_coleccion'),
    path('modificar_coleccion/<int:id_coleccion>/', views.modificar_coleccion, name='modificar_coleccion'),

    # Gestión de la galería de imágenes
    path('galeria_artistica/', views.galeria_artistica, name='galeria_artistica'),
    path('lista_imagenes/', views.listar_imagenes, name='lista_imagenes'),
    path('agregar/', views.agregar_imagen, name='agregar_imagen'),
    path('editar_imagen/<int:id_imagen>/', views.editar_imagen, name='editar_imagen'),
    path('editar_marca/<int:id_imagen>/', views.editar_marca, name='editar_marca'),
    path('eliminar/<int:pk>/', views.eliminar_imagen, name='eliminar_imagen'),
    path('ver_imagen/<int:id>/', views.ver_imagen, name='ver_imagen'),
    
    # Catálogo y otras funcionalidades
    path('catalogo/', views.catalogo, name='catalogo'),
    path('buscar_libros/', views.buscar_libros, name='buscar_libros'),
    path('chatbot/', views.chatbot_view, name='chatbot_view'),

    # Cambiar estado de descarga
    path('libro/<int:libro_id>/cambiar_estado_descarga/', views.cambiar_estado_descarga, name='cambiar_estado_descarga'),
    path('actualizar-orden/', views.actualizar_orden_colecciones, name='actualizar_orden_colecciones'),
    path('obtener_novedades/', views.obtener_novedades, name='obtener_novedades'),

    # Monitoreo de usuarios activos
    path('usuarios-activos/', views.usuarios_activos, name='usuarios_activos'),
    path('ver-historial/<int:usuario_id>/', views.ver_historial_usuario, name='ver_historial_usuario'),
    
    # Chat con IA
    path('chat-gemini/', views.chat_con_gemini, name='chat_gemini'),
]

# Archivos de medios
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)