# biblioartdis/groq_config.py

import os
import logging
from django.conf import settings
from dotenv import load_dotenv

# Cargar variables .env
load_dotenv()

logger = logging.getLogger(__name__)

# Obtener API Key desde variables de entorno
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# Intentar también desde settings si no está en .env
if not GROQ_API_KEY and hasattr(settings, 'GROQ_API_KEY'):
    GROQ_API_KEY = settings.GROQ_API_KEY

# ✅ MODELOS VÁLIDOS DE GROQ (octubre 2024)
# Basado en: https://console.groq.com/docs/models
MODELOS_DISPONIBLES = [
    "llama-3.1-70b-versatile",  # Mejor calidad (recomendado)
    "llama-3.1-8b-instant",     # Rápido y eficiente
    "mixtral-8x7b-32768",       # Buen equilibrio
    "gemma2-9b-it",             # Modelo de Google
]

# Modelo por defecto
MODELO_POR_DEFECTO = "llama-3.1-70b-versatile"

# Validar existencia de API KEY
if not GROQ_API_KEY:
    logger.warning("GROQ_API_KEY no encontrada en variables de entorno - El chatbot no funcionará")
    cliente = None
else:
    try:
        from groq import Groq
        cliente = Groq(api_key=GROQ_API_KEY)
        logger.info("✅ Cliente Groq inicializado correctamente")
    except ImportError:
        logger.error("❌ No se pudo importar la librería 'groq'")
        cliente = None
    except Exception as e:
        logger.error(f"❌ Error inicializando cliente Groq: {str(e)}")
        cliente = None


def buscar_libros_en_bd(prompt):
    """
    Busca libros en la base de datos según la consulta del usuario.
    """
    from biblioartdis.models import Libro, Autor
    from django.db.models import Q
    
    prompt_lower = prompt.lower()

    # Extraer palabras clave (mínimo 3 caracteres)
    palabras_clave = [
        p for p in prompt_lower.split()
        if len(p) > 2 and p not in ['para', 'por', 'con', 'sin', 'del', 'la', 'los', 'las', 'el', 'un', 'una', 'de', 'en', 'al']
    ]

    if not palabras_clave:
        return []

    # Construir consulta dinámica
    q = Q()
    for palabra in palabras_clave:
        q |= Q(titulo__icontains=palabra)
        q |= Q(descripcion__icontains=palabra)
        q |= Q(palabra_clave__icontains=palabra)
        q |= Q(autores__nombre__icontains=palabra)
        q |= Q(categorias__nom_cat__icontains=palabra)

    libros = Libro.objects.filter(q).distinct()[:5]

    resultados = []
    for libro in libros:
        resultados.append({
            "titulo": libro.titulo,
            "autor": ", ".join([a.nombre for a in libro.autores.all()]) or "Autor no especificado",
            "descripcion": libro.descripcion[:150] if libro.descripcion else "Sin descripción",
            "tipo": libro.get_tipo_display(),
            "id": libro.id_libro,
            "categoria": libro.categoria if libro.categoria else "Sin categoría"
        })

    return resultados


def get_ai_response(prompt):
    """
    Obtiene una respuesta de Groq API.
    Primero busca libros en la base de datos.
    Si no encuentra, usa la IA con fallback de modelos.
    """
    try:
        # Buscar libros primero
        libros_encontrados = buscar_libros_en_bd(prompt)

        if libros_encontrados:
            respuesta = "📚 **Encontré estos libros en nuestra biblioteca:**\n\n"
            for libro in libros_encontrados:
                respuesta += f"• **{libro['titulo']}**\n"
                respuesta += f"  ✍️ Autor: {libro['autor']}\n"
                if libro["descripcion"] != "Sin descripción":
                    respuesta += f"  📝 {libro['descripcion']}...\n"
                respuesta += f"  🏷️ Tipo: {libro['tipo']}\n"
                respuesta += f"  📂 Categoría: {libro['categoria']}\n\n"
            
            if len(libros_encontrados) == 5:
                respuesta += "📌 *Hay más resultados disponibles. ¿Quieres que busque más específicamente?*"
            else:
                respuesta += "¿Te gustaría más detalles de algún libro en particular?"
            return respuesta

        # Validar cliente Groq
        if not cliente:
            return "⚠️ El asistente IA no está configurado correctamente en este momento."

        # Prompt del sistema mejorado
        system_prompt = (
            "Eres el asistente virtual de la Biblioteca ARTyDIS (Artes y Diseño). "
            "INFORMACIÓN SOBRE LA BIBLIOTECA: "
            "Especializada en arte, diseño, pintura, escultura, arquitectura, dibujo y publicaciones académicas. "
            "Cuenta con libros, revistas, artículos, tesis, monografías y material audiovisual. "
            "Los usuarios pueden sugerir libros para su adquisición. "
            "El catálogo está organizado por categorías y niveles (1-4). "
            "REGLAS DE RESPUESTA: "
            "Responde SIEMPRE en español, de forma amable y profesional. "
            "Sé conciso: máximo 3-4 oraciones por respuesta. "
            "Si preguntan por un libro específico, sugiere buscar por autor, título o tema. "
            "Si no sabes algo, sugiere contactar al bibliotecario o usar el buscador del sitio. "
            "Ofrece ayuda para buscar en el catálogo digital. "
            "No inventes libros que no existen en la biblioteca."
        )

        # Intentar con el modelo por defecto, si falla probar con otros
        ultimo_error = None
        
        for modelo in MODELOS_DISPONIBLES:
            try:
                respuesta = cliente.chat.completions.create(
                    model=modelo,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.7,
                    max_tokens=500,
                    top_p=0.9,
                )
                
                logger.info(f"✅ Groq respondió usando modelo: {modelo}")
                return respuesta.choices[0].message.content
                
            except Exception as e:
                logger.warning(f"⚠️ Modelo {modelo} falló: {str(e)}")
                ultimo_error = e
                continue
        
        # Si todos los modelos fallaron
        logger.error(f"❌ Todos los modelos fallaron. Último error: {ultimo_error}")
        return "Lo siento, el asistente no está disponible en este momento. Por favor intenta más tarde o usa el buscador de la biblioteca."

    except Exception as e:
        logger.error(f"❌ Error en Groq API: {str(e)}", exc_info=True)
        return "Lo siento, el asistente no está disponible en este momento. Intenta más tarde o contacta al bibliotecario."


def probar_conexion():
    """
    Prueba conexión con Groq API (útil para diagnóstico)
    """
    print("=" * 50)
    print("🔍 Probando conexión con Groq API...")
    print("=" * 50)

    if not GROQ_API_KEY:
        print("❌ ERROR: GROQ_API_KEY no está configurada")
        print("   Asegúrate de tener un archivo .env con:")
        print("   GROQ_API_KEY=tu_api_key_aqui")
        return None

    print("✅ API Key encontrada")
    print(f"📋 Probando modelos: {', '.join(MODELOS_DISPONIBLES)}")

    # Probar cada modelo disponible
    print("\n📋 Probando modelos disponibles:")
    for modelo in MODELOS_DISPONIBLES:
        try:
            respuesta = cliente.chat.completions.create(
                model=modelo,
                messages=[
                    {"role": "user", "content": "Responde solo con la palabra 'OK' para probar la conexion."}
                ],
                max_tokens=10,
            )
            print(f"   ✅ {modelo} - FUNCIONA")
        except Exception as e:
            error_msg = str(e)
            if "decommissioned" in error_msg:
                print(f"   ❌ {modelo} - DESCONTINUADO")
            elif "not found" in error_msg:
                print(f"   ❌ {modelo} - NO EXISTE")
            else:
                print(f"   ❌ {modelo} - Error: {error_msg[:60]}...")

    print("\n📝 Probando respuesta completa:")
    try:
        respuesta = get_ai_response("Hola, ¿cómo estás?")
        print("✅ Conexión exitosa!")
        print(f"Respuesta: {respuesta[:200]}..." if len(respuesta) > 200 else f"Respuesta: {respuesta}")
        return respuesta
    except Exception as e:
        print(f"❌ Error en la conexión: {e}")
        return None


# Ejecutar prueba si se llama directamente
if __name__ == "__main__":
    probar_conexion()