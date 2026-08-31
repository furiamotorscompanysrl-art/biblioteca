# views/__init__.py
# Reexporta todas las vistas desde los submódulos para mantener compatibilidad con urls.py

from .auth_views import (
    home, 
    CustomLoginView, 
    logout_view, 
    cambiar_password,
    registrar_usuario,
    listar_solicitudes_pendientes,
    aprobar_usuario,
    rechazar_usuario,
    restablecer_password_admin,
    restablecer_password_api,
    upload_to_drive_ajax,  # ← NUEVA IMPORTACIÓN
)

from .admin_views import (
    lista_usuarios, 
    agregar_usuario, 
    modificar_usuario, 
    eliminar_usuario,
    principal, 
    agregar_categoria, 
    editar_categoria, 
    eliminar_categoria,
    agregar_autor, 
    editar_autor, 
    eliminar_autor, 
    listar_sugerencias,
    aprobar_sugerencia, 
    usuarios_activos, 
    ver_historial_usuario,
    # ============================================
    # NUEVAS VISTAS PARA GESTIÓN DE SOLICITUDES
    # ============================================
    gestionar_solicitudes,
    aprobar_solicitud,
    rechazar_solicitud,
    ver_documentos_solicitud,
)

from .usuario_views import (
    inicio, 
    perfil, 
    historial_visitas, 
    registrar_visita_libro,
    novedades_libros, 
    libros_nivel, 
    catalogo, 
    sugerir_libro,
    listar_sugerencias_usuario, 
    descartar_sugerencia, 
    ver_pdf,
    galeria_artistica, 
    ver_imagen, 
    buscar_libros, 
    chatbot_view,
    obtener_novedades, 
    chat_con_gemini,
    restablecer_password,
)

from .libro_views import (
    listar_libros, 
    agregar_libro, 
    editar_libro, 
    eliminar_libro,
    cambiar_estado_descarga, 
    eliminar_autorizacion,
    listar_revistas, 
    agregar_revista, 
    modificar_revista, 
    eliminar_revista,
    agregar_coleccion, 
    modificar_coleccion, 
    eliminar_coleccion,
    actualizar_orden_colecciones,
    listar_imagenes, 
    agregar_imagen, 
    editar_imagen, 
    eliminar_imagen, 
    editar_marca,
    ver_descargar_libro
)

__all__ = [
    # Auth views
    'home', 
    'CustomLoginView', 
    'logout_view', 
    'cambiar_password',
    'registrar_usuario',
    'listar_solicitudes_pendientes',
    'aprobar_usuario',
    'rechazar_usuario',
    'restablecer_password_admin',
    'restablecer_password_api',
    'upload_to_drive_ajax',  # ← NUEVO EN __ALL__
    
    # Admin views
    'lista_usuarios', 
    'agregar_usuario', 
    'modificar_usuario', 
    'eliminar_usuario',
    'principal', 
    'agregar_categoria', 
    'editar_categoria', 
    'eliminar_categoria',
    'agregar_autor', 
    'editar_autor', 
    'eliminar_autor', 
    'listar_sugerencias',
    'aprobar_sugerencia', 
    'usuarios_activos', 
    'ver_historial_usuario',
    # ============================================
    # NUEVAS VISTAS PARA GESTIÓN DE SOLICITUDES
    # ============================================
    'gestionar_solicitudes',
    'aprobar_solicitud',
    'rechazar_solicitud',
    'ver_documentos_solicitud',
    
    # Usuario views
    'inicio', 
    'perfil', 
    'historial_visitas', 
    'registrar_visita_libro',
    'novedades_libros', 
    'libros_nivel', 
    'catalogo', 
    'sugerir_libro',
    'listar_sugerencias_usuario', 
    'descartar_sugerencia', 
    'ver_pdf',
    'galeria_artistica', 
    'ver_imagen', 
    'buscar_libros', 
    'chatbot_view',
    'obtener_novedades', 
    'chat_con_gemini',
    'restablecer_password',
    
    # Libro views
    'listar_libros', 
    'agregar_libro', 
    'editar_libro', 
    'eliminar_libro',
    'cambiar_estado_descarga', 
    'eliminar_autorizacion',
    'listar_revistas', 
    'agregar_revista', 
    'modificar_revista', 
    'eliminar_revista',
    'agregar_coleccion', 
    'modificar_coleccion', 
    'eliminar_coleccion',
    'actualizar_orden_colecciones',
    'listar_imagenes', 
    'agregar_imagen', 
    'editar_imagen', 
    'eliminar_imagen', 
    'editar_marca',
    'ver_descargar_libro'
]