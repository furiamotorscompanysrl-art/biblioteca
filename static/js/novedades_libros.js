let pdfDoc = null;
let pageNum = 1;
let zoomLevel = 0.72;
let canvas = document.getElementById('pdfCanvas');
let ctx = canvas.getContext('2d');

function renderPage(num) {
  pdfDoc.getPage(num).then(function(page) {
    let viewport = page.getViewport({scale: zoomLevel});
    canvas.height = viewport.height;
    canvas.width = viewport.width;

    page.render({
      canvasContext: ctx,
      viewport: viewport
    });
  });
  document.getElementById('pageNum').textContent = num;
}

function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

function registrarVisita(libroId) {
    const csrftoken = getCookie('csrftoken');
    
    return fetch(`/registrar_visita/${libroId}/`, {
        method: 'POST',
        headers: {
            'X-CSRFToken': csrftoken,
            'Content-Type': 'application/json',
        },
    })
    .then(response => response.json())
    .then(data => {
        console.log('Visita registrada:', data);
        return data;
    })
    .catch(error => {
        console.error('Error al registrar visita:', error);
        // Return null instead of throwing error
        return null;
    });
}

function manejarPDF(pdfUrl, libroId, descargaAutorizada) {
    const loadingIndicator = document.getElementById('loadingIndicator');
    loadingIndicator.style.display = 'block'; // Mostrar indicador de carga

    const handlePDFDisplay = () => {
        if (descargaAutorizada) {
            window.open(pdfUrl, '_blank');
        } else {
            const pdfModal = document.getElementById('pdfModal');
            if (typeof bootstrap !== 'undefined') {
                const modal = new bootstrap.Modal(pdfModal);
                modal.show();
            } else {
                pdfModal.style.display = 'block';
            }
            
            pdfjsLib.getDocument(pdfUrl).promise
                .then(function(pdf) {
                    pdfDoc = pdf;
                    document.getElementById('pageCount').textContent = pdf.numPages;
                    pageNum = 1;
                    renderPage(pageNum);
                })
                .catch(function(error) {
                    console.error('Error loading PDF:', error);
                    alert('Error al cargar el PDF. Por favor, intente nuevamente.');
                })
                .finally(() => {
                    loadingIndicator.style.display = 'none'; // Ocultar indicador de carga
                });
        }
    };

    registrarVisita(libroId)
        .then(() => {
            handlePDFDisplay();
        })
        .catch((error) => {
            console.error('Error registering visit:', error);
            handlePDFDisplay();
        });
}

// Controles de zoom
document.getElementById('zoomIn').onclick = function() {
    if (zoomLevel < 3) { // Limitar el zoom máximo
        zoomLevel *= 1.2;
        document.getElementById('zoomLevel').textContent = Math.round(zoomLevel * 100) + '%';
        renderPage(pageNum);
    }
};

document.getElementById('zoomOut').onclick = function() {
    if (zoomLevel > 0.5) { // Limitar el zoom mínimo
        zoomLevel /= 1.2;
        document.getElementById('zoomLevel').textContent = Math.round(zoomLevel * 100) + '%';
        renderPage(pageNum);
    }
};

// Navegación de páginas
document.getElementById('prevPage').onclick = function() {
    if (pageNum <= 1) return;
    pageNum--;
    renderPage(pageNum);
};

document.getElementById('nextPage').onclick = function() {
    if (pageNum >= pdfDoc.numPages) return;
    pageNum++;
    renderPage(pageNum);
};

// Soporte para navegación con teclado
document.addEventListener('keydown', function(e) {
    if (!$('#pdfModal').is(':visible')) return;
    
    switch(e.key) {
        case 'ArrowLeft':
            document.getElementById('prevPage').click();
            break;
        case 'ArrowRight':
            document.getElementById('nextPage').click();
            break;
        case '+':
            document.getElementById('zoomIn').click();
            break;
        case '-':
            document.getElementById('zoomOut').click();
            break;
    }
});

// Cerrar modal
$('.close').click(function() {
  $('#pdfModal').modal('hide');
});

function toggleFilters() {
  const sidebar = document.querySelector('.sidebar-filters');
  const overlay = document.querySelector('.sidebar-overlay');
  
  sidebar.classList.toggle('active');
  overlay.classList.toggle('active');
  
}

// Cerrar sidebar al cambiar el tamaño de la ventana
window.addEventListener('resize', function() {
  if (window.innerWidth >= 768) {
    const sidebar = document.querySelector('.sidebar-filters');
    const overlay = document.querySelector('.sidebar-overlay');
    sidebar.classList.remove('active');
    overlay.classList.remove('active');
    document.body.style.overflow = '';
  }
});

const filterSections = document.querySelector('.filter-sections');
let isDown = false;
let startX;
let scrollLeft;

filterSections.addEventListener('mousedown', (e) => {
  isDown = true;
  filterSections.style.cursor = 'grabbing';
  startX = e.pageX - filterSections.offsetLeft;
  scrollLeft = filterSections.scrollLeft;
});

filterSections.addEventListener('mouseleave', () => {
  isDown = false;
  filterSections.style.cursor = 'grab';
});

filterSections.addEventListener('mouseup', () => {
  isDown = false;
  filterSections.style.cursor = 'grab';
});

filterSections.addEventListener('mousemove', (e) => {
  if(!isDown) return;
  e.preventDefault();
  const x = e.pageX - filterSections.offsetLeft;
  const walk = (x - startX) * 2; // Velocidad del scroll
  filterSections.scrollLeft = scrollLeft - walk;
});

/* Agregar JavaScript para el buscador */
document.getElementById('searchInput').addEventListener('input', function(e) {
  const searchTerm = e.target.value.toLowerCase();
  const items = document.querySelectorAll('.filter-item'); // Seleccionar los elementos de los filtros
  
  items.forEach(item => {
    const title = item.querySelector('span').textContent.toLowerCase(); // Obtener el texto del filtro
    if (title.includes(searchTerm)) {
      item.style.display = 'flex'; // Mostrar el filtro si coincide
    } else {
      item.style.display = 'none'; // Ocultar el filtro si no coincide
    }
  });
});

// Función de búsqueda para el sidebar
document.addEventListener('DOMContentLoaded', function() {
    const searchInput = document.getElementById('searchInput');
    const filterSections = document.getElementById('filterSections');

    function calculateSimilarity(str1, str2) {
        str1 = str1.toLowerCase();
        str2 = str2.toLowerCase();
        
        // Coincidencia exacta tiene prioridad máxima
        if (str1.includes(str2)) {
            return 1;
        }
        
        // Coincidencia por palabras
        const words1 = str1.split(/\s+/);
        const words2 = str2.split(/\s+/);
        
        // Si alguna palabra coincide exactamente
        for (const word2 of words2) {
            if (word2.length > 2) { // Solo considerar palabras de más de 2 letras
                for (const word1 of words1) {
                    if (word1.includes(word2)) {
                        return 0.9; // Alta similitud para coincidencias de palabras
                    }
                }
            }
        }
        
        // Si no hay coincidencias exactas, buscar coincidencias parciales
        let maxSimilarity = 0;
        for (const word2 of words2) {
            if (word2.length > 2) { // Solo considerar palabras de más de 2 letras
                for (const word1 of words1) {
                    // Calcular cuántos caracteres coinciden en secuencia
                    let matchLength = 0;
                    let consecutiveMatches = 0;
                    let maxConsecutiveMatches = 0;
                    
                    for (let i = 0; i < word1.length; i++) {
                        if (word2.includes(word1.substring(i, i + 3))) {
                            consecutiveMatches += 3;
                            maxConsecutiveMatches = Math.max(maxConsecutiveMatches, consecutiveMatches);
                        } else {
                            consecutiveMatches = 0;
                        }
                    }
                    
                    const similarity = maxConsecutiveMatches / Math.max(word1.length, word2.length);
                    maxSimilarity = Math.max(maxSimilarity, similarity);
                }
            }
        }
        
        // Solo retornar similitud si es significativa
        return maxSimilarity > 0.7 ? maxSimilarity : 0;
    }

    if (searchInput) {
        searchInput.addEventListener('input', function(e) {
            const searchTerm = e.target.value.toLowerCase().trim();
            
            if (filterSections) {
                const sections = filterSections.getElementsByClassName('filter-section');
                
                Array.from(sections).forEach(section => {
                    const sectionType = section.getAttribute('data-section-type');
                    const filterItems = section.getElementsByClassName('filter-item');
                    const filterContent = section.querySelector('.filter-content');
                    
                    if (searchTerm === '') {
                        // Mostrar todos los elementos cuando no hay búsqueda
                        Array.from(filterItems).forEach(item => {
                            item.style.display = '';
                            item.style.order = 0;
                        });
                        filterContent.style.display = '';
                    } else {
                        // Array para almacenar elementos y sus puntuaciones
                        const itemScores = [];
                        
                        Array.from(filterItems).forEach(item => {
                            const itemText = item.querySelector('span')?.textContent || '';
                            let similarity = calculateSimilarity(itemText, searchTerm);
                            
                            // Ajustar el umbral de similitud según el tipo de sección
                            const threshold = 0.7; // Umbral más alto para todos los tipos
                            
                            if (similarity >= threshold) {
                                itemScores.push({ item, similarity });
                            }
                        });
                        
                        // Ordenar por similitud
                        itemScores.sort((a, b) => b.similarity - a.similarity);
                        
                        // Ocultar todos los elementos primero
                        Array.from(filterItems).forEach(item => {
                            item.style.display = 'none';
                            item.style.order = 999;
                        });
                        
                        // Mostrar solo los elementos con puntuación suficiente
                        itemScores.forEach(({item, similarity}, index) => {
                            item.style.display = '';
                            item.style.order = index;
                        });
                        
                        // Mostrar/ocultar el contenido de la sección
                        filterContent.style.display = itemScores.length > 0 ? '' : 'none';
                    }
                    
                    // El título de la sección siempre visible
                    const sectionHeader = section.querySelector('.filter-header');
                    if (sectionHeader) {
                        sectionHeader.style.display = '';
                    }
                });
            }
        });

        // Limpiar búsqueda
        const clearButton = document.getElementById('clearFilters');
        if (clearButton) {
            clearButton.addEventListener('click', function() {
                searchInput.value = '';
                searchInput.dispatchEvent(new Event('input'));
            });
        }
    }
});