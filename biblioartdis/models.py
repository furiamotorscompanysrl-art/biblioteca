from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from datetime import date
import io
from PIL import Image, ImageDraw, ImageFont
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.utils import timezone
from datetime import timedelta
from django.db.models import Count

# Importar Cloudinary (solo para imágenes y archivos pequeños)
from cloudinary.models import CloudinaryField

def get_fecha_baja_default():
    return timezone.now() + timedelta(days=5*365)


class Usuario(models.Model):
    opciones_usuarios = (
        ('Estudiante', 'Estudiante'),
        ('Administrador', 'Administrador'),
        ('Docente', 'Docente'),
        ('Externo', 'Externo'),
    )
    opciones_extensiones = (
        ('LP', 'LP'),
        ('CH', 'CH'),
        ('CB', 'CB'),
        ('OR', 'OR'),
        ('PT', 'PT'),
        ('TJ', 'TJ'),
        ('SC', 'SC'),
        ('BE', 'BE'),
        ('PD', 'PD'),
    )
    usuario_id = models.AutoField(primary_key=True)  
    nombres = models.CharField(max_length=50)
    apepat = models.CharField(max_length=30)
    apemat = models.CharField(max_length=30)
    ci = models.CharField(max_length=20)
    correo = models.EmailField()
    extension = models.CharField(max_length=5, choices=opciones_extensiones)
    complemento = models.CharField(max_length=100, blank=True, null=True)
    tipo_usuario = models.CharField(max_length=50, choices=opciones_usuarios)
    ru = models.CharField(max_length=20, blank=True, null=True)
    nro_celular = models.CharField(max_length=20)
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True, blank=True)
    fecha_alta = models.DateTimeField(default=timezone.now)
    fecha_baja = models.DateTimeField(null=True, blank=True,
        default=get_fecha_baja_default
    )
    esta_activo = models.BooleanField(default=True)

    class Meta:
        ordering = ['-fecha_alta']

    def __str__(self):
        try:
            nombre_str = str(self.nombres) if self.nombres else "Sin nombre"
            tipo_str = str(self.tipo_usuario) if self.tipo_usuario else "Sin tipo"
            return f"ID: {self.usuario_id} Usuario: {nombre_str}, Tipo: {tipo_str}"
        except:
            return f"Usuario {self.usuario_id}"

    def save(self, *args, **kwargs):
        if not self.pk:
            self.fecha_baja = get_fecha_baja_default()
        super().save(*args, **kwargs)

    @property
    def dias_restantes(self):
        if self.fecha_baja:
            delta = self.fecha_baja - timezone.now()
            return max(0, delta.days)
        return 0

    @property
    def estado(self):
        if not self.esta_activo:
            return "Inactivo"
        if self.dias_restantes <= 0:
            return "Expirado"
        return "Activo"

    @classmethod
    def get_usuarios_por_vencer(cls, dias=30):
        fecha_limite = timezone.now() + timedelta(days=dias)
        return cls.objects.filter(
            esta_activo=True,
            fecha_baja__lte=fecha_limite,
            fecha_baja__gt=timezone.now()
        )

    @classmethod
    def get_estadisticas(cls):
        total = cls.objects.count()
        activos = cls.objects.filter(esta_activo=True).count()
        por_tipo = cls.objects.filter(esta_activo=True).values(
            'tipo_usuario'
        ).annotate(total=Count('tipo_usuario'))
        
        return {
            'total_usuarios': total,
            'usuarios_activos': activos,
            'por_tipo': por_tipo
        }


# ============================================
# SEÑAL COMENTADA - DESACTIVADA TEMPORALMENTE
# ============================================
# La señal está desactivada porque:
# 1. El auth_views.py ya crea usuarios automáticamente con get_or_create
# 2. El Admin también maneja la creación de perfiles automáticamente
# 3. Esta señal causaba conflictos (duplicate key) al crear usuarios desde Admin
#
# Si se necesita reactivar en el futuro, descomentar el código siguiente:
# ============================================

# @receiver(post_save, sender=User)
# def create_or_update_user_profile(sender, instance, created, **kwargs):
#     """
#     Crea o actualiza el perfil Usuario cuando se crea/actualiza un User
#     Usa get_or_create para evitar duplicados
#     """
#     if created:
#         # Para usuarios NUEVOS: crear perfil solo si no existe
#         perfil, created = Usuario.objects.get_or_create(
#             user=instance,
#             defaults={
#                 'nombres': instance.first_name if instance.first_name else (instance.username if instance.username else "Usuario"),
#                 'apepat': '-',
#                 'apemat': '-',
#                 'ci': instance.username if instance.username else 'SIN CI',
#                 'correo': instance.email if instance.email else f'{instance.username}@example.com',
#                 'extension': 'LP',
#                 'tipo_usuario': 'Externo',
#                 'nro_celular': '00000000'
#             }
#         )
#         if created:
#             print(f"✅ Perfil Usuario creado para: {instance.username}")
#         else:
#             print(f"⚠️ Perfil Usuario ya existía para: {instance.username}")
#     else:
#         # Para usuarios EXISTENTES: actualizar datos si es necesario
#         try:
#             perfil = instance.usuario
#             # Actualizar campos si cambiaron en User
#             if instance.first_name and perfil.nombres != instance.first_name:
#                 perfil.nombres = instance.first_name
#             if instance.email and perfil.correo != instance.email:
#                 perfil.correo = instance.email
#             perfil.save()
#             print(f"🔄 Perfil Usuario actualizado para: {instance.username}")
#         except Usuario.DoesNotExist:
#             # Si por alguna razón no existe, crearlo
#             Usuario.objects.create(
#                 user=instance,
#                 nombres=instance.first_name if instance.first_name else instance.username,
#                 apepat='-',
#                 apemat='-',
#                 ci=instance.username,
#                 correo=instance.email or f'{instance.username}@example.com',
#                 extension='LP',
#                 tipo_usuario='Externo',
#                 nro_celular='00000000'
#             )
#             print(f"✅ Perfil Usuario recreado para: {instance.username}")


class Autor(models.Model):
    id_autor = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=100)

    def __str__(self):
        try:
            if self.nombre and self.nombre.strip():
                return str(self.nombre)
            return f"Autor {self.id_autor}"
        except:
            return f"Autor {self.id_autor}"


class Categoria(models.Model):
    id_categoria = models.AutoField(primary_key=True)
    nom_cat = models.CharField(max_length=100)
    
    def __str__(self):
        try:
            if self.nom_cat and self.nom_cat.strip():
                return str(self.nom_cat)
            return f"Categoría {self.id_categoria}"
        except:
            return f"Categoría {self.id_categoria}"


class Libro(models.Model):
    opciones_categ = (
        ('NIVEL 1', 'NIVEL 1'),
        ('NIVEL 2', 'NIVEL 2'),
        ('NIVEL 3', 'NIVEL 3'),
        ('NIVEL 4', 'NIVEL 4'),
        ('OTRO', 'OTRO'),
    ) 

    opciones_tipo = (
        ('LIBRO', 'Libro'),
        ('ARTICULO', 'Artículo'),
        ('REVISTA', 'Revista'),
        ('TESIS', 'Tesis'),
        ('DICCIONARIO', 'Diccionario'),
        ('MONOGRAFIA', 'Monografía'),
        ('FOLLETO', 'Folleto'),
        ('INFORME', 'Informe'),
        ('OTRO', 'Otro'),
    )
    
    id_libro = models.AutoField(primary_key=True)
    tipo = models.CharField(max_length=15, choices=opciones_tipo)
    titulo = models.CharField(max_length=255)
    edicion = models.CharField(max_length=50, blank=True, null=True)  
    categoria = models.CharField(max_length=15, choices=opciones_categ)
    
    # Cloudinary SOLO para portadas (imágenes pequeñas)
    img_portada = CloudinaryField(
        'Portada',
        folder='biblioteca/portadas/',
        transformation={'quality': 'auto', 'fetch_format': 'auto'},
        null=True,
        blank=True
    )
    
    # ⚠️ Cloudinary SOLO para PDFs pequeños (< 10 MB)
    # Para PDFs grandes (> 10 MB) usar google_drive_url
    pdf = CloudinaryField(
        'PDF',
        folder='biblioteca/pdfs/',
        resource_type='auto',
        null=True,
        blank=True
    )
    
    # ✅ NUEVO: Campo para URL de Google Drive (PDFs grandes)
    google_drive_url = models.URLField(
        'URL de Google Drive',
        max_length=500,
        blank=True,
        null=True,
        help_text='Enlace de Google Drive para PDFs grandes (vista previa embed)'
    )
    
    # URL externa alternativa (para otros servicios)
    pdf_url = models.URLField(
        max_length=500, 
        blank=True, 
        null=True,
        help_text='URL externa del PDF (Google Drive, OneDrive, etc.)'
    )
    
    archivo_autorizacion = CloudinaryField(
        'Autorización',
        folder='biblioteca/autorizaciones/',
        resource_type='auto',
        null=True,
        blank=True
    )
    
    autores = models.ManyToManyField('Autor')
    fecha_publicacion = models.DateField(default=date.today)
    descripcion = models.TextField(blank=True, null=True)
    palabra_clave = models.TextField(blank=True, null=True)
    descarga_autorizada = models.BooleanField(default=True)
    categorias = models.ManyToManyField(Categoria, blank=True)

    def agregar_palabras_claves(self, palabras):
        palabras_claves_actuales = self.palabra_clave.split(', ') if self.palabra_clave else []
        nuevas_palabras = [palabra.strip() for palabra in palabras.split(',')]
        palabras_claves_actuales.extend(nuevas_palabras)
        self.palabra_clave = ', '.join(palabras_claves_actuales)
        self.save()

    def get_pdf_display_url(self):
        """
        Retorna la URL para mostrar el PDF en el template.
        Prioridad: google_drive_url → pdf_url → pdf de Cloudinary
        """
        if self.google_drive_url:
            # Convertir URL de Google Drive a embed si es necesario
            if 'drive.google.com' in self.google_drive_url:
                file_id = self.google_drive_url.split('/d/')[1].split('/')[0] if '/d/' in self.google_drive_url else None
                if file_id:
                    return f'https://drive.google.com/file/d/{file_id}/preview'
            return self.google_drive_url
        if self.pdf_url:
            return self.pdf_url
        if self.pdf:
            return self.pdf.url
        return None

    def __str__(self):
        try:
            if self.titulo and self.titulo.strip():
                return str(self.titulo)
            return f"Libro {self.id_libro}"
        except:
            return f"Libro {self.id_libro}"


class Sugerencia(models.Model):
    id_sugerencia = models.AutoField(primary_key=True)
    solicitante = models.ForeignKey(Usuario, on_delete=models.CASCADE)
    autor_sugerencia = models.CharField(max_length=50)
    titulo_sugerencia = models.CharField(max_length=80)
    fecha_sugerencia = models.DateField(auto_now_add=True)
    edicion = models.CharField(max_length=50)
    estado_respuesta = models.CharField(max_length=20, default='Pendiente')
    descripcion = models.TextField()
    respondido_por = models.ForeignKey(Usuario, on_delete=models.SET_NULL, null=True, blank=True, related_name='sugerencias_respondidas')
    fecha_respuesta = models.DateTimeField(null=True, blank=True)
    
    def __str__(self):
        try:
            titulo = str(self.titulo_sugerencia) if self.titulo_sugerencia else "Sin título"
            autor = str(self.autor_sugerencia) if self.autor_sugerencia else "Autor desconocido"
            return f"Sugerencia #{self.id_sugerencia}: {titulo} ({autor})"
        except:
            return f"Sugerencia {self.id_sugerencia}"


class Coleccion(models.Model):
    id_coleccion = models.AutoField(primary_key=True)
    nomb_colecc = models.CharField(max_length=100)
    orden = models.PositiveIntegerField(default=0)
    descripcion = models.TextField(blank=True, null=True)

    class Meta:
        ordering = ['orden']

    def __str__(self):
        try:
            if self.nomb_colecc and self.nomb_colecc.strip():
                return str(self.nomb_colecc)
            return f"Colección {self.id_coleccion}"
        except:
            return f"Colección {self.id_coleccion}"


class Revista(models.Model):
    id_revista = models.AutoField(primary_key=True)
    nro_revista = models.IntegerField(null=True, blank=True)
    coleccion = models.ForeignKey(Coleccion, on_delete=models.CASCADE)
    
    img_portada = CloudinaryField(
        'Portada',
        folder='revistas/portadas/',
        transformation={'quality': 'auto', 'fetch_format': 'auto'},
        null=True,
        blank=True
    )
    
    pdf = CloudinaryField(
        'PDF',
        folder='revistas/pdfs/',
        resource_type='auto',
        null=True,
        blank=True
    )
    
    google_drive_url = models.URLField(
        'URL de Google Drive',
        max_length=500,
        blank=True,
        null=True,
        help_text='Enlace de Google Drive para PDFs grandes'
    )
    
    url = models.URLField(max_length=200, blank=True, null=True)
    descripcion = models.TextField(blank=True, null=True)

    def __str__(self):
        try:
            coleccion_nombre = str(self.coleccion.nomb_colecc) if self.coleccion and self.coleccion.nomb_colecc else "Sin colección"
            numero = f"#{self.nro_revista}" if self.nro_revista else "s/n"
            return f"Revista {numero} de la colección {coleccion_nombre}"
        except:
            return f"Revista {self.id_revista}"


class VisitaLibro(models.Model):
    fecha_visualizacion = models.DateTimeField(auto_now=True)
    fecha_consulta = models.DateField(default=date.today)
    visitante = models.ForeignKey('Usuario', on_delete=models.CASCADE)
    libro_visitado = models.ForeignKey('Libro', on_delete=models.CASCADE)

    def __str__(self):
        try:
            visitante_str = str(self.visitante) if self.visitante else "Usuario desconocido"
            libro_str = str(self.libro_visitado) if self.libro_visitado else "Libro desconocido"
            fecha_str = str(self.fecha_visualizacion) if self.fecha_visualizacion else "fecha desconocida"
            return f"{visitante_str} visitó {libro_str} el {fecha_str}"
        except:
            return f"Visita {self.id}"

    @classmethod
    def obtUltimaVisitaLibro(cls, usuario, libro, fecha):
        try:
            return cls.objects.filter(
                visitante=usuario,
                libro_visitado=libro,
                fecha_consulta__year=fecha.year,
                fecha_consulta__month=fecha.month
            ).latest('fecha_visualizacion')
        except cls.DoesNotExist:
            return None


class Imagen(models.Model):
    id_Imagen = models.AutoField(primary_key=True)
    titulo = models.CharField(max_length=255)
    autorImg = models.CharField(max_length=100)
    descripcion = models.TextField(blank=True, null=True)
    
    img_portada = CloudinaryField(
        'Imagen',
        folder='imagenes/',
        transformation={'quality': 'auto', 'fetch_format': 'auto', 'crop': 'limit', 'width': 1200},
        null=True,
        blank=True
    )
    
    pdf = CloudinaryField(
        'PDF',
        folder='imagenes/pdfs/',
        resource_type='auto',
        null=True,
        blank=True
    )
    
    fecha_subida = models.DateTimeField(auto_now_add=True)
    
    marca_agua = CloudinaryField(
        'Marca de agua',
        folder='imagenes/marcas_agua/',
        null=True,
        blank=True
    )
    
    categorias = models.ManyToManyField(Categoria, blank=True)

    def __str__(self):
        try:
            if self.titulo and self.titulo.strip():
                return str(self.titulo)
            return f"Imagen {self.id_Imagen}"
        except:
            return f"Imagen {self.id_Imagen}"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)


class HistorialBusqueda(models.Model):
    usuario = models.ForeignKey(User, on_delete=models.CASCADE)
    termino_busqueda = models.CharField(max_length=255)
    fecha_busqueda = models.DateTimeField(auto_now_add=True)
   
    class Meta:
        ordering = ['-fecha_busqueda']
    
    def __str__(self):
        try:
            usuario_str = str(self.usuario.username) if self.usuario and self.usuario.username else "Usuario desconocido"
            termino = str(self.termino_busqueda) if self.termino_busqueda else "Sin término"
            return f"{usuario_str} buscó: {termino}"
        except:
            return f"Búsqueda {self.id}"


class CodigoVerificacion(models.Model):
    id_codigo = models.AutoField(primary_key=True)
    usuario = models.ForeignKey(User, on_delete=models.CASCADE)
    codigo = models.CharField(max_length=6)
    creado_en = models.DateTimeField(auto_now_add=True)
    expira_en = models.DateTimeField()
    usado = models.BooleanField(default=False)
    
    class Meta:
        verbose_name = "Código de verificación"
        verbose_name_plural = "Códigos de verificación"
        ordering = ['-creado_en']
    
    def __str__(self):
        try:
            email = str(self.usuario.email) if self.usuario and self.usuario.email else "usuario desconocido"
            expira = str(self.expira_en) if self.expira_en else "fecha desconocida"
            return f"Código para {email} - Expira: {expira}"
        except:
            return f"Código {self.id_codigo}"
    
    def es_valido(self):
        from django.utils import timezone
        return not self.usado and timezone.now() < self.expira_en


# ============================================
# AUDITLOG - DESACTIVADO TEMPORALMENTE
# ============================================
# from auditlog.registry import auditlog
# auditlog.register(Usuario)
# auditlog.register(Autor)
# auditlog.register(Categoria)
# auditlog.register(Libro, exclude_fields=['archivo_autorizacion'])
# auditlog.register(Sugerencia)
# auditlog.register(Imagen)
# auditlog.register(Revista)
# auditlog.register(Coleccion)