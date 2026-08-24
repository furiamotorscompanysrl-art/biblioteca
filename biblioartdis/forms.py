# forms.py
from django import forms
import locale
from datetime import datetime
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
            pass  # Usar locale por defecto

class LoginForm(forms.Form):
    correo = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ingrese su correo electrónico',
            'id': 'id_correo'
        })
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ingrese su contraseña',
            'id': 'id_password'
        })
    )


class VisitaFilterForm(forms.Form):
    MESES = [
        (1, 'Enero'), (2, 'Febrero'), (3, 'Marzo'), (4, 'Abril'),
        (5, 'Mayo'), (6, 'Junio'), (7, 'Julio'), (8, 'Agosto'),
        (9, 'Septiembre'), (10, 'Octubre'), (11, 'Noviembre'), (12, 'Diciembre')
    ]
    
    # Generar años a partir del año actual hasta un rango de 10 años hacia atrás
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
                # Validar que la fecha sea válida
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
        # Make all fields optional by default
        for field in self.fields:
            self.fields[field].required = False
            if 'class' not in self.fields[field].widget.attrs:
                self.fields[field].widget.attrs.update({'class': 'form-control'})
        
        # Set required fields
        self.fields['nombres'].required = True
        self.fields['ci'].required = True
        self.fields['correo'].required = True
        self.fields['nro_celular'].required = True

    class Meta:
        model = Usuario
        fields = [
            'nombres', 
            'apepat', 
            'apemat', 
            'ci', 
            'correo', 
            'extension',
            'complemento',
            'tipo_usuario',
            'ru',
            'nro_celular',
            'esta_activo',
            'fecha_baja'
        ]
        widgets = {
            'fecha_baja': forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control'}),
            'extension': forms.Select(attrs={'class': 'form-control'}),
            'tipo_usuario': forms.Select(attrs={'class': 'form-control'}),
        }

    def clean_correo(self):
        correo = self.cleaned_data.get('correo')
        if not correo:
            raise forms.ValidationError('El correo es requerido.')
        # Verificar si el correo ya existe, excluyendo el usuario actual
        if Usuario.objects.filter(correo=correo).exclude(pk=self.instance.pk).exists():
            raise forms.ValidationError('Este correo ya está registrado.')
        return correo

    def clean_ci(self):
        ci = self.cleaned_data.get('ci')
        if not ci:
            raise forms.ValidationError('El CI es requerido.')
        # Verificar si el CI ya existe, excluyendo el usuario actual
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

        if password_nuevo and password_confirmacion:
            if password_nuevo != password_confirmacion:
                raise forms.ValidationError('Las contraseñas no coinciden')
        return cleaned_data