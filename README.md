# Carrera de Artes Plásticas y Diseño Gráfico - Sistema de Gestión de Biblioteca

Desarrollado por: Lex Carita

© 2024 BiblioArtdis. Todos los derechos reservados.

## Aviso de Copyright

Este software está protegido por derechos de autor. La reproducción o distribución no autorizada de este software, o cualquier porción del mismo, puede resultar en responsabilidades civiles y penales severas y será procesada en la máxima medida posible bajo la ley.

### Protección Legal

- Todo el código fuente está protegido por derechos de autor
- Las marcas comerciales y logotipos son propiedad exclusiva
- La documentación y materiales relacionados están protegidos
- Se prohíbe la ingeniería inversa del software

## Contacto

Para consultas sobre licencias y permisos, por favor contacte a los propietarios del sistema.

# Manual de Instalación - BiblioArtdis

Este es un sistema de biblioteca digital desarrollado con Django. A continuación se detallan los pasos para su instalación y configuración.

## Requisitos Previos

### Requisitos del Sistema

#### Sistema Operativo
- **Windows**: Windows 10 o superior
  - Todas las actualizaciones instaladas
  - PowerShell habilitado
- **Linux**: Ubuntu 20.04+ o distribuciones similares
  - Paquetes de desarrollo instalados

#### Hardware Mínimo
- **Procesador**: Dual-core 2GHz o superior
- **Memoria RAM**: 2 GB mínimo (4 GB recomendado)
- **Espacio en Disco**: 2 GB disponible
  - Sistema base: 500 MB
  - Entorno virtual y dependencias: 500 MB
  - Espacio para datos y archivos: 1 GB

### Software Necesario

#### 1. Python
- **Versión**: 3.8 o superior
- **Instalación**:
  1. Descargar de [python.org](https://www.python.org/downloads/)
  2. Marcar "Add Python to PATH" durante la instalación
  3. Verificar instalación: `python --version`

#### 3. Virtualenv
- **Propósito**: Gestionar entorno virtual Python
- **Instalación**: 
  ```bash
  pip install virtualenv
  ```
- **Verificar**: `virtualenv --version`

### Pasos de Verificación

1. **Comprobar Python**:
   ```bash
   python --version
   pip --version
   ```

2. **Crear Entorno Virtual**:
   ```bash
   python -m venv venv
   ```

3. **Activar Entorno**:
   ```bash
   # Windows
   venv\Scripts\activate
   
   # Linux/macOS
   source venv/bin/activate
   ```

### Resolución de Problemas Comunes

1. **Python no encontrado**:
   - Reinstalar Python marcando "Add to PATH"
   - Reiniciar el sistema

2. **Pip no funciona**:
   ```bash
   python -m ensurepip --default-pip
   ```

3. **Error al crear entorno virtual**:
   - Ejecutar como administrador
   - Verificar permisos de escritura

### 2. Requisitos del Sistema

#### 2.1 Sistema Operativo
- **Windows**
  - Windows 10 (versión 1903 o superior)
  - Windows 11
  - Actualizaciones de sistema al día
  - PowerShell 5.1 o superior

- **Linux**
  - Ubuntu 20.04 LTS o superior
  - Debian 11 o superior
  - CentOS 8 o superior
  - Paquetes base de desarrollo:
    ```bash
    # Ubuntu/Debian
    sudo apt-get install python3-dev default-libmysqlclient-dev build-essential
    
    # CentOS
    sudo yum groupinstall "Development Tools"
    ```

#### 2.2 Recursos de Hardware
- **Procesador**:
  - Mínimo: Dual-core 2GHz
  - Recomendado: Quad-core 2.5GHz o superior

- **Memoria RAM**:
  - Mínimo: 2 GB
  - Recomendado: 4 GB
  - Óptimo: 8 GB o más para desarrollo

- **Espacio en Disco**:
  - Sistema Base: 500 MB
  - Entorno Virtual: 200 MB
  - Dependencias: 300 MB
  - Base de Datos y Media: 1 GB (expansible)
  - Espacio Total Recomendado: 2 GB mínimo

- **Conexión a Internet**:
  - Requerida para instalación
  - Mínimo: 1 Mbps
  - Recomendado: 5 Mbps o superior

### 3. Dependencias Principales

#### 3.1 Django Framework y Componentes
- **Django Core** (4.2.0+)
  ```bash
  pip install Django>=4.2.0
  ```

- **Componentes Django**:
  - django-admin-interface
    - Para personalización del panel admin
    - Requiere: django-colorfield
  - django-rest-framework
    - Para APIs RESTful
    - Incluye serializers y viewsets
  - django-extensions
    - Herramientas adicionales de desarrollo
    - Shell plus y debugging

#### 3.2 Bibliotecas Python Esenciales
- **Procesamiento de Imágenes**:
  - Pillow>=9.5.0
    - Soporte para: JPEG, PNG, GIF, WebP
    - Manipulación y optimización de imágenes

- **Procesamiento de Lenguaje**:
  - NLTK>=3.8.1
    - Tokenización
    - Análisis de sentimientos
    - Corpus necesarios:
      ```python
      import nltk
      nltk.download(['punkt', 'averaged_perceptron_tagger', 'wordnet'])
      ```

- **Gestión de Formularios**:
  - django-crispy-forms>=2.0
  - django-widget-tweaks>=1.4.12
  - Mejoras visuales y funcionales

- **Seguridad y Optimización**:
  - python-dotenv>=1.0.0
  - whitenoise>=6.5.0
  - gunicorn>=21.2.0

### 4. Configuración del Entorno

#### 4.1 Variables de Entorno
- **Variables Requeridas**:
  ```env
  DJANGO_SETTINGS_MODULE=arteydis.settings
  DEBUG=True
  SECRET_KEY=your-secret-key
  DATABASE_URL=sqlite:///db.sqlite3
  ```

#### 4.2 Navegadores Soportados
- **Versiones Mínimas**:
  - Chrome 90+
  - Firefox 88+
  - Edge 90+
  - Safari 14+

#### 4.3 Herramientas de Desarrollo
- **IDEs Recomendados**:
  - VS Code
    - Extensiones:
      - Python
      - Django
      - GitLens
  - PyCharm Professional
    - Con soporte Django integrado

- **Herramientas de Base de Datos**:
  - SQLite Browser
  - DBeaver (alternativa)

- **Herramientas de API**:
  - Postman
  - Insomnia
  - Thunder Client (VS Code)

### 5. Conocimientos Técnicos

#### 5.1 Conocimientos Básicos Necesarios
- **Línea de Comandos**:
  - Navegación básica
  - Gestión de archivos
  - Comandos pip y python

- **Python**:
  - Sintaxis básica
  - Funciones y clases
  - Manejo de excepciones
  - Entornos virtuales

- **Bases de Datos**:
  - Conceptos SQL básicos
  - Modelos de datos
  - Relaciones

#### 5.2 Conocimientos Adicionales Útiles
- **Django**:
  - MVT (Model-View-Template)
  - ORM básico
  - Sistema de plantillas
  - Admin site

- **Frontend**:
  - HTML5
  - CSS3
  - JavaScript básico
  - Bootstrap 5

- **APIs**:
  - REST conceptos
  - JSON
  - Endpoints
  - Autenticación básica

### 6. Recomendaciones Adicionales

#### 6.1 Seguridad
- Firewall configurado
- Antivirus actualizado
- Puerto 8000 disponible (desarrollo)
- Puerto 80/443 (producción)

#### 6.2 Backup y Versionado
- Sistema de respaldo configurado
- Git inicializado
- .gitignore apropiado

#### 6.3 Entorno Virtual
- Uso obligatorio
- Nombre sugerido: `venv`
- Separación de dependencias

## Pasos de Instalación

1. **Clonar o Descargar el Repositorio**
   ```bash
   git clone <url-del-repositorio>
   # O descargar y descomprimir el archivo ZIP
   ```

2. **Crear y Activar el Entorno Virtual**
   ```bash
   # Crear entorno virtual
   python -m venv venv

   # Activar entorno virtual
   # En Windows:
   venv\Scripts\activate
   # En Linux/Mac:
   source venv/bin/activate
   ```

3. **Instalar Dependencias**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configurar la Base de Datos**
   ```bash
   python manage.py migrate
   ```

5. **Crear un Superusuario (Administrador)**
   ```bash
   python manage.py createsuperuser
   ```

6. **Recolectar Archivos Estáticos**
   ```bash
   python manage.py collectstatic
   ```

7. **Iniciar el Servidor de Desarrollo**
   ```bash
   python manage.py runserver
   ```

## Estructura del Proyecto

- `arteydis/`: Configuración principal del proyecto
- `biblioartdis/`: Aplicación principal
  - `models.py`: Modelos de datos
  - `views.py`: Lógica de las vistas
  - `forms.py`: Formularios
  - `admin.py`: Configuración del panel de administración
- `media/`: Archivos subidos por usuarios
- `static/`: Archivos estáticos (CSS, JS, imágenes)
- `templates/`: Plantillas HTML
- `manage.py`: Script de gestión de Django

## Características Principales

1. Sistema de gestión de biblioteca
2. Panel de administración personalizado
3. Sistema de búsqueda integrado
4. Chatbot para asistencia
5. Gestión de archivos multimedia

## Configuración Adicional

### Base de Datos
El sistema usa SQLite por defecto. Para usar otra base de datos, modifica la configuración en `arteydis/settings.py`.

### Archivos Estáticos y Media
- Los archivos estáticos se sirven desde `/static/`
- Los archivos multimedia se almacenan en `/media/`

### Chatbot
El sistema incluye un chatbot integrado con las siguientes características:
- Procesamiento de lenguaje natural
- Registro de errores en `chatbot_errors.log`

## Solución de Problemas

1. **Errores de Dependencias**
   ```bash
   pip install -r requirements.txt --upgrade
   ```

2. **Errores de Base de Datos**
   ```bash
   python manage.py makemigrations
   python manage.py migrate
   ```

3. **Errores de Archivos Estáticos**
   ```bash
   python manage.py collectstatic --clear
   ```

## Mantenimiento

- Revisar regularmente `debug.log` para errores
- Monitorear `chatbot_errors.log` para problemas del chatbot
- Hacer copias de seguridad regulares de la base de datos

## Soporte

Para reportar problemas o solicitar ayuda, por favor:
1. Revisa los logs de error
2. Verifica la configuración
3. Contacta al equipo de soporte

---

Desarrollado con Django Framework
