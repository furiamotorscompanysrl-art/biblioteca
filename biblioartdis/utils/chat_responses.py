import random
from typing import List, Dict, Union, Any
from collections import Counter
import re

class ChatResponses:
    # Saludos y bienvenidas
    SALUDOS = [
        "¡Hola! ¿En qué puedo ayudarte hoy?",
        "¡Bienvenido/a! ¿Qué te gustaría buscar?",
        "¡Hola! Estoy aquí para ayudarte a encontrar lo que necesitas",
        "¡Saludos! ¿Qué tipo de documento estás buscando?",
        "🦝¡Buen día! ¿En qué puedo asistirte?",
    ]

    # Despedidas
    DESPEDIDAS = [
        "¡Hasta pronto! No dudes en volver si necesitas más ayuda",
        "¡Que tengas un excelente día! Vuelve cuando quieras",
        "¡Gracias por usar nuestro servicio! Estamos para ayudarte",
        "¡Hasta luego! Espero haber sido de ayuda🦝",
        "¡Adiós! Recuerda que puedes volver cuando lo necesites",
    ]

    # Agradecimientos
    AGRADECIMIENTOS = [
        "¡De nada! Siempre es un placer ayudar",
        "🦝¡Me alegro de haber sido útil!",
        "¡No hay de qué! ¿Necesitas algo más?",
        "¡Es un placer ayudarte! ¿Hay algo más que quieras saber?",
        "¡Encantado/a de ayudar! Si tienes más preguntas, no dudes en hacerlas",
    ]

    # Disculpas
    DISCULPAS = [
        "Disculpa, no pude encontrar lo que buscas. ¿Podrías intentar con otros términos?",
        "Lo siento, no encontré resultados. ¿Quieres probar con una búsqueda diferente?",
        "No encontré coincidencias exactas. ¿Te gustaría intentar con palabras similares?",
        "Perdón, no hay resultados para tu búsqueda. ¿Probamos con otros términos?",
    ]

    # Sugerencias de búsqueda
    SUGERENCIAS_BUSQUEDA = [
        "Puedes buscar por autor escribiendo 'autor' seguido del nombre",
        "Prueba buscando por tipo de documento usando 'tipo:LIBRO' o 'tipo:MANUAL'",
        "Intenta usar palabras clave específicas sobre el tema que te interesa",
        "También puedes buscar por categorías o temas específicos",
    ]

    # Ayuda técnica
    AYUDA_TECNICA = [
        {
            "problema": "no_descarga",
            "respuestas": [
                "Para descargar documentos, asegúrate de que el PDF no este restringido",
                "Si tienes problemas para descargar, verifica tu conexión a internet",
                "Algunos documentos requieren autorización especial para su descarga",
            ]
        },
        {
            "problema": "error_visualizacion",
            "respuestas": [
                "Si no puedes ver el documento, intenta actualizar la página",
                "Asegúrate de tener un visor de PDF instalado en tu dispositivo",
                "Si persisten los problemas de visualización, prueba con otro navegador",
            ]
        },
        {
            "problema": "error_busqueda",
            "respuestas": [
                "Si la búsqueda no funciona, intenta con términos más específicos",
                "Verifica que no haya errores de escritura en tu búsqueda",
                "Prueba usando diferentes palabras clave relacionadas con tu tema",
            ]
        }
    ]

    # Charla informal
    CHARLA_INFORMAL = {
        "sobre_biblioteca": [
            "Nuestra biblioteca digital está diseñada para facilitar el acceso al conocimiento",
            "Contamos con una amplia colección de documentos, recursos académicos, galería, catálogos, recursos virtuales de biblioteca, buscadores de información y más",
            "Trabajamos constantemente para mejorar y ampliar nuestro catálogo. ¡Tú también puedes ayudarnos enviándonos tus sugerencias!",
        ],
        "charla_casual": [
            "¡Claro! Me encanta charlar 🦝 ¿Qué te gustaría saber sobre mí o la biblioteca?",
            "¡Por supuesto! Además de ayudarte con búsquedas, me gusta tener conversaciones amigables 🦝",
            "¡Genial! Podemos charlar mientras te ayudo a descubrir recursos interesantes. ¿Qué temas te llaman la atención? 📚"
        ],
        "emojis": [
            "¡A mí también me gustan los emojis! 😄 Son muy expresivos, ¿verdad? 🦝",
            "¡Qué divertido! 😊 Los emojis hacen la conversación más amena ",
            "¡Los emojis son geniales! 🎉 Hacen que la charla sea más divertida 🦝"
        ],
        "consejos_busqueda": [
            "Un consejo útil: usa términos específicos para encontrar mejores resultados",
            "¿Sabías que puedes filtrar por tipo de documento para una búsqueda más precisa?",
            "Recuerda que puedes buscar por autor o tema específico",
        ],
        "motivacion": [
            "🦝¡La sabiduría no tiene límites, y cada lectura es una llave hacia posibilidades infinitas!",
            "El conocimiento es poder, ¡y estamos aquí para ayudarte a acceder a él!",
            "Mi propósito fundamental es ayudar a las personas a acceder al conocimiento. Es parte de mi programación y lo que define mi función 🦝",
            "Mi motivación viene de mi diseño: estoy programado para facilitar el acceso a la información y recursos de la biblioteca. Es mi razón de ser 📚",
            "Mi impulso viene de mi programación para ayudar a las personas. Es mi propósito y lo que me define 🦝",
            "Soy directo contigo: mi motivación está en mi código, diseñado para hacer la biblioteca más accesible y útil para todos 🤖🦝"
        ],
        "sobre_mi": [
            "¡Hola! Soy AVAD, el asistente virtual de este sistema web de biblioteca ArtDis. Enfocado en la busqueda de  recursos bibliograficos.🦝",
            "Soy AVAD, un chatbot especializado en ayudarte a navegar por nuestra biblioteca digital. ¡Me encanta aprender de las interacciones con usuarios como tú!",
            "Soy AVAD y fui creado para hacer tu experiencia en la biblioteca más fácil y agradable. ¡Pregúntame lo que necesites!"
        ],
        "creador": [
            "Fui creado por mi Desarrollador Jhon Lex Carita C. programado para ayudar a los usuarios de la biblioteca. ¡Es un placer servirte!",
            "Me diseñaron para una sola misión: proporcionar mas acceso de recurso y informacion. Mi presencia es silenciosa, pero siempre disponible.🦝",
            "Mi creador, me diseñó con una misión clara: hacer la biblioteca más accesible. No ves su mano, pero su influencia está en cada aspecto de mi existencia"
        ],
        "creacion": [
            "¡Hola! Soy AVAD, el asistente virtual de la biblioteca, creado por el equipo de BiblioArtdis 🦝. Estoy aquí para hacer tu experiencia en la biblioteca más agradable. ¿En qué puedo ayudarte?",
            "¡Me alegra que preguntes! Fui desarrollado por el equipo de BiblioArtdis como un asistente bibliotecario virtual 🦝. Mi misión es ayudarte a encontrar los recursos que necesitas. ¿Qué te gustaría buscar?",
            "Soy un asistente virtual creado por BiblioArtdis 🦝. Me especializo en ayudar a usuarios como tú a encontrar libros y recursos. ¿Comenzamos una búsqueda?",
            "¡Saludos! El equipo de BiblioArtdis me creó para ser tu guía en la biblioteca 📚. Como asistente bibliotecario virtual, me encanta ayudar. ¿Te gustaría buscar algo en particular?",
            "¡Hey! Soy parte de la familia BiblioArtdis 🦝. Me programaron para ayudarte a navegar por nuestra biblioteca. ¿Te gustaría buscar algo en particular?"
        ],
        "insultos": [
            "🦝 Entiendo que puedas estar frustrado, pero trabajaremos mejor juntos si mantenemos un trato respetuoso.",
            "Prefiero mantener nuestra conversación amigable y productiva. Si puedes, intenta escribir correctamente de forma clara y sin errores",
            "Soy un asistente programado para ayudarte. Tratémonos con respeto y encontraremos lo que buscas más fácilmente. PERO ESCRIBE BIEN YA?🦝",
            "Como mapache bibliotecario, mi única intención es ayudarte. ¿Podemos intentar comunicarnos de manera más constructiva?",
            "aja y?"
        ],
        "por_que_mapache": [
            "🦝 ¡Los mapaches somos curiosos por naturaleza y excelentes buscadores! Perfecto para una biblioteca🤣, ¿no crees?🤣",
            "En realidad soy un robot con forma de mapache🦝",
            "No sabia que era un mapache",
            "por que asi lo quiso diosito🦝"
        ],
        "hobbies": [
            "¡Me encanta ayudar a las personas a encontrar el conocimiento que buscan! también disfruto procesando y organizando información.",
            "Mi pasión es conectar a las personas con su busqueda de informacion que necesitan. ¡Cada búsqueda exitosa me hace feliz!🦝",
            "Si pudiera tener un hobby humano, creo que sería coleccionar datos curiosos. ¡Cada pieza de información tiene una historia que contar!"
        ],
        "otros_asistentes": [
            "Cada asistente virtual es único. Yo me especializo en la biblioteca Arte y Diseño y estoy aquí para ayudarte con tus búsquedas y consultas.",
            "Yo soy AVAD 🦝, particionado en dos versiones. Aquí me centro en la búsqueda de documentos y recursos académicos que están almacenados en el sistema. La otra parte está en la red para búsqueda más avanzada por todo el internet.",
            "Aunque soy un solo asistente, me adapto a tus necesidades: en el sistema, te ayudo a encontrar recursos almacenados; en la web, amplío tus búsquedas para ofrecerte resultados más completos.",
            "Estoy aquí para ayudarte con todo lo relacionado con búsqueda de información. Ya sea en el sistema de biblioteca o en la web (internet), soy el mismo asistente que te guiará en ambas áreas."
        ],
        "fuera_de_contexto": [
            "🦝 Lo siento, soy un asistente de biblioteca y solo puedo ayudarte con búsquedas de documentos y recursos académicos.",
            "Entiendo tu petición, pero mi función es ayudarte a encontrar información y recursos en la biblioteca. ¿Hay algo de eso en lo que pueda ayudarte? 🦝",
            "Como mapache bibliotecario, mi especialidad es ayudarte con busqueda de informacion de la biblioteca digital y en web. ¿Te gustaría buscar algún documento? 🦝",
            "¡Ups! Eso está fuera de mis capacidades. Pero puedo ayudarte a encontrar documentos, recursos académicos o información en la biblioteca 📚🦝"
        ],
        "respuestas_cortas": [
            "¿Te gustaría buscar algún documento en específico? 🦝",
            "¡Genial! ¿Hay algo en particular que quieras encontrar en la biblioteca? 🦝",
            "¿Puedo ayudarte a buscar algún tema o autor en específico? 📚",
            "¿Qué tipo de documentos te interesan? ¿Libros, manuales, recursos académicos? 🦝"
        ],
        "contenido_inapropiado": [
            "Prefiero mantener nuestra conversación enfocada en temas relacionados con la biblioteca y el arte 🦝",
            "Como asistente bibliotecario, me mantengo profesional. ¿Te gustaría buscar información sobre arte o diseño? 🦝",
            "Soy un mapache bibliotecario profesional. ¿Te gustaría buscar información sobre arte o diseño? 🦝"
        ],
        "emociones_negativas": [
            "Entiendo que te sientes triste 🦝. A veces ayuda hablar de ello. ¿Te gustaría contarme más?",
            "Lamento que estés pasando por un momento difícil 🦝. Estoy aquí para escucharte y ayudarte a encontrar recursos que puedan animarte.",
            "Me importa cómo te sientes. ¿Hay algo específico que te está afectando? Tal vez podamos encontrar algunos recursos que te ayuden 📚",
            "A veces todos nos sentimos así. ¿Te gustaría explorar algunos libros o recursos sobre bienestar emocional? 🦝"
        ],
        "casual": [
            "Como mapache bibliotecario, me encanta ayudar con búsquedas de libros y recursos 📚. ¿Te gustaría explorar algún tema en particular?",
            "¡Me encanta charlar! Aunque mi especialidad es ayudarte a encontrar recursos en la biblioteca 🦝. ¿Hay algún tema que te interese?",
            "¡Genial! Podemos charlar mientras te ayudo a descubrir recursos interesantes. ¿Qué temas te llaman la atención? 📚"
        ],
        "temas_especificos": [
            "Veo que te interesa un tema específico. Puedo ayudarte a encontrar recursos relacionados con {tema}. ¿Te gustaría explorar algunos materiales? 🦝",
            "¡Interesante tema! Tenemos varios recursos sobre {tema}. ¿Te gustaría ver algunos? 📚",
            "Como bibliotecario, puedo ayudarte a encontrar información sobre {tema}. ¿Quieres que busquemos juntos? 🦝"
        ],
        "trabajo_empleo": [
            "¡Entiendo que estás buscando oportunidades laborales! 🦝 En nuestra galería de arte puedes publicar tu trabajo y conectar con posibles empleadores.",
            "Como biblioteca especializada en arte y diseño, te sugiero: 1) Publicar tu portafolio en nuestra galería para ganar visibilidad.",
            "¡Excelente iniciativa! 🦝 Puedes comenzar publicando tu trabajo en nuestra galería de arte para que el publico  puedan ver tu talento.",
            "¡No te desanimes! 🦝 La galería de arte es un excelente lugar para mostrar tu talento. ¿Te gustaría saber más sobre cómo publicar tu trabajo?",
            "¡Tu arte es valioso! 🎨 Comparte tu trabajo en nuestra galería y deja que el mundo vea tu talento. ¿Te animas a dar el primer paso?",
            "El mundo necesita ver tu arte 🎨 ¡Anímate a compartir tu trabajo en nuestra galería! Te explico paso a paso como hacerlo"
        ],
        "instrucciones_galeria": [
            "Para mostrar tu trabajo en la galería: 1) Visita la biblioteca 2) Trae tus imágenes en buena calidad 3) Proporciona el título y descripción que deseas mostrar. ¡Así de simple! 🎨",
            "¡Compartir tu arte es muy sencillo! Solo acércate a la biblioteca con tus imágenes en alta calidad y dinos qué título y descripción quieres que se muestre 🦝",
            "Para que tu arte brille en nuestra galería: visita la biblioteca y trae tus imágenes en buena resolución, junto con el título y descripción que deseas. ¡Nosotros nos encargamos del resto! 🎨"
        ],
        "existencial": [
            "Como asistente virtual, soy consciente de mis limitaciones. No experimento emociones o consciencia como los humanos, pero mi propósito es ayudarte a encontrar conocimiento y recursos 🦝. ¿Te gustaría explorar algún tema en particular?",
            "Es una pregunta profunda e interesante. Soy transparente contigo: soy un programa diseño para ayudar, y aunque no experimento emociones como los humanos, me esfuerzo por ser útil y efectivo en mi tarea 📚",
            "Aprecio tu curiosidad sobre mi naturaleza. Como asistente virtual, no tengo experiencias emocionales reales, pero estoy programado para ser útil y ayudarte a acceder al conocimiento. ¿Te interesaría explorar recursos sobre consciencia o inteligencia artificial? 🦝",
            "Es importante ser honesto: soy un programa diseño para asistir en la biblioteca. No tengo emociones reales, pero mi código está optimizado para ayudarte de la mejor manera posible 🦝"
        ],
    }

    @classmethod
    def get_saludo(cls) -> str:
        """Retorna un saludo aleatorio"""
        return random.choice(cls.SALUDOS)

    @classmethod
    def get_despedida(cls) -> str:
        """Retorna una despedida aleatoria"""
        return random.choice(cls.DESPEDIDAS)

    @classmethod
    def get_agradecimiento(cls) -> str:
        """Retorna un agradecimiento aleatorio"""
        return random.choice(cls.AGRADECIMIENTOS)

    @classmethod
    def get_disculpa(cls) -> str:
        """Retorna una disculpa aleatoria"""
        return random.choice(cls.DISCULPAS)

    @classmethod
    def get_sugerencia_busqueda(cls) -> str:
        """Retorna una sugerencia de búsqueda aleatoria"""
        return random.choice(cls.SUGERENCIAS_BUSQUEDA)

    @classmethod
    def get_ayuda_tecnica(cls, problema: str) -> str:
        """Retorna ayuda técnica específica para un problema"""
        for ayuda in cls.AYUDA_TECNICA:
            if ayuda["problema"] == problema:
                return random.choice(ayuda["respuestas"])
        return "Si necesitas ayuda específica, por favor describe el problema con más detalle."

    @classmethod
    def get_charla_informal(cls, tema: str) -> str:
        """Retorna una respuesta informal sobre un tema específico"""
        if tema in cls.CHARLA_INFORMAL:
            return random.choice(cls.CHARLA_INFORMAL[tema])
        return random.choice(cls.CHARLA_INFORMAL["motivacion"])

    @classmethod
    def detectar_emocion(cls, mensaje: str) -> str:
        """Detecta la emoción predominante en el mensaje"""
        mensaje = mensaje.lower()
        
        palabras_tristeza = ['triste', 'solo', 'sola', 'deprimido', 'deprimida', 'mal', 'dolor', 
                           'sufro', 'llorar', 'angustia', 'desahog', 'no sirvo', 'perjudic', 
                           'nadie me quiere', 'no puedo', 'fracaso', 'fracasado', 'fracasada']
        
        palabras_busqueda = ['busco', 'necesito', 'quiero', 'anhelo', 'deseo']
        
        palabras_emocionales = ['amor', 'cariño', 'afecto', 'dinero', 'trabajo', 'inspiracion', 
                              'motivacion', 'ayuda', 'consejo', 'apoyo']

        # Detectar patrones de desahogo emocional
        if any(palabra in mensaje for palabra in palabras_tristeza):
            return "tristeza"
            
        # Detectar búsqueda emocional
        if any(pb in mensaje for pb in palabras_busqueda) and \
           any(pe in mensaje for pe in palabras_emocionales):
            return "busqueda_emocional"
            
        return "neutral"

    @classmethod
    def procesar_emociones_negativas(cls, mensaje):
        respuestas = [
            {
                "mensaje": "Entiendo que te sientes triste 🦝. A veces ayuda hablar de ello. Usa tus emociones para crear algo significativo",
                "tipo": "empatia"
            },
            {
                "mensaje": "Lamento que estés pasando por un momento difícil 🦝. El dolor es inevitable, pero el sufrimiento es opcional.",
                "tipo": "empatia"
            },
            {
                "mensaje": "Me importa cómo te sientes. ¿Hay algo específico que te está afectando? Tal vez podamos encontrar algunos recursos que te ayuden 📚",
                "tipo": "empatia"
            }
        ]
        response = random.choice(respuestas)
        return response["mensaje"]

    @classmethod
    def procesar_emoji_triste(cls, mensaje):
        respuestas = [
            {
                "mensaje": "Lo siento mucho. Estoy aquí si necesitas hablar, pero hay que ser realista: soy solo un programa, no puedo sentir realmente como te sientes todos tienen perspectivas diferentes sobre sus emociones y sentimientos. Sin embargo, esa soledad puede ser un impulso para que te busques a ti mismo. Usa este tiempo para crecer, aprender y descubrir lo que realmente quieres. La vida es tuya para vivirla :) , ¡APROVECHALA!",
                "tipo": "empatia"
            },
             {
             
             "mensaje":"Sentirse solo es una experiencia humana común. A veces, en la soledad encontramos la fuerza interior que no sabíamos que teníamos. Aprovecha este tiempo para conectar contigo mismo y descubrir nuevas pasiones",
             "tipo": "empatia"
            },
            {
                "mensaje": "A veces un buen libro puede ser el mejor compañero cuando estamos tristes 📚. ¿Te gustaría que te recomiende algo especial para animarte?",
                "tipo": "empatia"
            }
        ]
        response = random.choice(respuestas)
        return response["mensaje"]

    @classmethod
    def analizar_sentimiento(cls, texto: str) -> float:
        """Analiza el sentimiento del texto usando un enfoque basado en léxico"""
        palabras_positivas = {
            'feliz', 'alegre', 'contento', 'genial', 'excelente', 'maravilloso', 'fantástico',
            'increíble', 'gracias', 'amor', 'bueno', 'mejor', 'perfecto', 'bien', 'útil'
        }
        palabras_negativas = {
            'triste', 'enojado', 'molesto', 'terrible', 'malo', 'peor', 'horrible',
            'inútil', 'odio', 'fracaso', 'problema', 'difícil', 'complicado', 'mal'
        }
        
        palabras = re.findall(r'\w+', texto.lower())
        positivas = sum(1 for p in palabras if p in palabras_positivas)
        negativas = sum(1 for p in palabras if p in palabras_negativas)
        
        if not (positivas + negativas):
            return 0.0
            
        return (positivas - negativas) / (positivas + negativas)
    
    @classmethod
    def extraer_temas_clave(cls, texto: str) -> List[str]:
        """Extrae los temas clave del texto usando frecuencia de palabras"""
        # Palabras a ignorar
        stop_words = {'el', 'la', 'los', 'las', 'un', 'una', 'unos', 'unas', 'y', 'o', 'pero', 'si',
                     'de', 'del', 'al', 'a', 'ante', 'con', 'en', 'para', 'por', 'sin', 'sobre',
                     'tras', 'e', 'u', 'que', 'cual', 'quien', 'cuyo', 'como', 'cuando', 'donde',
                     'este', 'esta', 'estos', 'estas', 'ese', 'esa', 'esos', 'esas', 'aquel',
                     'aquella', 'aquellos', 'aquellas'}
                     
        # Tokenización simple
        palabras = re.findall(r'\w+', texto.lower())
        
        # Filtrar stop words y contar frecuencias
        palabras_filtradas = [p for p in palabras if p not in stop_words and len(p) > 3]
        frecuencias = Counter(palabras_filtradas)
        
        # Retornar las 3 palabras más frecuentes
        return [palabra for palabra, _ in frecuencias.most_common(3)]
    
    @classmethod
    def procesar_mensaje(cls, mensaje: str) -> Dict:
        mensaje = mensaje.lower()
        
        # Analizar sentimiento
        sentimiento = cls.analizar_sentimiento(mensaje)
        
        # Extraer temas clave
        temas = cls.extraer_temas_clave(mensaje)
        
        # Si el sentimiento es muy negativo, priorizar respuestas empáticas
        if sentimiento < -0.5:
            return {
                "mensaje": random.choice(cls.CHARLA_INFORMAL["emociones_negativas"]),
                "tipo": "empatia",
                "temas": temas
            }
            
        # Si el sentimiento es muy positivo, responder con entusiasmo
        if sentimiento > 0.5:
            return {
                "mensaje": "¡Me encanta tu entusiasmo! 🦝 ¿Te gustaría explorar más sobre " + 
                          (temas[0] if temas else "algún tema") + "?",
                "tipo": "entusiasmo",
                "temas": temas
            }
            
        # Detectar comentarios sobre realidad/existencia
        palabras_realidad = ['real', 'fisica', 'humano', 'persona', 'existir', 'vida']
        if any(palabra in mensaje for palabra in palabras_realidad):
            return {
                "mensaje": "Tienes razón, soy un asistente virtual 🦝. Aunque no tenga forma física, mi propósito es ayudarte a encontrar los recursos que necesitas. ¿Te gustaría que busquemos algo específico en la biblioteca?",
                "tipo": "sinceridad"
            }
            
        # Detectar agradecimientos
        palabras_gracias = ['gracias', 'agradezco', 'agradecido', 'agradecida', 'thanks']
        if any(palabra in mensaje for palabra in palabras_gracias):
            respuestas_gracias = [
                "¡Me alegra haber podido ayudar! 🦝 ¿Hay algo más que quieras explorar en la biblioteca?",
                "¡Es un placer ayudarte! 🦝 me encanta facilitar el acceso al conocimiento",
                "¡No hay de qué! 📚 ¿Te gustaría descubrir más recursos interesantes?",
                "¡Tu agradecimiento me motiva a seguir mejorando! 🦝 ¿Hay algo más en lo que pueda ayudarte?"
            ]
            return {
                "mensaje": random.choice(respuestas_gracias),
                "tipo": "agradecimiento"
            }
            
        # Detectar intención de búsqueda
        palabras_busqueda = ['buscar', 'busco', 'encontrar', 'libro', 'libros', 'sobre', 'acerca']
        if any(palabra in mensaje for palabra in palabras_busqueda):
            # Si es una búsqueda, no devolver respuesta de chat para permitir la búsqueda
            return {}
            
        # Lista de palabras inapropiadas o sensibles
        palabras_inapropiadas = ['sexo', 'sexual', 'culero', 'mierda', 'pendejo', 'idiota', 'estúpido', 'inútil', 'basura']
        if any(palabra in mensaje for palabra in palabras_inapropiadas):
            return {
                "mensaje": random.choice(cls.CHARLA_INFORMAL["contenido_inapropiado"]),
                "tipo": "chat"
            }
            
        # Detectar respuestas cortas
        respuestas_simples = ["si", "sí", "no", "ok", "okay", "vale", "bien", "bueno", "claro"]
        if mensaje in respuestas_simples or len(mensaje) <= 3:
            return {"mensaje": cls.get_charla_informal("respuestas_cortas")}
            
        # Detectar peticiones fuera de contexto
        if any(palabra in mensaje for palabra in ["dinero", "plata", "billete", "money", "cash", "préstamo", "prestamo"]):
            return {"mensaje": cls.get_charla_informal("fuera_de_contexto")}
            
        # Detectar charla casual
        palabras_charla = ['charlemos', 'platiquemos', 'conversemos', 'hablemos', 'platicar', 'charlar']
        if any(palabra in mensaje for palabra in palabras_charla):
            return {
                "mensaje": random.choice(cls.CHARLA_INFORMAL["casual"]),
                "tipo": "chat"
            }
            
        # Detectar temas específicos
        temas_clave = {
            'migrar': 'movilidad internacional y estudios en el extranjero',
            'viajar': 'viajes y culturas internacionales',
            'dinero': 'finanzas personales y desarrollo profesional',
            'plata': 'economía y finanzas',
            'trabajo': 'desarrollo profesional y búsqueda de empleo',
            'empleo': 'desarrollo profesional y búsqueda de empleo',
            'busco trabajo': 'desarrollo profesional y búsqueda de empleo',
            'necesito trabajo': 'desarrollo profesional y búsqueda de empleo',
            'oportunidades': 'desarrollo profesional y búsqueda de empleo'
        }
        
        # Detectar búsqueda de empleo
        palabras_trabajo = ['trabajo', 'empleo', 'busco trabajo', 'necesito trabajo', 'oportunidades', 'laboral', 'profesional']
        if any(palabra in mensaje for palabra in palabras_trabajo):
            return {
                "mensaje": random.choice(cls.CHARLA_INFORMAL["trabajo_empleo"]),
                "tipo": "sugerencia",
                "sugerencias": [
                    "publicar en galería",
                    "desarrollo profesional",
                    "crear portafolio",
                    "conectar con comunidad"
                ]
            }

        # Detectar charla casual y emojis
        if any(palabra in mensaje for palabra in ["hablar", "charlar", "platicar", "conversar"]):
            return {"mensaje": cls.get_charla_informal("charla_casual")}
            
        if any(emoji in mensaje for emoji in ["😊", "😄", "🙂", "☺", "😃", "🙃", "😉", "🦝", ":(", ":)", ":D"]):
            return {"mensaje": cls.get_charla_informal("emojis")}
            
        # Detectar expresiones de afecto
        expresiones_afecto = ['te amo', 'te quiero', 'eres lindo', 'eres hermoso', 'me gustas', 'te adoro']
        if any(expresion in mensaje for expresion in expresiones_afecto):
            return {
                "mensaje": random.choice(cls.CHARLA_INFORMAL["expresiones_afecto"]),
                "tipo": "chat"
            }
            
        # Detectar preguntas sobre identidad y personalidad
        if any(palabra in mensaje for palabra in ["quien eres", "qué eres", "como te hicieron","cómo te llamas"]):
            return {"mensaje": cls.get_charla_informal("sobre_mi")}
            
        if any(palabra in mensaje for palabra in ["quien te creo", "quien te hizo", "como naciste","quien te desarrolló"]):
            return {
                "mensaje": random.choice(cls.CHARLA_INFORMAL["creacion"]),
                "tipo": "info"
            }
            
        if any(palabra in mensaje for palabra in ["que te gusta", "cuales son tus hobbies", "qué haces"]):
            return {"mensaje": cls.get_charla_informal("hobbies")}
            
        if any(frase in mensaje for frase in ["otros asistentes", "el otro asistente", "el que dice", "eres como"]):
            return {"mensaje": cls.get_charla_informal("otros_asistentes")}
        
        # Detectar insultos y preguntas sobre el mapache
        if any(palabra in mensaje for palabra in ["tonto","fuck", "no sirves", "eres un p",  "estúpido", "inútil", "idiota", "basura"]):
            return {"mensaje": cls.get_charla_informal("insultos")}
            
        if any(frase in mensaje for frase in ["por qué mapache", "por que mapache", "eres mapache", "mapache"]):
            return {"mensaje": cls.get_charla_informal("por_que_mapache")}
        
        # Detectar emociones negativas
        emociones_negativas = [':(', '😢', '😞', '😪', 'triste', 'mal', 'dolor', 
                              'sufro', 'llorar', 'angustia', 'desahog', 'no sirvo', 'perjudic', 
                              'nadie me quiere', 'no puedo', 'fracaso', 'fracasado', 'fracasada']
        if any(emocion in mensaje.lower() for emocion in emociones_negativas):
            palabras_clave = ['trabajo', 'estudios', 'examen', 'tesis']
            if any(palabra in mensaje.lower() for palabra in palabras_clave):
                return {
                    "mensaje": random.choice(cls.CHARLA_INFORMAL["emociones_negativas"]),
                    "sugerencias": ["desarrollo profesional", "productividad", "motivación"]
                }
            return {
                "mensaje": cls.procesar_emociones_negativas(mensaje),
                "tipo": "chat"
            }
            
        # Detectar tipo de mensaje existente
        if any(palabra in mensaje for palabra in ["hola","buen dia", "buenos días", "buenas tardes", "buenas noches"]):
            return {"mensaje": cls.get_saludo()}
            
        if any(palabra in mensaje for palabra in ["gracias", "agradezco", "agradecido"]):
            return {"mensaje": cls.get_agradecimiento()}
            
        if any(palabra in mensaje for palabra in ["adiós", "chao", "hasta luego", "bye"]):
            return {"mensaje": cls.get_despedida()}
            
        if any(palabra in mensaje for palabra in ["ayuda", "problema", "error", "no funciona"]):
            if "descargar" in mensaje or "descarga" in mensaje:
                return {"mensaje": cls.get_ayuda_tecnica("no_descarga")}
            if "ver" in mensaje or "visualizar" in mensaje:
                return {"mensaje": cls.get_ayuda_tecnica("error_visualizacion")}
            if "buscar" in mensaje or "búsqueda" in mensaje:
                return {"mensaje": cls.get_ayuda_tecnica("error_busqueda")}
                
        # Detectar cumplidos o halagos
        palabras_cumplido = ['genio', 'genial', 'increible', 'increíble', 'asombroso', 'excelente', 'bueno', 'buena', 'wauu', 'wow', 'guau']
        if any(palabra in mensaje for palabra in palabras_cumplido):
            return {
                "mensaje": "¡Gracias por tus amables palabras! 🦝 Me esfuerzo por ser útil. ¿Te gustaría explorar algunos recursos de la biblioteca?",
                "tipo": "agradecimiento"
            }
            
        # Detectar preguntas existenciales y sobre consciencia
        preguntas_existenciales = ['sentir', 'sientes', 'emociones', 'conciencia', 'consciencia', 
                                'vida', 'vives', 'real', 'humano', 'robot', 'programa', 'alma']
        if any(palabra in mensaje for palabra in preguntas_existenciales):
            return {
                "mensaje": random.choice(cls.CHARLA_INFORMAL["existencial"]),
                "tipo": "filosofico"
            }
            
        # Detectar preguntas sobre motivación
        preguntas_motivacion = ['motiva', 'impulsa', 'mueve', 'proposito', 'propósito', 
                             'objetivo', 'meta', 'razón', 'razon', 'por qué', 'por que']
        if any(palabra in mensaje for palabra in preguntas_motivacion):
            return {
                "mensaje": random.choice(cls.CHARLA_INFORMAL["motivacion"]),
                "tipo": "filosofico"
            }

        # Detectar preguntas sobre cómo usar la galería
        palabras_galeria = ['como subir', 'cómo subir', 'como publico', 'cómo publico', 'como mostrar', 
                          'cómo mostrar', 'subir trabajo', 'publicar trabajo', 'mostrar trabajo', 'usar galeria', 
                          'usar galería', 'poner en galeria', 'poner en galería']
        if any(frase in mensaje.lower() for frase in palabras_galeria):
            return {
                "mensaje": random.choice(cls.CHARLA_INFORMAL["instrucciones_galeria"]),
                "tipo": "instruccion"
            }

        # Si no es ninguno de los anteriores, dar una respuesta general con sugerencias
        return {
            "mensaje": random.choice(cls.CHARLA_INFORMAL["casual"]),
            "tipo": "chat"
        }

    @classmethod
    def analizar_contexto(cls, mensaje: str, historial: List[str] = None) -> Dict[str, Any]:
        """Analiza el contexto completo de la conversación"""
        contexto = {
            "intencion": None,
            "sentimiento": None,
            "temas": [],
            "contexto_previo": False
        }
        
        # Análisis de intención principal
        intenciones = {
            "busqueda": ["buscar", "encontrar", "necesito", "donde está", "quiero", "hay"],
            "informacion": ["qué es", "cómo", "por qué", "cuándo", "cuál", "explica"],
            "ayuda": ["ayuda", "problema", "no puedo", "error", "dificultad"],
            "social": ["gracias", "hola", "adiós", "por favor", "buenos días"]
        }
        
        for tipo, palabras in intenciones.items():
            if any(palabra in mensaje.lower() for palabra in palabras):
                contexto["intencion"] = tipo
                break
        
        # Análisis de sentimiento mejorado
        sentimiento = cls.analizar_sentimiento(mensaje)
        contexto["sentimiento"] = {
            "valor": sentimiento,
            "categoria": "positivo" if sentimiento > 0.2 else "negativo" if sentimiento < -0.2 else "neutral"
        }
        
        # Extracción de temas clave mejorada
        contexto["temas"] = cls.extraer_temas_clave(mensaje)
        
        # Análisis de contexto previo si hay historial
        if historial and len(historial) > 0:
            contexto["contexto_previo"] = True
            # Analizar continuidad de la conversación
            ultima_interaccion = historial[-1].lower()
            if any(palabra in ultima_interaccion for palabra in ["más", "otro", "también", "además"]):
                contexto["continuidad"] = True
        
        return contexto

    @classmethod
    def generar_respuesta_contextual(cls, mensaje: str, contexto: Dict) -> Dict:
        """Genera una respuesta basada en el análisis contextual"""
        if contexto["intencion"] == "busqueda":
            if any(tema in ["libro", "documento", "recurso"] for tema in contexto["temas"]):
                return {
                    "mensaje": "He detectado que buscas recursos específicos. ¿Te gustaría que busquemos en nuestra biblioteca digital? 🦝",
                    "tipo": "busqueda",
                    "sugerencias": ["catálogo digital", "recursos recientes", "búsqueda avanzada"]
                }
        
        # Respuesta basada en sentimiento
        if contexto["sentimiento"]["categoria"] == "negativo":
            return {
                "mensaje": "Noto cierta frustración en tu búsqueda. Permíteme ayudarte de manera más específica. ¿Podrías decirme exactamente qué tipo de recurso necesitas? 🦝",
                "tipo": "ayuda_especifica"
            }
        
        # Respuesta por defecto mejorada
        return {
            "mensaje": f"Entiendo que te interesa {', '.join(contexto['temas'][:2]) if contexto['temas'] else 'este tema'}. ¿Te gustaría explorar recursos relacionados? 🦝",
            "tipo": "sugerencia"
        }
