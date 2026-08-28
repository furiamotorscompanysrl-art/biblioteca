# biblioartdis/forms.py

from django import forms
import locale
from datetime import datetime
from django.contrib.auth.models import User
from .models import Autor, Imagen, Usuario, Coleccion, Revista
from django.utils import timezone
import os
import tempfile

# Configurar locale para fechas en español
try:
    locale.setlocale(locale.LC_TIME, 'es_ES.UTF-8')
except locale.Error:
    try:
        locale.setlocale(locale.LC_TIME, 'es_BO.UTF-8')
    except locale.Error:
        try:
            locale.setlocale(locale.LC_TIME, 'es_ES')
        except locale.Error:
            pass


# ============================================
# FORMULARIO DE LOGIN (EMAIL Y CONTRASEÑA)
# ============================================

class LoginForm(forms.Form):
    """Formulario de login con email y contraseña"""
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'ejemplo@umsa.bo',
            'id': 'id_email'
        }),
        label='Correo UMSA'
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ingrese su contraseña',
            'id': 'id_password'
        }),
        label='Contraseña'
    )


class VisitaFilterForm(forms.Form):
    MESES = [
        (1, 'Enero'), (2, 'Febrero'), (3, 'Marzo'), (4, 'Abril'),
        (5, 'Mayo'), (6, 'Junio'), (7, 'Julio'), (8, 'Agosto'),
        (9, 'Septiembre'), (10, 'Octubre'), (11, 'Noviembre'), (12, 'Diciembre')
    ]
    
    current_year = datetime.now().year
    AÑOS = [(year, year) for year in range(current_year, current_year - 10, -1)]
    
    mes = forms.ChoiceField(choices=MESES, label='Mes', required=True)
    año = forms.ChoiceField(choices=AÑOS, label='Año', required=True)
    vista_opcion = forms.ChoiceField(
        choices=[
            ('nivel', 'Por Nivel'),
            ('unitarias', 'Unitarias')
        ],
        label='Ver por',
        required=True
    )
    
    def clean(self):
        cleaned_data = super().clean()
        mes = cleaned_data.get('mes')
        año = cleaned_data.get('año')
        
        if mes and año:
            try:
                datetime(int(año), int(mes), 1)
            except ValueError:
                raise forms.ValidationError('La fecha seleccionada no es válida')
        
        return cleaned_data


class ColeccionForm(forms.ModelForm):
    class Meta:
        model = Coleccion
        fields = ['nomb_colecc', 'descripcion']
        labels = {
            'nomb_colecc': 'Nombre de la Colección',
            'descripcion': 'Descripción'
        }
        widgets = {
            'nomb_colecc': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ingrese el nombre de la colección'
            }),
            'descripcion': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'Ingrese la descripción de la colección',
                'rows': 3
            })
        }


class RevistaForm(forms.ModelForm):
    class Meta:
        model = Revista
        fields = ['coleccion', 'nro_revista', 'descripcion', 'img_portada', 'pdf', 'url']
        labels = {
            'nro_revista': 'Número de Revista',
            'coleccion': 'Colección',
            'descripcion': 'Descripción',
            'img_portada': 'Imagen de Portada',
            'pdf': 'Archivo PDF',
            'url': 'URL de la Revista'
        }
        widgets = {
            'nro_revista': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Número de la revista'
            }),
            'descripcion': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Descripción de la revista'
            }),
            'coleccion': forms.Select(attrs={'class': 'form-control'}),
            'url': forms.URLInput(attrs={
                'class': 'form-control',
                'placeholder': 'https://...'
            })
        }
    
    def clean_nro_revista(self):
        nro = self.cleaned_data.get('nro_revista')
        if nro and nro < 0:
            raise forms.ValidationError('El número de revista no puede ser negativo')
        return nro


class AutorForm(forms.ModelForm):
    class Meta:
        model = Autor
        fields = ['nombre']
        widgets = {
            'nombre': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nombre del autor'
            })
        }


class ImagenForm(forms.ModelForm):
    class Meta:
        model = Imagen
        fields = ['titulo', 'autorImg', 'descripcion', 'img_portada', 'pdf']
        widgets = {
            'titulo': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Título de la imagen'}),
            'autorImg': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Autor de la imagen'}),
            'descripcion': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Descripción'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields:
            if 'class' not in self.fields[field].widget.attrs:
                self.fields[field].widget.attrs.update({'class': 'form-control'})


class LibroSearchForm(forms.Form):
    query = forms.CharField(
        max_length=255, 
        required=False, 
        label='Buscar',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Buscar libros...'
        })
    )


class UsuarioForm(forms.ModelForm):
    correo = forms.EmailField(required=True, widget=forms.EmailInput(attrs={'class': 'form-control'}))
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields:
            self.fields[field].required = False
            if 'class' not in self.fields[field].widget.attrs:
                self.fields[field].widget.attrs.update({'class': 'form-control'})
        
        self.fields['nombres'].required = True
        self.fields['ci'].required = True
        self.fields['correo'].required = True
        self.fields['nro_celular'].required = True

    class Meta:
        model = Usuario
        fields = [
            'nombres', 'apepat', 'apemat', 'ci', 'correo', 'extension',
            'complemento', 'tipo_usuario', 'ru', 'nro_celular',
            'esta_activo', 'fecha_baja', 'telefono', 'direccion',
            'carrera', 'semestre', 'anio_ingreso', 'estado_registro',
            'matricula_pdf', 'carnet_frente', 'carnet_reverso'
        ]
        widgets = {
            'fecha_baja': forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control'}),
            'extension': forms.Select(attrs={'class': 'form-control'}),
            'tipo_usuario': forms.Select(attrs={'class': 'form-control'}),
            'estado_registro': forms.Select(attrs={'class': 'form-control'}),
        }

    def clean_correo(self):
        correo = self.cleaned_data.get('correo')
        if not correo:
            raise forms.ValidationError('El correo es requerido.')
        if Usuario.objects.filter(correo=correo).exclude(pk=self.instance.pk).exists():
            raise forms.ValidationError('Este correo ya está registrado.')
        return correo

    def clean_ci(self):
        ci = self.cleaned_data.get('ci')
        if not ci:
            raise forms.ValidationError('El CI es requerido.')
        if Usuario.objects.filter(ci=ci).exclude(pk=self.instance.pk).exists():
            raise forms.ValidationError('Este CI ya está registrado.')
        return ci
    
    def clean_nro_celular(self):
        nro = self.cleaned_data.get('nro_celular')
        if nro and len(nro) != 8:
            raise forms.ValidationError('El número de celular debe tener 8 dígitos.')
        return nro


class CambiarPasswordForm(forms.Form):
    password_actual = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ingrese su contraseña actual'
        })
    )
    password_nuevo = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ingrese su nueva contraseña (mínimo 8 caracteres)'
        })
    )
    password_confirmacion = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Confirme su nueva contraseña'
        })
    )

    def clean_password_nuevo(self):
        password = self.cleaned_data.get('password_nuevo')
        if password and len(password) < 8:
            raise forms.ValidationError('La contraseña debe tener al menos 8 caracteres.')
        return password

    def clean(self):
        cleaned_data = super().clean()
        password_nuevo = cleaned_data.get('password_nuevo')
        password_confirmacion = cleaned_data.get('password_confirmacion')
        if password_nuevo and password_confirmacion and password_nuevo != password_confirmacion:
            raise forms.ValidationError('Las contraseñas no coinciden')
        return cleaned_data


# ============================================
# FORMULARIO DE REGISTRO CON APROBACIÓN
# CON SUBIDA A GOOGLE DRIVE
# ============================================

class RegistroUsuarioForm(forms.ModelForm):
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Contraseña (mínimo 9 caracteres)'
        }),
        label='Contraseña',
        min_length=9,
        help_text='Mínimo 9 caracteres'
    )
    password_confirm = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Confirmar contraseña'
        }),
        label='Confirmar Contraseña'
    )
    
    class Meta:
        model = Usuario
        fields = [
            'nombres', 'apepat', 'apemat',
            'ci', 'extension', 'complemento',
            'correo', 'telefono', 'direccion',
            'carrera', 'semestre', 'anio_ingreso',
            'tipo_usuario',
            'matricula_pdf', 'carnet_frente', 'carnet_reverso'
        ]
        widgets = {
            'nombres': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: Juan'
            }),
            'apepat': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: Pérez'
            }),
            'apemat': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: Gómez (opcional)'
            }),
            'ci': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: 1234567'
            }),
            'extension': forms.Select(attrs={
                'class': 'form-control'
            }),
            'complemento': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: 123 (opcional)'
            }),
            'correo': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'ejemplo@umsa.bo'
            }),
            'telefono': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: 71234567'
            }),
            'direccion': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'Ej: Calle 123, Zona Central'
            }),
            'carrera': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: Ingeniería de Sistemas'
            }),
            'semestre': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: 5to Semestre'
            }),
            'anio_ingreso': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: 2023'
            }),
            'tipo_usuario': forms.Select(attrs={
                'class': 'form-control'
            }),
            'matricula_pdf': forms.FileInput(attrs={
                'class': 'form-control-file',
                'accept': '.pdf'
            }),
            'carnet_frente': forms.FileInput(attrs={
                'class': 'form-control-file',
                'accept': 'image/*'
            }),
            'carnet_reverso': forms.FileInput(attrs={
                'class': 'form-control-file',
                'accept': 'image/*'
            }),
        }
        labels = {
            'nombres': 'Nombre',
            'apepat': 'Apellido Paterno',
            'apemat': 'Apellido Materno',
            'ci': 'CI',
            'extension': 'Extensión',
            'complemento': 'Complemento (opcional)',
            'correo': 'Correo UMSA',
            'telefono': 'Teléfono / Celular',
            'direccion': 'Dirección',
            'carrera': 'Carrera',
            'semestre': 'Semestre',
            'anio_ingreso': 'Año de Ingreso',
            'tipo_usuario': 'Tipo de Usuario',
            'matricula_pdf': 'Matrícula (PDF)',
            'carnet_frente': 'Carnet - Frente',
            'carnet_reverso': 'Carnet - Reverso',
        }
        help_texts = {
            'correo': 'Debe ser @umsa.bo',
            'tipo_usuario': 'Selecciona tu tipo de usuario',
            'matricula_pdf': 'Sube tu matrícula en formato PDF',
            'carnet_frente': 'Sube la foto del frente de tu carnet',
            'carnet_reverso': 'Sube la foto del reverso de tu carnet',
        }
    
    def clean_correo(self):
        correo = self.cleaned_data.get('correo', '').lower().strip()
        CORREO_ESPECIAL = 'vc3070934@gmail.com'
        
        if not (correo.endswith('@umsa.bo') or correo == CORREO_ESPECIAL):
            raise forms.ValidationError('❌ Solo se permiten correos institucionales @umsa.bo')
        
        if User.objects.filter(email=correo).exists():
            raise forms.ValidationError('❌ Este correo ya está registrado')
        
        if Usuario.objects.filter(correo=correo).exists():
            raise forms.ValidationError('❌ Este correo ya está registrado')
        
        return correo
    
    def clean_ci(self):
        ci = self.cleaned_data.get('ci', '').strip()
        if not ci:
            raise forms.ValidationError('❌ El CI es requerido')
        if not ci.isdigit():
            raise forms.ValidationError('❌ El CI debe contener solo números')
        if len(ci) < 6:
            raise forms.ValidationError('❌ El CI debe tener al menos 6 dígitos')
        
        if Usuario.objects.filter(ci=ci).exists():
            raise forms.ValidationError('❌ Este CI ya está registrado')
        
        return ci
    
    def clean_password(self):
        password = self.cleaned_data.get('password', '')
        if len(password) < 9:
            raise forms.ValidationError('❌ La contraseña debe tener al menos 9 caracteres')
        return password
    
    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        password_confirm = cleaned_data.get('password_confirm')
        
        if password and password_confirm and password != password_confirm:
            raise forms.ValidationError('❌ Las contraseñas no coinciden')
        
        # ============================================
        # VALIDACIONES POR ROL
        # ============================================
        tipo_usuario = cleaned_data.get('tipo_usuario')
        matricula = cleaned_data.get('matricula_pdf')
        carnet_frente = cleaned_data.get('carnet_frente')
        carnet_reverso = cleaned_data.get('carnet_reverso')
        
        if tipo_usuario == 'Estudiante':
            if not matricula:
                raise forms.ValidationError('❌ Los estudiantes deben subir la matrícula en PDF')
            if not carnet_frente:
                raise forms.ValidationError('❌ Los estudiantes deben subir la foto del frente del carnet')
            if not carnet_reverso:
                raise forms.ValidationError('❌ Los estudiantes deben subir la foto del reverso del carnet')
        
        elif tipo_usuario == 'Docente':
            if not carnet_frente:
                raise forms.ValidationError('❌ Los docentes deben subir la foto del frente del carnet')
            if not carnet_reverso:
                raise forms.ValidationError('❌ Los docentes deben subir la foto del reverso del carnet')
            # No requiere matrícula
        
        elif tipo_usuario == 'Investigador':
            if not carnet_frente:
                raise forms.ValidationError('❌ Los investigadores deben subir la foto del frente del carnet')
            if not carnet_reverso:
                raise forms.ValidationError('❌ Los investigadores deben subir la foto del reverso del carnet')
            # No requiere matrícula
        
        return cleaned_data
    
    def _subir_a_drive(self, archivo, usuario_id, tipo, carpeta_destino):
        """Subir un archivo a Google Drive"""
        try:
            from .google_drive_utils import drive_service
            from django.conf import settings
            
            if not archivo:
                return None
            
            folder_id = drive_service.get_or_create_folder(
                carpeta_destino,
                settings.GOOGLE_DRIVE_FOLDER_ID
            )
            
            if not folder_id:
                return None
            
            ext = os.path.splitext(archivo.name)[1]
            with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as tmp_file:
                for chunk in archivo.chunks():
                    tmp_file.write(chunk)
                tmp_path = tmp_file.name
            
            nombre_archivo = f"{usuario_id}_{tipo}{ext}"
            resultado = drive_service.upload_file(
                file_path=tmp_path,
                file_name=nombre_archivo,
                folder_id=folder_id
            )
            
            os.unlink(tmp_path)
            
            if resultado:
                return resultado['download_link']
            return None
            
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error subiendo archivo a Drive: {e}")
            return None
    
    def save(self, commit=True):
        from .google_drive_utils import drive_service
        from django.conf import settings
        
        correo = self.cleaned_data['correo'].lower().strip()
        
        username = correo.split('@')[0]
        if User.objects.filter(username=username).exists():
            import random
            username = f"{username}_{random.randint(100, 999)}"
        
        user = User.objects.create_user(
            username=username,
            email=correo,
            password=self.cleaned_data['password'],
            first_name=self.cleaned_data['nombres'],
            last_name=f"{self.cleaned_data['apepat']} {self.cleaned_data.get('apemat', '')}".strip()
        )
        user.is_active = False
        user.save()
        
        usuario = super().save(commit=False)
        usuario.user = user
        usuario.correo = correo
        usuario.estado_registro = 'pendiente'
        usuario.fecha_solicitud = timezone.now()
        usuario.esta_activo = False
        
        if commit:
            usuario.save()
            
            usuario_id = usuario.usuario_id
            tipo_usuario = self.cleaned_data.get('tipo_usuario')
            
            # Subir documentos según el rol
            # Matrícula - SOLO para estudiantes
            if tipo_usuario == 'Estudiante':
                if 'matricula_pdf' in self.cleaned_data and self.cleaned_data['matricula_pdf']:
                    url = self._subir_a_drive(
                        self.cleaned_data['matricula_pdf'],
                        usuario_id,
                        'matricula',
                        'Usuarios/Matriculas'
                    )
                    if url:
                        usuario.google_drive_matricula_url = url
            
            # Carnet Frente - TODOS los roles
            if 'carnet_frente' in self.cleaned_data and self.cleaned_data['carnet_frente']:
                url = self._subir_a_drive(
                    self.cleaned_data['carnet_frente'],
                    usuario_id,
                    'carnet_frente',
                    'Usuarios/Carnets/Frente'
                )
                if url:
                    usuario.google_drive_carnet_frente_url = url
            
            # Carnet Reverso - TODOS los roles
            if 'carnet_reverso' in self.cleaned_data and self.cleaned_data['carnet_reverso']:
                url = self._subir_a_drive(
                    self.cleaned_data['carnet_reverso'],
                    usuario_id,
                    'carnet_reverso',
                    'Usuarios/Carnets/Reverso'
                )
                if url:
                    usuario.google_drive_carnet_reverso_url = url
            
            usuario.save()
        
        return usuario


# ============================================
# FORMULARIO PARA RESTABLECER CONTRASEÑA (ADMIN)
# ============================================

class RestablecerPasswordForm(forms.Form):
    usuario_id = forms.IntegerField(widget=forms.HiddenInput())
    nueva_password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        label='Nueva Contraseña',
        min_length=9,
        help_text='Mínimo 9 caracteres'
    )
    confirmar_password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        label='Confirmar Contraseña'
    )
    
    def clean(self):
        cleaned_data = super().clean()
        nueva = cleaned_data.get('nueva_password')
        confirmar = cleaned_data.get('confirmar_password')
        if nueva and confirmar and nueva != confirmar:
            raise forms.ValidationError('Las contraseñas no coinciden')
        return cleaned_data