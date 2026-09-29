# biblioartdis/openrouter_config.py

import os
import logging
from django.conf import settings
from openai import OpenAI

logger = logging.getLogger(__name__)

# --- CONFIGURACIÓN DE OPENROUTER ---
OPENROUTER_API_KEY = getattr(settings, 'OPENROUTER_API_KEY', os.getenv("OPENROUTER_API_KEY"))

if not OPENROUTER_API_KEY:
    logger.warning("OPENROUTER_API_KEY no configurada - El chatbot no funcionará")
    cliente = None
else:
    try:
        # OpenRouter es compatible con el SDK de OpenAI.
        cliente = OpenAI(
            base_url="https://openrouter.ai/api/v1",  # <-- URL de OpenRouter
            api_key=OPENROUTER_API_KEY
        )
        logger.info("✅ Cliente OpenRouter inicializado correctamente")
    except Exception as e:
        logger.error(f"❌ Error inicializando cliente OpenRouter: {str(e)}")
        cliente = None


def buscar_libros_en_bd(prompt):
    """
    Busca libros en la base de datos según la consulta del usuario.
    (Esta función se mantiene igual que en tus versiones anteriores)
    """
    from biblioartdis.models import Libro, Autor
    from django.db.models import Q
    
    prompt_lower = prompt.lower()
    palabras_clave = [
        p for p in prompt_lower.split()
        if len(p) > 2 and p not in ['para', 'por', 'con', 'sin', 'del', 'la', 'los', 'las', 'el', 'un', 'una', 'de', 'en', 'al']
    ]
    if not palabras_clave:
        return []
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
    Obtiene una respuesta de OpenRouter.
    Primero busca libros en la base de datos.
    Si no encuentra, usa la IA.
    """
    try:
        # 1. Buscar libros primero
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

        # 2. Si no hay libros, usar IA
        if not cliente:
            return "⚠️ El asistente IA no está configurado correctamente en este momento."

        system_prompt = (
            "Eres el asistente virtual de la Biblioteca ARTyDIS (Artes y Diseño). "
            "INFORMACIÓN: Especializada en arte, diseño, pintura, escultura, arquitectura, dibujo. "
            "REGLAS: Responde SIEMPRE en español, de forma amable y profesional. "
            "Sé conciso: máximo 3-4 oraciones por respuesta."
        )

        # Llamada al endpoint de OpenRouter.
        # Usamos el modelo "openrouter/free" que enruta automáticamente a un modelo gratuito.
        respuesta = cliente.chat.completions.create(
            model="openrouter/free",  # <-- Enrutador automático a modelos gratuitos
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=500,
        )
        
        # El campo 'model' en la respuesta te dice qué modelo gratuito se usó.
        logger.info(f"✅ OpenRouter respondió usando: {respuesta.model}")
        return respuesta.choices[0].message.content

    except Exception as e:
        logger.error(f"❌ Error en OpenRouter API: {str(e)}", exc_info=True)
        return "Lo siento, el asistente no está disponible en este momento. Intenta más tarde."