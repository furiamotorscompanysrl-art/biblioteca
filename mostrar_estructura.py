#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script para generar un archivo TXT con la estructura del proyecto
Excluye: __pycache__, .venv, venv, .git, .pytest_cache, .mypy_cache, logs, staticfiles, media
"""

import os
from pathlib import Path
from datetime import datetime

# ============================================
# CONFIGURACIÓN
# ============================================
BASE_DIR = Path(__file__).resolve().parent
ARCHIVO_SALIDA = 'estructura.txt'

# Carpetas y archivos a EXCLUIR
EXCLUIR = {
    '__pycache__',
    '.venv',
    'venv',
    'env',
    '.git',
    '.pytest_cache',
    '.mypy_cache',
    '.pyc',
    '.pyo',
    '.pyd',
    'logs',
    'staticfiles',
    'media',
    'node_modules',
    '.vscode',
    '.idea',
    '.DS_Store',
    'Thumbs.db',
    '*.pyc',
    '*.pyo',
    '*.pyd',
    '*.db',
    '*.sqlite3',
}

# Extensiones a EXCLUIR
EXCLUIR_EXTENSIONES = {
    '.pyc',
    '.pyo',
    '.pyd',
    '.db',
    '.sqlite3',
    '.log',
    '.cache',
}

# Extensiones de archivos de imagen que queremos mostrar (pero no su contenido)
IMAGENES = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.svg', '.ico', '.webp'}

# ============================================
# FUNCIÓN PARA VERIFICAR SI DEBE EXCLUIR
# ============================================
def debe_excluir(nombre, ruta):
    """Verifica si un archivo o carpeta debe ser excluido"""
    
    # Excluir por nombre exacto
    if nombre in EXCLUIR:
        return True
    
    # Excluir por extensión
    extension = os.path.splitext(nombre)[1].lower()
    if extension in EXCLUIR_EXTENSIONES:
        return True
    
    # Excluir si empieza con . (archivos ocultos excepto .env)
    if nombre.startswith('.') and nombre not in ['.env', '.env.example', '.gitignore']:
        return True
    
    # Excluir si contiene ciertos patrones
    if '__pycache__' in ruta:
        return True
    
    return False

# ============================================
# FUNCIÓN PARA GENERAR ESTRUCTURA
# ============================================
def generar_estructura(directorio, prefijo='', nivel=0, max_nivel=6, archivo=None):
    """Genera la estructura de carpetas y archivos en el archivo"""
    
    # Limitar profundidad para no saturar
    if nivel > max_nivel:
        return
    
    try:
        items = sorted(os.listdir(directorio))
    except PermissionError:
        archivo.write(f"{prefijo}⚠️  [Permiso denegado]\n")
        return
    
    # Filtrar items
    items_filtrados = []
    for item in items:
        ruta = os.path.join(directorio, item)
        if debe_excluir(item, ruta):
            continue
        items_filtrados.append(item)
    
    # Contar para saber si es el último
    total = len(items_filtrados)
    
    for idx, item in enumerate(items_filtrados):
        ruta = os.path.join(directorio, item)
        es_ultimo = (idx == total - 1)
        es_directorio = os.path.isdir(ruta)
        
        # Determinar símbolo
        if es_ultimo:
            nuevo_prefijo = prefijo + '    '
            simbolo = '└── '
        else:
            nuevo_prefijo = prefijo + '│   '
            simbolo = '├── '
        
        # Obtener tamaño
        try:
            tamaño = os.path.getsize(ruta)
            if tamaño > 1024 * 1024:
                tamaño_str = f" ({tamaño / (1024 * 1024):.1f} MB)"
            elif tamaño > 1024:
                tamaño_str = f" ({tamaño / 1024:.1f} KB)"
            else:
                tamaño_str = f" ({tamaño} B)"
        except:
            tamaño_str = ""
        
        # Mostrar el item
        if es_directorio:
            archivo.write(f"{prefijo}{simbolo}📁 {item}/\n")
            generar_estructura(ruta, nuevo_prefijo, nivel + 1, max_nivel, archivo)
        else:
            # Mostrar archivo con su extensión
            extension = os.path.splitext(item)[1].lower()
            
            # Iconos según extensión
            icono = '📄'
            if extension in ['.py']:
                icono = '🐍'
            elif extension in ['.html', '.htm']:
                icono = '🌐'
            elif extension in ['.css']:
                icono = '🎨'
            elif extension in ['.js']:
                icono = '📜'
            elif extension in ['.json']:
                icono = '📦'
            elif extension in ['.yml', '.yaml']:
                icono = '⚙️'
            elif extension in ['.md']:
                icono = '📝'
            elif extension in ['.txt']:
                icono = '📃'
            elif extension in ['.sh', '.bat']:
                icono = '⚡'
            elif extension in IMAGENES:
                icono = '🖼️'
            elif extension in ['.pdf']:
                icono = '📕'
            elif extension in ['.env']:
                icono = '🔐'
            elif extension in ['.gitignore']:
                icono = '🚫'
            elif extension in ['.xml']:
                icono = '📋'
            elif extension in ['.csv']:
                icono = '📊'
            elif extension in ['.zip', '.rar', '.7z', '.tar', '.gz']:
                icono = '📦'
            
            archivo.write(f"{prefijo}{simbolo}{icono} {item}{tamaño_str}\n")

# ============================================
# FUNCIÓN PARA GENERAR RESUMEN
# ============================================
def generar_resumen(directorio, archivo):
    """Genera un resumen con archivos importantes"""
    
    archivo.write("\n" + "=" * 80 + "\n")
    archivo.write("📊 RESUMEN DE ARCHIVOS IMPORTANTES\n")
    archivo.write("=" * 80 + "\n\n")
    
    # Archivos clave
    archivos_clave = {
        'manage.py': '🐍 Archivo principal de Django',
        'settings.py': '⚙️ Configuración del proyecto',
        'urls.py': '🌐 Rutas del proyecto',
        'models.py': '📊 Modelos de base de datos',
        'views.py': '👁️ Vistas del proyecto',
        'admin.py': '🛠️ Configuración del admin',
        'forms.py': '📝 Formularios',
        'requirements.txt': '📦 Dependencias',
        'start.sh': '⚡ Script de inicio',
        'Procfile': '📋 Procfile de Railway',
        'railpack.json': '⚙️ Configuración de Railway',
        '.env': '🔐 Variables de entorno',
        '.env.example': '🔐 Ejemplo de variables',
        '.gitignore': '🚫 Archivos ignorados por Git',
        'README.md': '📝 Documentación',
    }
    
    # Buscar archivos clave
    encontrados = []
    faltantes = []
    
    for archivo_clave, descripcion in archivos_clave.items():
        encontrado = False
        for root, dirs, files in os.walk(directorio):
            # Evitar carpetas excluidas
            if any(excl in root.split(os.sep) for excl in ['__pycache__', '.venv', 'venv', '.git']):
                continue
            if archivo_clave in files:
                ruta = os.path.join(root, archivo_clave)
                tamaño = os.path.getsize(ruta)
                encontrados.append(f"  ✅ {archivo_clave} ({tamaño} B) - {descripcion}")
                encontrado = True
                break
        if not encontrado:
            faltantes.append(f"  ❌ {archivo_clave} (NO ENCONTRADO) - {descripcion}")
    
    if encontrados:
        archivo.write("📌 Archivos clave ENCONTRADOS:\n")
        for item in encontrados:
            archivo.write(item + "\n")
    
    if faltantes:
        archivo.write("\n⚠️ Archivos clave NO ENCONTRADOS:\n")
        for item in faltantes:
            archivo.write(item + "\n")
    
    # Archivos de templates
    archivo.write("\n" + "=" * 80 + "\n")
    archivo.write("📂 ARCHIVOS DE TEMPLATES (.html)\n")
    archivo.write("=" * 80 + "\n\n")
    
    templates_encontrados = []
    for root, dirs, files in os.walk(directorio):
        # Evitar carpetas excluidas
        if any(excl in root.split(os.sep) for excl in ['__pycache__', '.venv', 'venv', '.git']):
            continue
        for file in files:
            if file.endswith('.html'):
                ruta_relativa = os.path.relpath(os.path.join(root, file), directorio)
                templates_encontrados.append(ruta_relativa)
    
    if templates_encontrados:
        archivo.write(f"Total: {len(templates_encontrados)} archivos HTML\n\n")
        for item in sorted(templates_encontrados):
            archivo.write(f"  📄 {item}\n")
    else:
        archivo.write("  ❌ No se encontraron archivos .html en el proyecto\n")
    
    # Archivos estáticos
    archivo.write("\n" + "=" * 80 + "\n")
    archivo.write("📁 ARCHIVOS ESTÁTICOS\n")
    archivo.write("=" * 80 + "\n\n")
    
    static_encontrados = []
    for root, dirs, files in os.walk(directorio):
        # Evitar carpetas excluidas
        if any(excl in root.split(os.sep) for excl in ['__pycache__', '.venv', 'venv', '.git']):
            continue
        if 'static' in root.split(os.sep):
            for file in files[:10]:  # Mostrar solo 10 ejemplos
                ruta_relativa = os.path.relpath(os.path.join(root, file), directorio)
                static_encontrados.append(ruta_relativa)
    
    if static_encontrados:
        archivo.write(f"Total: {len(static_encontrados)} archivos estáticos (mostrando 10 ejemplos)\n\n")
        for item in sorted(static_encontrados)[:10]:
            archivo.write(f"  📁 {item}\n")
    else:
        archivo.write("  ⚠️ No se encontraron archivos en carpetas 'static'\n")

# ============================================
# FUNCIÓN PRINCIPAL
# ============================================
def main():
    """Función principal"""
    
    # Crear archivo de salida
    with open(ARCHIVO_SALIDA, 'w', encoding='utf-8') as f:
        # Escribir encabezado
        f.write("=" * 80 + "\n")
        f.write("📂 ESTRUCTURA DEL PROYECTO\n")
        f.write(f"📌 Directorio: {BASE_DIR}\n")
        f.write(f"📅 Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write("=" * 80 + "\n\n")
        
        # Generar estructura
        generar_estructura(BASE_DIR, max_nivel=4, archivo=f)
        
        # Generar resumen
        generar_resumen(BASE_DIR, f)
        
        # Footer
        f.write("\n" + "=" * 80 + "\n")
        f.write("✅ FIN DEL ANÁLISIS\n")
        f.write("=" * 80 + "\n")
    
    print(f"✅ Estructura guardada en: {ARCHIVO_SALIDA}")
    print(f"📂 Ubicación: {BASE_DIR / ARCHIVO_SALIDA}")

# ============================================
# EJECUTAR
# ============================================
if __name__ == '__main__':
    main()