from django import forms
import locale
from datetime import datetime
from django.contrib.auth.models import User
from .models import Autor, Imagen, Usuario, Coleccion, Revista

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
# ============================================

class RegistroUsuarioForm(forms.ModelForm):
    username = forms.CharField(
        max_length=150, 
        label='Usuario',
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    email = forms.EmailField(
        label='Correo UMSA',
        widget=forms.EmailInput(attrs={'class': 'form-control'})
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        label='Contraseña',
        min_length=9,
        help_text='Mínimo 9 caracteres'
    )
    confirmar_password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        label='Confirmar Contraseña'
    )
    
    class Meta:
        model = Usuario
        fields = [
            'nombres', 'apepat', 'apemat', 'ci', 'extension', 'complemento',
            'telefono', 'direccion', 'carrera', 'semestre', 'anio_ingreso',
            'tipo_usuario', 'ru', 'nro_celular',
            'matricula_pdf', 'carnet_frente', 'carnet_reverso'
        ]
        widgets = {
            'nombres': forms.TextInput(attrs={'class': 'form-control'}),
            'apepat': forms.TextInput(attrs={'class': 'form-control'}),
            'apemat': forms.TextInput(attrs={'class': 'form-control'}),
            'ci': forms.TextInput(attrs={'class': 'form-control'}),
            'extension': forms.Select(attrs={'class': 'form-control'}),
            'complemento': forms.TextInput(attrs={'class': 'form-control'}),
            'telefono': forms.TextInput(attrs={'class': 'form-control'}),
            'direccion': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'carrera': forms.TextInput(attrs={'class': 'form-control'}),
            'semestre': forms.TextInput(attrs={'class': 'form-control'}),
            'anio_ingreso': forms.TextInput(attrs={'class': 'form-control'}),
            'tipo_usuario': forms.Select(attrs={'class': 'form-control'}),
            'ru': forms.TextInput(attrs={'class': 'form-control'}),
            'nro_celular': forms.TextInput(attrs={'class': 'form-control'}),
            'matricula_pdf': forms.FileInput(attrs={'class': 'form-control'}),
            'carnet_frente': forms.FileInput(attrs={'class': 'form-control'}),
            'carnet_reverso': forms.FileInput(attrs={'class': 'form-control'}),
        }
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if not email.endswith('@umsa.bo'):
            raise forms.ValidationError('Debes usar un correo institucional @umsa.bo')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError('Este correo ya está registrado')
        return email
    
    def clean_username(self):
        username = self.cleaned_data.get('username')
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError('Este usuario ya existe')
        return username
    
    def clean_ci(self):
        ci = self.cleaned_data.get('ci')
        if Usuario.objects.filter(ci=ci).exists():
            raise forms.ValidationError('Este CI ya está registrado')
        return ci
    
    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        confirmar = cleaned_data.get('confirmar_password')
        if password and confirmar and password != confirmar:
            raise forms.ValidationError('Las contraseñas no coinciden')
        return cleaned_data


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