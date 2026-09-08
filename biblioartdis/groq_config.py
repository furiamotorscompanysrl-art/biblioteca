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
        logger.info("✅ Cliente Groq inicializado correctamente")
    except ImportError:
        logger.error("❌ No se pudo importar la librería 'groq'")
        cliente = None
    except Exception as e:
        logger.error(f"❌ Error inicializando cliente Groq: {str(e)}")
        cliente = None


def listar_modelos_disponibles():
    """
    Lista los modelos disponibles en Groq para tu API Key.
    Útil para diagnosticar qué modelos funcionan.
    """
    if not cliente:
        return "Cliente no inicializado"
    
    try:
        modelos = cliente.models.list()
        disponibles = []
        for modelo in modelos.data:
            disponibles.append(modelo.id)
        return disponibles
    except Exception as e:
        return f"Error al listar modelos: {e}"


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

        # Prompt del sistema
        system_prompt = (
            "Eres el asistente virtual de la Biblioteca ARTyDIS (Artes y Diseño). "
            "INFORMACIÓN SOBRE LA BIBLIOTECA: "
            "Especializada en arte, diseño, pintura, escultura, arquitectura, dibujo y publicaciones académicas. "
            "REGLAS DE RESPUESTA: "
            "Responde SIEMPRE en español, de forma amable y profesional. "
            "Sé conciso: máximo 3-4 oraciones por respuesta."
        )

        # 🔥 PRIMERO: Intentar obtener la lista de modelos disponibles
        try:
            modelos_disponibles = cliente.models.list()
            modelos_ids = [m.id for m in modelos_disponibles.data]
            logger.info(f"📋 Modelos disponibles en tu cuenta: {modelos_ids}")
            
            # Usar el primer modelo disponible
            modelo_a_usar = modelos_ids[0] if modelos_ids else None
            
            if modelo_a_usar:
                logger.info(f"✅ Usando modelo: {modelo_a_usar}")
                respuesta = cliente.chat.completions.create(
                    model=modelo_a_usar,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.7,
                    max_tokens=500,
                )
                return respuesta.choices[0].message.content
        except Exception as e:
            logger.warning(f"⚠️ No se pudo listar modelos: {e}")

        # 🔥 SEGUNDO: Intentar con modelos comunes (uno por uno)
        modelos_a_probar = [
            "llama3-70b-8192",
            "llama3-8b-8192", 
            "mixtral-8x7b-32768",
            "gemma-7b-it",
        ]
        
        for modelo in modelos_a_probar:
            try:
                respuesta = cliente.chat.completions.create(
                    model=modelo,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.7,
                    max_tokens=500,
                )
                logger.info(f"✅ Groq respondió usando modelo: {modelo}")
                return respuesta.choices[0].message.content
            except Exception as e:
                logger.warning(f"⚠️ Modelo {modelo} falló: {str(e)}")
                continue

        return "Lo siento, el asistente no está disponible en este momento. Por favor intenta más tarde o usa el buscador de la biblioteca."

    except Exception as e:
        logger.error(f"❌ Error en Groq API: {str(e)}", exc_info=True)
        return "Lo siento, el asistente no está disponible en este momento. Intenta más tarde o contacta al bibliotecario."


def probar_conexion():
    """
    Prueba conexión con Groq API (útil para diagnóstico)
    """
    print("=" * 60)
    print("🔍 Probando conexión con Groq API...")
    print("=" * 60)

    if not GROQ_API_KEY:
        print("❌ ERROR: GROQ_API_KEY no está configurada")
        print("   Asegúrate de tener un archivo .env con:")
        print("   GROQ_API_KEY=tu_api_key_aqui")
        return None

    print("✅ API Key encontrada")

    if not cliente:
        print("❌ Cliente no inicializado")
        return None

    print("\n📋 Listando modelos disponibles en tu cuenta:")
    try:
        modelos = cliente.models.list()
        for modelo in modelos.data:
            print(f"   ✅ {modelo.id}")
    except Exception as e:
        print(f"   ❌ Error al listar modelos: {e}")

    print("\n📝 Probando respuesta con el primer modelo disponible:")
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