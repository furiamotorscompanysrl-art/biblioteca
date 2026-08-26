// Función para agregar mensaje del usuario
function addUserMessage(message) {
    const chatBox = document.getElementById('chat-box');
    const userDiv = document.createElement('div');
    userDiv.className = 'user-message';
    userDiv.innerHTML = `<strong>Tú:</strong> ${message}`;
    chatBox.appendChild(userDiv);
    chatBox.scrollTop = chatBox.scrollHeight;
}

// Función para agregar mensaje del bot
window.addBotMessage = function(message) {
    const chatBox = document.getElementById('chat-box');
    const botDiv = document.createElement('div');
    botDiv.className = 'bot-message';
    if (typeof message === 'string') {
        botDiv.innerHTML = `<strong>Asistente:</strong> ${message}`;
    } else if (message.mensaje) {
        let content = `<strong>Asistente:</strong> ${message.mensaje}<br>`;
        
        // Mostrar categorías y tipos si están disponibles
        if (message.categorias) {
            content += '<div class="mt-2"><strong>Categorías disponibles:</strong><ul>';
            message.categorias.forEach(cat => {
                content += `<li>${cat}</li>`;
            });
            content += '</ul></div>';
        }
        
        if (message.tipos) {
            content += '<div class="mt-2"><strong>Tipos de libros:</strong><ul>';
            message.tipos.forEach(tipo => {
                content += `<li>${tipo}</li>`;
            });
            content += '</ul></div>';
        }
        
        // Mostrar sugerencias de búsqueda si es un array
        if (Array.isArray(message.sugerencias)) {
            content += '<div class="mt-2"><strong>Ejemplos de búsqueda:</strong><ul>';
            message.sugerencias.forEach(sug => {
                content += `<li>${sug}</li>`;
            });
            content += '</ul></div>';
        }
        
        botDiv.innerHTML = content;
    } else if (Array.isArray(message)) {
        let content = '';
        message.forEach(item => {
            if (item.mensaje) {
                content += `<strong>Asistente:</strong> ${item.mensaje}<br>`;
            }
            if (item.titulo) {
                content += `
                    <div class="libro-card">
                        <div class="libro-content">
                            <div class="libro-header">
                                ${item.img_portada ? 
                                    `<div class="libro-portada">
                                        <img src="${item.img_portada}" alt="Portada de ${item.titulo}">
                                    </div>` : 
                                    `<div class="libro-portada-default">
                                        <i class="fas fa-book"></i>
                                    </div>`
                                }
                                <div class="libro-info">
                                    <h4>${item.titulo}</h4>
                                    <div class="libro-badges">
                                        ${item.tipo ? `<span class="badge-custom tipo">${item.tipo}</span>` : ''}
                                        ${item.categoria ? `<span class="badge-custom categoria">${item.categoria}</span>` : ''}
                                        ${item.categorias && item.categorias.length > 0 ? 
                                            item.categorias.map(cat => `<span class="badge-custom categoria">${cat}</span>`).join('') 
                                            : ''}
                                        ${item.edicion ? `<span class="badge-custom edicion"><i class="fas fa-book-open"></i> ${item.edicion}</span>` : ''}
                                    </div>
                                    ${item.autores ? `<p class="libro-autores"><i class="fas fa-user-edit"></i> ${item.autores}</p>` : ''}
                                    ${item.palabra_clave ? `<p class="libro-keywords"><i class="fas fa-tags"></i> Palabras clave: ${item.palabra_clave}</p>` : ''}
                                </div>
                            </div>
                            ${item.descripcion ? `
                                <div class="libro-descripcion">
                                    <p>${item.descripcion}</p>
                                </div>` : ''
                            }
                            <div class="libro-acciones">
                                ${item.pdf && item.descarga_autorizada ? 
                                    `<a href="${item.pdf}" target="_blank" class="libro-link">
                                        <span class="link-text">Ver PDF</span>
                                        <i class="fas fa-file-pdf"></i>
                                    </a>` : 
                                    (item.pdf ? 
                                        `<span class="libro-link disabled">
                                            <span class="link-text">Acceso restringido</span>
                                            <i class="fas fa-building"></i>
                                        </span>` : '')
                                }
                                ${item.pdf_url ? 
                                    `<a href="${item.pdf_url}" target="_blank" class="libro-link secundario">
                                        <span class="link-text">Enlace externo</span>
                                        <i class="fas fa-external-link-alt"></i>
                                    </a>` : ''
                                }
                                ${item.archivo_autorizacion ? 
                                    `<a href="${item.archivo_autorizacion}" target="_blank" class="libro-link autorizacion">
                                        <span class="link-text">Ver Autorización</span>
                                        <i class="fas fa-file-contract"></i>
                                    </a>` : ''
                                }
                            </div>
                        </div>
                    </div>
                `;
            }
            if (item.sugerencias && !Array.isArray(item.sugerencias)) {
                content += `<p>${item.sugerencias}</p>`;
            }
        });
        botDiv.innerHTML = content;
    }
    chatBox.appendChild(botDiv);
    chatBox.scrollTop = chatBox.scrollHeight;
}

document.addEventListener('DOMContentLoaded', function() {
    const chatBox = document.getElementById('chat-box');
    const chatInput = document.getElementById('chat-input');
    const sendButton = document.getElementById('send-button');
    let isTyping = false;

    // Función para mostrar indicador de escritura
    function showTypingIndicator() {
        if (!isTyping) {
            isTyping = true;
            const typingDiv = document.createElement('div');
            typingDiv.className = 'typing-indicator';
            typingDiv.innerHTML = `
                <div class="typing-dot"></div>
                <div class="typing-dot"></div>
                <div class="typing-dot"></div>
            `;
            chatBox.appendChild(typingDiv);
            chatBox.scrollTop = chatBox.scrollHeight;
        }
    }

    // Función para ocultar indicador de escritura
    function hideTypingIndicator() {
        const typingIndicator = document.querySelector('.typing-indicator');
        if (typingIndicator) {
            typingIndicator.remove();
        }
        isTyping = false;
    }

    // Función para enviar mensaje al backend
    async function sendMessage(message) {
        try {
            showTypingIndicator();
            const response = await fetch(`/buscar_libros?q=${encodeURIComponent(message)}`);
            if (!response.ok) {
                if (response.status === 404) {
                    throw new Error('Servicio no encontrado');
                } else if (response.status === 500) {
                    throw new Error('Error interno del servidor');
                } else if (response.status === 429) {
                    return [{
                        mensaje: "El sistema está ocupado en este momento. Por favor, espera un momento antes de intentar de nuevo ",
                        tipo: 'error'
                    }];
                } else {
                    throw new Error(`Error ${response.status}`);
                }
            }
            const data = await response.json();
            hideTypingIndicator();
            return data;
        } catch (error) {
            console.error('Error:', error);
            hideTypingIndicator();
            let errorMessage = "¡Ups! ";
            
            if (error.message.includes('Failed to fetch')) {
                errorMessage += "No puedo conectarme al servidor. ¿Podrías verificar tu conexión a internet?";
            } else if (error.message.includes('Servicio no encontrado')) {
                errorMessage += "No encuentro el servicio de búsqueda. Por favor, avisa al administrador.";
            } else if (error.message.includes('Error interno')) {
                errorMessage += "Hay un problema en el servidor. El equipo técnico está trabajando en ello.";
            } else {
                errorMessage += "Algo no salió como esperaba. ¿Podrías intentarlo de nuevo?";
            }
            
            return [{
                mensaje: errorMessage,
                tipo: 'error'
            }];
        }
    }

    // Manejador del evento de envío
    async function handleSend() {
        const message = chatInput.value.trim();
        if (message) {
            addUserMessage(message);
            chatInput.value = '';
            
            showTypingIndicator();

            try {
                // Procesar comandos especiales
                if (message.toLowerCase().includes('ayuda')) {
                    hideTypingIndicator();
                    mostrarAyuda();
                    return;
                } else if (message.toLowerCase().includes('novedades')) {
                    hideTypingIndicator();
                    buscarNovedades();
                    return;
                } else if (message.toLowerCase().includes('categorías') || message.toLowerCase().includes('categorias')) {
                    hideTypingIndicator();
                    mostrarCategorias();
                    return;
                }

                // Búsqueda normal de libros
                const response = await sendMessage(message);
                hideTypingIndicator();
                
                if (Array.isArray(response) && response.length === 0) {
                    addBotMessage({
                        mensaje: "No encontré exactamente lo que buscas, pero ¿qué tal si intentamos con otras palabras? Por ejemplo, podrías buscar por tema o autor ",
                        tipo: 'sugerencia'
                    });
                } else {
                    addBotMessage(response);
                }
            } catch (error) {
                console.error('Error:', error);
                hideTypingIndicator();
                addBotMessage({
                    mensaje: "¡Hola! Parece que hay un pequeño problema de conexión. ¿Podrías intentar de nuevo? Estoy aquí para ayudarte ",
                    tipo: 'error'
                });
            }
        }
    }

    // Event listeners
    sendButton.addEventListener('click', handleSend);
    chatInput.addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            e.preventDefault();
            handleSend();
        }
    });

    // Mensaje de bienvenida inicial
    addBotMessage({
        mensaje: "¡Hola! Soy tu asistente virtual. ¿En qué puedo ayudarte hoy? Puedes preguntarme sobre libros, autores o temas específicos.",
        tipo: 'bienvenida'
    });

    // Función para buscar novedades
    window.buscarNovedades = function() {
        addUserMessage("Mostrar últimas novedades");
        showTypingIndicator();
        
        fetch('/obtener_novedades/')
            .then(response => {
                if (!response.ok) {
                    throw new Error(`HTTP error! status: ${response.status}`);
                }
                return response.json();
            })
            .then(data => {
                console.log('Respuesta del servidor:', data); // Para depuración
                if (data.status === 'success' && data.libros && data.libros.length > 0) {
                    const mensajeCompleto = [
                        { mensaje: data.mensaje },
                        ...data.libros
                    ];
                    addBotMessage(mensajeCompleto);
                } else {
                    addBotMessage(data.mensaje || "No se encontraron libros recientes.");
                }
            })
            .catch(error => {
                console.error('Error en buscarNovedades:', error);
                addBotMessage("Lo siento, hubo un error al obtener las novedades. " + error.message);
            })
            .finally(() => {
                hideTypingIndicator();
            });
    };
});

// Funcionalidad del micrófono
let recognition = null;
let isListening = false;

function initSpeechRecognition() {
    if ('webkitSpeechRecognition' in window) {
        recognition = new webkitSpeechRecognition();
        recognition.continuous = false;
        recognition.interimResults = false;
        recognition.lang = 'es-ES';

        recognition.onstart = function() {
            isListening = true;
            const micButton = document.querySelector('.voice-input-btn i');
            if (micButton) {
                micButton.classList.remove('fa-microphone');
                micButton.classList.add('fa-microphone-slash');
                micButton.parentElement.classList.add('listening');
            }
        };

        recognition.onend = function() {
            isListening = false;
            const micButton = document.querySelector('.voice-input-btn i');
            if (micButton) {
                micButton.classList.remove('fa-microphone-slash');
                micButton.classList.add('fa-microphone');
                micButton.parentElement.classList.remove('listening');
            }
        };

        recognition.onresult = function(event) {
            const transcript = event.results[0][0].transcript;
            document.getElementById('chat-input').value = transcript;
        };

        recognition.onerror = function(event) {
            console.error('Error en reconocimiento de voz:', event.error);
            isListening = false;
            const micButton = document.querySelector('.voice-input-btn i');
            if (micButton) {
                micButton.classList.remove('fa-microphone-slash');
                micButton.classList.add('fa-microphone');
                micButton.parentElement.classList.remove('listening');
            }
            if (event.error === 'not-allowed') {
                alert('Por favor, permite el acceso al micrófono para usar esta función');
            }
        };
    }
}

function toggleVoiceInput() {
    if (!recognition) {
        initSpeechRecognition();
    }

    if (recognition) {
        if (!isListening) {
            recognition.start();
        } else {
            recognition.stop();
        }
    } else {
        console.error('El reconocimiento de voz no está soportado en este navegador');
        alert('Lo siento, el reconocimiento de voz no está disponible en este navegador');
    }
}

// Inicializar el reconocimiento de voz cuando se carga la página
document.addEventListener('DOMContentLoaded', function() {
    initSpeechRecognition();
});

// Funciones para los botones de acción
function nuevaBusqueda() {
    document.getElementById('chat-input').value = '';
    document.getElementById('chat-input').focus();
}

function limpiarChat() {
    if (confirm('¿Estás seguro de que quieres limpiar el chat?')) {
        document.getElementById('chat-box').innerHTML = '';
    }
}

// Agregar función de texto a voz para mensajes del bot
function speakMessage(text) {
    const utterance = new SpeechSynthesisUtterance(text);
    utterance.lang = 'es-ES';
    speechSynthesis.speak(utterance);
}

// Agregar botón de voz a los mensajes del bot
function addVoiceButton(message) {
    return `
        <div class="bot-message">
            <strong>Asistente:</strong> ${message}
            <button onclick="speakMessage('${message}')" class="voice-btn">
                <i class="fas fa-volume-up"></i>
            </button>
        </div>`;
}
// Función para mostrar buscadores externos
window.busExterno = function() {
    const recursos = {
        libros: [
            { nombre: 'Wosky Libros', url: 'https://wosky.org/libros/', descripcion: 'Biblioteca digital con amplia colección de libros' },
            { nombre: 'GetGPT Books', url: 'https://getgpt.app/play/32moHidZHr', descripcion: 'Buscador inteligente de libros' },
            { nombre: 'Project Gutenberg', url: 'https://www.gutenberg.org/', descripcion: 'Biblioteca gratuita de libros electrónicos' },
            { nombre: 'Internet Archive', url: 'https://archive.org/details/texts', descripcion: 'Colección digital de textos y libros' },
            { nombre: 'GBS Cor Libros', url: 'https://sites.google.com/site/gbscor/home/libros', descripcion: 'Recursos y libros educativos' },
            { nombre: 'Open Library', url: 'https://openlibrary.org/', descripcion: 'Biblioteca universal de acceso abierto' }
        ],
        arte: [
            { nombre: 'Google Arts & Culture', url: 'https://artsandculture.google.com/', descripcion: 'Explora colecciones de arte de todo el mundo' },
            { nombre: 'Saatchi Art', url: 'https://www.saatchiart.com/account/artworks/636941', descripcion: 'Galería de arte contemporáneo online' },
            { nombre: 'Artsy', url: 'https://www.artsy.net/', descripcion: 'Plataforma líder de arte contemporáneo' },
            { nombre: 'ArtStation', url: 'https://www.artstation.com/', descripcion: 'Plataforma de arte digital y diseño' },
            { nombre: 'Behance', url: 'https://www.behance.net/', descripcion: 'Red de portafolios creativos' },
            { nombre: 'Art Limited', url: 'https://www.artlimited.net/', descripcion: 'Red social para artistas visuales' }
        ],
        museos: [
            { nombre: 'Museo del Prado', url: 'https://www.museodelprado.es/coleccion', descripcion: 'Colección digital del Museo del Prado' },
            { nombre: 'MoMA', url: 'https://www.moma.org/collection/', descripcion: 'Museo de Arte Moderno de Nueva York' },
            { nombre: 'Louvre', url: 'https://www.louvre.fr/en/online-tours', descripcion: 'Tours virtuales del Museo del Louvre' },
            { nombre: 'Met Museum', url: 'https://www.metmuseum.org/art/collection', descripcion: 'Colección del Metropolitan Museum' },
            { nombre: 'Museo Reina Sofía', url: 'https://www.museoreinasofia.es/coleccion', descripcion: 'Arte moderno y contemporáneo' }
        ],
        recursos_arte: [
            { nombre: 'Art Resource', url: 'http://www.artres.com/', descripcion: 'Banco de imágenes de arte' },
            { nombre: 'Web Gallery of Art', url: 'https://www.wga.hu/', descripcion: 'Base de datos de arte europeo' },
            { nombre: 'WikiArt', url: 'https://www.wikiart.org/', descripcion: 'Enciclopedia visual de arte' },
            { nombre: 'Art History Resources', url: 'http://arthistoryresources.net/', descripcion: 'Recursos de historia del arte' }
        ]
    };

    const mensajeAsistente = `
        <div class="asistente-mensaje">
            <p>¡Hola! He recopilado una selección de recursos digitales que pueden ser de gran ayuda en tu búsqueda. 
            Aquí encontrarás bibliotecas digitales, galerías de arte, museos virtuales y recursos educativos. 
            Cada enlace ha sido cuidadosamente seleccionado para ofrecerte acceso a contenido de calidad.</p>
        </div>
    `;

    let mensaje = `
        ${mensajeAsistente}
        <div class="recursos-container">
            ${Object.entries(recursos).map(([categoria, items]) => `
                <div class="categoria-card">
                    <h4 class="categoria-titulo">${getCategoriaTitle(categoria)}</h4>
                    <div class="recursos-grid">
                        ${items.map(recurso => `
                            <div class="recurso-card">
                                <h5>
                                    <a href="${recurso.url}" target="_blank" rel="noopener noreferrer">
                                        ${recurso.nombre}
                                    </a>
                                </h5>
                                <p>${recurso.descripcion}</p>
                            </div>
                        `).join('')}
                    </div>
                </div>
            `).join('')}
        </div>
    `;
    addBotMessage(mensaje);
}

// Función auxiliar para obtener títulos en español
function getCategoriaTitle(categoria) {
    const titulos = {
        libros: 'Bibliotecas Digitales y Libros',
        arte: 'Galerías de Arte',
        museos: 'Museos Virtuales',
        recursos_arte: 'Recursos de Arte'
    };
    return titulos[categoria] || categoria;
}

function mostrarAyuda() {
    $('#resultados-modal').modal('show');
    $('#modal-title').text('Ayuda');
    $('#modal-body').html(`
        <div class="help-content">
            <h5><i class="fas fa-robot"></i> ¿Cómo usar el asistente?</h5>
            <ul>
                <li>Escribe tu pregunta en el campo de texto</li>
                <li>Usa palabras clave como "autor", "libro", "buscar"</li>
                <li>Puedes hacer preguntas naturales como "¿tienes libros de García Márquez?"</li>
                <li>Utiliza los botones de preguntas frecuentes para consultas rápidas</li>
            </ul>

            <h5><i class="fas fa-robot"></i> Capacidades del Asistente IA</h5>
            <ul>
                <li>Búsqueda Inteligente:</li>
                <ul>
                    <li>Entiende preguntas en lenguaje natural</li>
                    <li>Sugiere términos relacionados y alternativas</li>
                    <li>Aprende de las interacciones previas</li>
                </ul>
                <li>Asistencia Personalizada:</li>
                <ul>
                    <li>Ayuda con búsquedas específicas por área </li>
                    <li>Proporciona información sobre recursos en la web</li>
                </ul>
            </ul>

            <h5><i class="fas fa-search"></i> Búsqueda Básica</h5>
            <ul>
                <li>Sé específico en tus búsquedas</li>
                <li>El asistente está optimizado para búsquedas generales de libros en la plataforma</li>
                <li>Evita errores gramaticales y ortográficos para mejores resultados</li>
                <li>Utiliza las sugerencias para descubrir nuevos libros</li>
            </ul>

            <h5><i class="fas fa-filter"></i> Filtros y Categorías</h5>
            <ul>
                <li>Filtra por edición, área, categoría o idioma</li>
                <p>Tambien puedes ir a la pestaña "Catalogo" para ver todos los libros y hacer la busqueda por filtro</p>
                <li>Usa las menciones específicas como "Escultura", "Grabado", "Diseño"</li>
                <li>Explora por nivel académico en la pestaña correspondiente</li>
                <li>Revisa el catálogo completo para una vista general</li>
            </ul>

            <h5><i class="fas fa-globe"></i> Búsqueda Avanzada y Recursos Externos</h5>
            <ul>
                <li>Utiliza la barra lateral para acceder a:</li>
                <ul>
                    <li>Búsquedas avanzadas y específicas</li>
                    <li>Recursos externos y bases de datos</li>
                </ul>
                <li>Explora los recursos virtuales para acceder a repositorios institucionales</li>
                <li>Combina diferentes criterios para búsquedas más precisas</li>
            </ul>
        </div>
    `);
}

function mostrarFAQ() {
    $('#resultados-modal').modal('show');
    $('#modal-title').text('Centro de Ayuda - Preguntas Frecuentes');
    $('#modal-body').html(`
        <div class="faq-content">
            <div class="accordion" id="faqAccordion">
                <!-- Búsqueda -->
                <div class="card">
                    <div class="card-header" id="headingOne">
                        <h2 class="mb-0">
                            <button class="btn btn-link" type="button" data-toggle="collapse" data-target="#collapseOne">
                                <i class="fas fa-search"></i> Búsqueda de Libros
                            </button>
                        </h2>
                    </div>
                    <div id="collapseOne" class="collapse show" data-parent="#faqAccordion">
                        <div class="card-body">
                            <h6><strong>¿Cómo busco un libro específico?</strong></h6>
                            <p>Puedes escribir el título, autor o ISBN en el campo de búsqueda. También puedes usar filtros avanzados para refinar tu búsqueda.</p>
                            
                            <h6><strong>¿Puedo buscar por mencion?</strong></h6>
                            <p>Sí, usa palabras clave como "Escultura" o "Grabado" y en etre otras en tu búsqueda.</p>
                        </div>
                    </div>
                </div>

                <!-- Resultados -->
                <div class="card">
                    <div class="card-header" id="headingTwo">
                        <h2 class="mb-0">
                            <button class="btn btn-link collapsed" type="button" data-toggle="collapse" data-target="#collapseTwo">
                                <i class="fas fa-list"></i> Resultados y Filtros
                            </button>
                        </h2>
                    </div>
                    <div id="collapseTwo" class="collapse" data-parent="#faqAccordion">
                        <div class="card-body">
                            <h6><strong>¿Cómo filtro los resultados?</strong></h6>
                            <p>Usa los filtros en la barra lateral para refinar por categoria, tipo de archivo o disponibilidad.</p>
                            <p>Tambien puedes ir a la pestaña "Catalogo" para ver todos los libros y hacer la busqueda por filtro</p>
                            <h6><strong>¿Por qué no encuentro un libro específico?</strong></h6>
                            <p>Verifica la ortografía o intenta con términos alternativos. Si persiste, contacta a soporte.</p>
                        </div>
                    </div>
                </div>

                <!-- Funcionalidades -->
                <div class="card">
                    <div class="card-header" id="headingThree">
                        <h2 class="mb-0">
                            <button class="btn btn-link collapsed" type="button" data-toggle="collapse" data-target="#collapseThree">
                                <i class="fas fa-cogs"></i> Funcionalidades Adicionales
                            </button>
                        </h2>
                    </div>
                    <div id="collapseThree" class="collapse" data-parent="#faqAccordion">
                        <div class="card-body">
                            <h6><strong>¿Puedo usar comandos de voz?</strong></h6>
                            <p>Sí, haz clic en el ícono del micrófono para activar la búsqueda por voz.</p>
                            
                            <h6><strong>¿Cómo guardo mis búsquedas favoritas?</strong></h6>
                            <p>NO, Pero los libros que se visitan en los de mas pestañas como en "inicio","Nivel" y "Catalogo" los libros que vayas visitando se guardaran en tu historial</p>
                        </div>
                    </div>
                </div>
                <!-- Galería de Arte -->
                <div class="card">
                    <div class="card-header" id="headingSix">
                        <h2 class="mb-0">
                            <button class="btn btn-link collapsed" type="button" data-toggle="collapse" data-target="#collapseSix">
                                <i class="fas fa-palette"></i> Galería de Arte
                            </button>
                        </h2>
                    </div>
                    <div id="collapseSix" class="collapse" data-parent="#faqAccordion">
                        <div class="card-body">
                            <h6><strong>¿Cómo puedo mostrar mi arte en la galería?</strong></h6>
                            <p>
                                Para exhibir tu trabajo en la galería, sigue estos pasos:
                                <ol>
                                    <li>Visita la biblioteca de la carrera de Artes Plásticas y Diseño Gráfico.</li>
                                    <li>Trae tus imágenes en buena calidad.</li>
                                    <li>Proporciona el título y la descripción que deseas mostrar junto a tu obra.</li>
                                </ol>
                            </p>
                            
                            <h6><strong>¿Qué tipo de arte puedo compartir?</strong></h6>
                            <p>
                                Puedes compartir cualquier tipo de arte visual, como: pinturas, dibujos, fotografías, diseños digitales.
                                Lo importante es que las imágenes sean de alta o buena calidad para garantizar una buena visualización en la galería.
                            </p>

                            <h6><strong>¿El sistema protege los derechos de autor?</strong></h6>
                            <p>
                                Sí, el sistema agrega una marca de agua a las imágenes para protegerlas contra el uso no autorizado y resaltar la autoría del artista.
                            </p>
                        </div>
                    </div>

                <!-- Préstamos y Reservas -->
                <div class="card">
                    <div class="card-header" id="headingFive">
                        <h2 class="mb-0">
                            <button class="btn btn-link collapsed" type="button" data-toggle="collapse" data-target="#collapseFive">
                                <i class="fas fa-book-reader"></i> Préstamos y Reservas
                            </button>
                        </h2>
                    </div>
                    <div id="collapseFive" class="collapse" data-parent="#faqAccordion">
                        <div class="card-body">
                            <h6><strong>¿Puedo realizar préstamos o reservaciones desde la plataforma?</strong></h6>
                            <p>NO, los préstamos y reservas solo se pueden realizar de forma presencial en la biblioteca de la carrera.</p>
                            
                            <h6><strong>¿Qué necesito para hacer un préstamo?</strong></h6>
                            <p>Debes acudir personalmente a la biblioteca de la carrera con tu carnet y maatricula vigente.</p>
                        </div>
                    </div>
                </div>
                <!-- Problemas Comunes -->
                <div class="card">
                    <div class="card-header" id="headingFour">
                        <h2 class="mb-0">
                            <button class="btn btn-link collapsed" type="button" data-toggle="collapse" data-target="#collapseFour">
                                <i class="fas fa-exclamation-circle"></i> Solución de Problemas
                            </button>
                        </h2>
                    </div>
                    <div id="collapseFour" class="collapse" data-parent="#faqAccordion">
                        <div class="card-body">
                            <h6><strong>El chatbot no responde</strong></h6>
                            <p>Intenta refrescar la página o limpiar el chat. Si el problema persiste, contacta a soporte.</p>
                            
                            <h6><strong>Los resultados tardan en cargar</strong></h6>
                            <p>Verifica tu conexión a internet o intenta más tarde. También puedes probar limpiando el caché del navegador.</p>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    `);
}

function buscarPorGenero() {
    $('#resultados-modal').modal('show');
    $('#modal-title').text('Guía de Búsqueda de Libros');
    $('#modal-body').html(`
        <div class="search-guide">
            <div class="guide-section mb-4">
                <h5><i class="fas fa-search"></i> Búsqueda Básica</h5>
                <ul class="list-unstyled">
                    <li class="mb-2"><i class="fas fa-check text-success"></i> Escribe el título o autor en el campo de búsqueda</li>
                    <li class="mb-2"><i class="fas fa-check text-success"></i> Usa palabras clave como "novela", "poesía", "historia"</li>
                    <li class="mb-2"><i class="fas fa-check text-success"></i> Incluye el año o época si lo conoces</li>
                </ul>
            </div>

            <div class="guide-section mb-4">
                <h5><i class="fas fa-filter"></i> Filtros por Área Artística</h5>
                <div class="row">
                    <div class="col-md-6">
                        <h6>Por Disciplina</h6>
                        <ul class="list-unstyled">
                            <li><button class="btn btn-link" onclick="buscarTiposs('Pintura')">Pintura</button></li>
                            <li><button class="btn btn-link" onclick="buscarTiposs('Dibujo')">Dibujo</button></li>
                            <li><button class="btn btn-link" onclick="buscarTiposs('Diseño')">Diseño</button></li>
                            <li><button class="btn btn-link" onclick="buscarTiposs('Historia del Arte')">Historia del Arte</button></li>
                            <li><button class="btn btn-link" onclick="buscarTiposs('Teoría del Arte')">Teoría del Arte</button></li>
                        </ul>
                    </div>
                    <div class="col-md-6">
                        <h6>Por Época</h6>
                        <ul class="list-unstyled">
                            <li><button class="btn btn-link" onclick="buscarTiposs('Arte Clásico')">Arte Clásico</button></li>
                            <li><button class="btn btn-link" onclick="buscarTiposs('Arte Medieval')">Arte Medieval</button></li>
                            <li><button class="btn btn-link" onclick="buscarTiposs('Renacimiento')">Renacimiento</button></li>
                            <li><button class="btn btn-link" onclick="buscarTiposs('Arte Moderno')">Arte Moderno</button></li>
                            <li><button class="btn btn-link" onclick="buscarTiposs('Arte Contemporáneo')">Arte Contemporáneo</button></li>
                        </ul>
                    </div>
                </div>

                <div class="row mt-3">
                    <div class="col-md-6">
                        <h6>Por categorias</h6>
                        <ul class="list-unstyled">
                            <li><button class="btn btn-link" onclick="buscarTiposs('Ceramica')">Ceramica</button></li>
                            <li><button class="btn btn-link" onclick="buscarTiposs('Escultura')">Escultura</button></li>
                            <li><button class="btn btn-link" onclick="buscarTiposs('Tallado')">Tallado</button></li>
                            <li><button class="btn btn-link" onclick="buscarTiposs('Serigrafia')">Serigrafia</button></li>
                        </ul>
                    </div>
                    <div class="col-md-6">
                        <h6>Por Técnica</h6>
                        <ul class="list-unstyled">
                            <li><button class="btn btn-link" onclick="buscarTiposs('Óleo')">Óleo</button></li>
                            <li><button class="btn btn-link" onclick="buscarTiposs('Acuarela')">Acuarela</button></li>
                            <li><button class="btn btn-link" onclick="buscarTiposs('Diseño Digital')">Diseño Digital</button></li>
                            <li><button class="btn btn-link" onclick="buscarTiposs('Técnicas Mixtas')">Técnicas Mixtas</button></li>
                        </ul>
                    </div>
                </div>
            </div>

            <div class="guide-section">
                <h5><i class="fas fa-lightbulb"></i> Consejos de Búsqueda</h5>
                <ul class="list-group">
                    <li class="list-group-item">Usa comillas para búsquedas exactas: "Historia del Arte"</li>
                    <li class="list-group-item">Combina términos: autor + género + año</li>
                    <li class="list-group-item">Utiliza los filtros para refinar resultados</li>
                </ul>
            </div>
        </div>
    `);
}

function buscarTiposs(tipo) {
    $('#resultados-modal').modal('hide');
    document.getElementById('chat-input').value = `Buscar libros de ${tipo}`;
    document.getElementById('send-button').click();
}

function mostrarCategorias() {
    $('#resultados-modal').modal('show');
    $('#modal-title').text('Tipos de Libros Disponibles');
    $('#modal-body').html(`
        <div class="categories-content">
            <!-- Tipos de Documentos -->
            <div class="row mb-4">
                <div class="col-12">
                    <h5><i class="fas fa-book-open"></i> Tipos de Documentos</h5>
                    <div class="list-group">
                        <button onclick="buscarTipo('LIBRO')" class="list-group-item list-group-item-action">
                            <i class="fas fa-book"></i> Libros
                        </button>
                        <button onclick="buscarTipo('ARTICULO')" class="list-group-item list-group-item-action">
                            <i class="fas fa-newspaper"></i> Artículos
                        </button>
                        <button onclick="buscarTipo('REVISTA')" class="list-group-item list-group-item-action">
                            <i class="fas fa-magazine"></i> Revistas
                        </button>
                        <button onclick="buscarTipo('TESIS')" class="list-group-item list-group-item-action">
                            <i class="fas fa-graduation-cap"></i> Tesis
                        </button>
                        <button onclick="buscarTipo('DICCIONARIO')" class="list-group-item list-group-item-action">
                            <i class="fas fa-spell-check"></i> Diccionarios
                        </button>
                        <button onclick="buscarTipo('MONOGRAFIA')" class="list-group-item list-group-item-action">
                            <i class="fas fa-file-alt"></i> Monografías
                        </button>
                        <button onclick="buscarTipo('FOLLETO')" class="list-group-item list-group-item-action">
                            <i class="fas fa-file-pdf"></i> Folletos
                        </button>
                        <button onclick="buscarTipo('INFORME')" class="list-group-item list-group-item-action">
                            <i class="fas fa-file-contract"></i> Informes
                        </button>
                        <button onclick="buscarTipo('OTRO')" class="list-group-item list-group-item-action">
                            <i class="fas fa-file"></i> Otros Documentos
                        </button>
                    </div>
                </div>
            </div>
            <div class="mt-4 text-center">
                <p class="text-muted">
                    <i class="fas fa-info-circle"></i> 
                    Haz clic en cualquier tipo de documento de interes para buscar
                </p>
            </div>
        </div>
    `);

    // Cerrar modal al hacer clic en un botón
    $('#modal-body button').click(function() {
        $('#resultados-modal').modal('hide');
    });
}

// Funciones auxiliares para las búsquedas por categoría
function buscarTipo(tipo) {
    let mensaje;
    if (tipo === 'todos') {
        mensaje = 'Mostrar todos los documentos';
    } else {
        mensaje = `tipo:${tipo}`;  // Formato especial para búsqueda por tipo
    }
    document.getElementById('chat-input').value = mensaje;
    document.getElementById('send-button').click();
}

function mostrarMensaje(mensaje, tipo) {
    const chatMessages = document.querySelector('.chat-messages');
    const messageDiv = document.createElement('div');
    messageDiv.classList.add('message');
    
    if (tipo === 'historial_item') {
        messageDiv.classList.add('historial-item');
        messageDiv.innerHTML = `<span class="historial-texto">${mensaje}</span>`;
    } else {
        messageDiv.classList.add(tipo === 'usuario' ? 'user-message' : 'bot-message');
        messageDiv.textContent = mensaje;
    }
    
    chatMessages.appendChild(messageDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

function enviarPregunta(pregunta) {
    const chatInput = document.getElementById('chat-input');
    if (chatInput) {
        chatInput.value = pregunta;
        const sendButton = document.getElementById('send-button');
        if (sendButton) {
            sendButton.click();
        }
    }
}

document.addEventListener('click', function(event) {
    const leftSidebar = document.querySelector('.left-sidebar');
    const rightSidebar = document.querySelector('.right-sidebar');
    const leftToggle = document.querySelector('.toggle-left');
    const rightToggle = document.querySelector('.toggle-right');

    if (leftSidebar && leftSidebar.classList.contains('active') && 
        !leftSidebar.contains(event.target) && 
        event.target !== leftToggle) {
        leftSidebar.classList.remove('active');
    }

    if (rightSidebar && rightSidebar.classList.contains('active') && 
        !rightSidebar.contains(event.target) && 
        event.target !== rightToggle) {
        rightSidebar.classList.remove('active');
    }
});

// Funciones para los botones de acción
function nuevaBusqueda() {
    document.getElementById('chat-input').value = '';
    document.getElementById('chat-input').focus();
}

function RecursosVirtuales() {
    const recursos = [
        {
            nombre: "Repositorio Institucional UMSA",
            url: "https://repositorio.umsa.bo",
            descripcion: "Explora la producción científica de la UMSA a través de nuestro Repositorio Institucional.Accede a tesis, proyectos de grado y trabajos dirigidos en formato PDF a texto completo.",
            logo: "/static/imgLogos/rep-ins.png",
        },
        {
            nombre: "Research4Life",
            url: "https://portal.research4life.org",
            descripcion: "Acceso a información científica y académica de texto completo. Requiere cuenta institucional para ingresar.",
            logo: "/static/imgLogos/LogoRese.png",
        },
        {
            nombre: "SciELO",
            url: "https://scielo.org",
            descripcion: "Acceso libre a libros, journals y revistas científicas electrónicas a texto completo.",
            logo: "/static/imgLogos/logoscielo.png",
        },
        {
            nombre: "Scopus",
            url: "https://www.scopus.com",
            descripcion: "Base de datos con producción académica y científica de más de 7000 editoriales.",
            logo: "/static/imgLogos/scopus.png",
        },
        {
            nombre: "Biblioteca UMSA - Estantería Virtual",
            url: "http://bibliotecas.umsa.bo",
            descripcion: "Consulta material bibliográfico, tesis y proyectos de grado para préstamo a domicilio o en formato digital.",
            logo: "/static/imgLogos/logoRecB.png",
        }
    ];

    let mensaje = '<div class="bot-message"><strong>Asistente:</strong> Aquí tienes los recursos institucionales disponibles:</div>';
    mensaje += '<div class="recursos-grid">';
    
    recursos.forEach(recurso => {
        mensaje += `
            <div class="recurso-card">
                <div class="recurso-content">
                    <div class="recurso-header">
                        <img src="${recurso.logo}" alt="${recurso.nombre}" class="recurso-logo">
                    </div>
                    <h4>${recurso.nombre}</h4>
                    <p>${recurso.descripcion}</p>
                    <a href="${recurso.url}" target="_blank" class="recurso-link">
                        <span class="link-text">Explorar Recursos</span>
                        <i class="fas fa-arrow-right"></i>
                    </a>
                </div>
            </div>
        `;
    });
    
    mensaje += '</div>';
    addBotMessage(mensaje);
}

function toggleSidebar(side) {
    const leftSidebar = document.getElementById('leftSidebar');
    const rightSidebar = document.getElementById('rightSidebar');
    
    // Si el sidebar que queremos abrir ya está abierto, lo cerramos
    if (side === 'left' && leftSidebar.classList.contains('active')) {
        leftSidebar.classList.remove('active');
        return;
    }
    if (side === 'right' && rightSidebar.classList.contains('active')) {
        rightSidebar.classList.remove('active');
        return;
    }

    // Cerrar cualquier sidebar abierto
    leftSidebar.classList.remove('active');
    rightSidebar.classList.remove('active');

    // Abrir el sidebar seleccionado
    if (side === 'left') {
        leftSidebar.classList.add('active');
    } else {
        rightSidebar.classList.add('active');
    }
}

// Cerrar sidebars al hacer clic fuera
document.addEventListener('click', function(event) {
    const leftSidebar = document.getElementById('leftSidebar');
    const rightSidebar = document.getElementById('rightSidebar');

    // Si el clic no fue dentro de un sidebar ni en un botón de toggle
    if (!event.target.closest('.action-sidebar') && 
        !event.target.closest('.menu-toggle')) {
        leftSidebar.classList.remove('active');
        rightSidebar.classList.remove('active');
    }
});

// Inicializar la navegación móvil cuando se carga el documento
document.addEventListener('DOMContentLoaded', function() {
    // Inicializar los botones de navegación móvil
    const mobileButtons = document.querySelectorAll('.menu-toggle');
    mobileButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            e.preventDefault();
            const side = this.getAttribute('data-side');
            toggleSidebar(side);
        });
    });
});

// Función mejorada para cerrar sidebars y modales
function closeElement(elementId) {
    const element = document.getElementById(elementId);
    if (element) {
        if (element.classList.contains('modal')) {
            $(element).modal('hide');
        } else {
            element.classList.remove('active', 'show');
        }
    }
}

// Event listeners para botones de cerrar
document.addEventListener('DOMContentLoaded', function() {
    // Cerrar modales
    const closeButtons = document.querySelectorAll('[data-dismiss="modal"]');
    closeButtons.forEach(button => {
        button.addEventListener('click', function() {
            const modalId = this.closest('.modal').id;
            closeElement(modalId);
        });
    });

    // Cerrar sidebars
    const sidebarCloseButtons = document.querySelectorAll('.sidebar-close');
    sidebarCloseButtons.forEach(button => {
        button.addEventListener('click', function() {
            const sidebar = this.closest('.action-sidebar');
            if (sidebar) {
                sidebar.classList.remove('active', 'show');
            }
        });
    });

    // Cerrar al hacer clic fuera
    document.addEventListener('click', function(event) {
        const sidebars = document.querySelectorAll('.action-sidebar');
        const modals = document.querySelectorAll('.modal');
        
        sidebars.forEach(sidebar => {
            if (!sidebar.contains(event.target) && !event.target.matches('.sidebar-toggle')) {
                sidebar.classList.remove('active', 'show');
            }
        });

        modals.forEach(modal => {
            if (modal.classList.contains('show') && !modal.contains(event.target) && !event.target.matches('[data-toggle="modal"]')) {
                $(modal).modal('hide');
            }
        });
    });
});