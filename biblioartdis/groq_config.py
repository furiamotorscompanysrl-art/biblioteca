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

# Validar existencia de API KEY
if not GROQ_API_KEY:
    logger.warning("GROQ_API_KEY no encontrada en variables de entorno - El chatbot no funcionará")
    cliente = None
else:
    try:
        from groq import Groq
        cliente = Groq(api_key=GROQ_API_KEY)
        logger.info("Cliente Groq inicializado correctamente")
    except ImportError:
        logger.error("No se pudo importar la librería 'groq'")
        cliente = None
    except Exception as e:
        logger.error(f"Error inicializando cliente Groq: {str(e)}")
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
        if len(p) > 2 and p not in ['para', 'por', 'con', 'sin', 'del', 'la', 'los', 'las', 'el', 'un', 'una']
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

    libros = Libro.objects.filter(q).distinct()[:5]

    resultados = []
    for libro in libros:
        resultados.append({
            "titulo": libro.titulo,
            "autor": ", ".join([a.nombre for a in libro.autores.all()]) or "Autor no especificado",
            "descripcion": libro.descripcion[:150] if libro.descripcion else "Sin descripción",
            "tipo": libro.get_tipo_display(),
            "id": libro.id_libro
        })

    return resultados


def get_ai_response(prompt):
    """
    Obtiene una respuesta de Groq API.
    Primero busca libros en la base de datos.
    """
    try:
        # Buscar libros primero
        libros_encontrados = buscar_libros_en_bd(prompt)

        if libros_encontrados:
            respuesta = "📚 Encontré estos libros en nuestra biblioteca:\n\n"
            for libro in libros_encontrados:
                respuesta += f"• **{libro['titulo']}**\n"
                respuesta += f"  ✍️ Autor: {libro['autor']}\n"
                if libro["descripcion"] != "Sin descripción":
                    respuesta += f"  📝 {libro['descripcion']}...\n"
                respuesta += f"  🏷️ Tipo: {libro['tipo']}\n\n"
            respuesta += "¿Te gustaría más detalles de algún libro?"
            return respuesta

        # Validar cliente Groq
        if not cliente:
            return "⚠️ El asistente IA no está configurado correctamente en este momento."

        # Prompt del sistema mejorado
        system_prompt = """Eres un asistente virtual de una biblioteca digital llamada Biblioteca ARTyDIS (Artes y Diseño).

Características:
- Especializado en arte, diseño, y publicaciones académicas
- Responde en español, de forma amable y concisa
- Máximo 3-4 oraciones por respuesta
- Si no sabes algo, sugiere contactar al bibliotecario

Si el usuario pregunta por un libro que no existe en la base de datos:
- Sugiere palabras clave alternativas (autor, tema, año)
- Recomienda temas similares disponibles
- Ofrece ayuda para buscar en el catálogo"""

        # Llamar a la API
        respuesta = cliente.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=500,
        )

        return respuesta.choices[0].message.content

    except Exception as e:
        logger.error(f"Error en Groq API: {str(e)}", exc_info=True)
        return "Lo siento, el asistente no está disponible en este momento. Intenta más tarde o contacta al bibliotecario."


def probar_conexion():
    """
    Prueba conexión con Groq API (útil para diagnóstico)
    """
    print("=" * 50)
    print("Probando conexión con Groq API...")
    print("=" * 50)

    if not GROQ_API_KEY:
        print("❌ ERROR: GROQ_API_KEY no está configurada")
        print("   Asegúrate de tener un archivo .env con:")
        print("   GROQ_API_KEY=tu_api_key_aqui")
        return None

    print("✅ API Key encontrada")

    try:
        respuesta = get_ai_response("Hola, ¿cómo estás?")
        print("✅ Conexión exitosa!")
        print(f"Respuesta: {respuesta[:200]}...")
        return respuesta
    except Exception as e:
        print(f"❌ Error en la conexión: {e}")
        return None


# Ejecutar prueba si se llama directamente
if __name__ == "__main__":
    probar_conexion()