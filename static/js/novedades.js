// Variables globales para el visor de PDF
let pdfDoc = null;
let pageNum = 1;
let pageRendering = false;
let pageNumPending = null;
let scale = 1.0;
let canvas = document.getElementById('pdfViewer');
let ctx = canvas?.getContext('2d');

// Función para renderizar una página del PDF
function renderPage(num) {
    if (!pdfDoc) return;
    pageRendering = true;
    
    pdfDoc.getPage(num).then(function(page) {
        const viewport = page.getViewport({scale: scale});
        canvas.height = viewport.height;
        canvas.width = viewport.width;

        const renderContext = {
            canvasContext: ctx,
            viewport: viewport
        };

        const renderTask = page.render(renderContext);

        renderTask.promise.then(function() {
            pageRendering = false;
            if (pageNumPending !== null) {
                renderPage(pageNumPending);
                pageNumPending = null;
            }
            document.getElementById('pageNum').textContent = num;
        });
    });
}

// Función para obtener cookies
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

// Función para registrar visitas
function registrarVisita(libroId) {
    const csrftoken = getCookie('csrftoken');
    
    fetch('/registrar_visita/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrftoken,
        },
        body: JSON.stringify({
            libro_id: libroId
        })
    })
    .then(response => response.json())
    .then(data => {
        console.log('Visita registrada:', data);
    })
    .catch(error => {
        console.error('Error al registrar visita:', error);
    });
}

// Función para manejar la visualización de PDFs
function manejarPDF(pdfUrl, libroId, descargaAutorizada) {
    registrarVisita(libroId);
    
    if (descargaAutorizada) {
        window.open(pdfUrl, '_blank');
    } else {
        const loadingTask = pdfjsLib.getDocument(pdfUrl);
        
        loadingTask.promise.then(function(pdf) {
            pdfDoc = pdf;
            document.getElementById('pageCount').textContent = pdf.numPages;
            
            // Mostrar el modal
            const pdfModal = new bootstrap.Modal(document.getElementById('pdfModal'));
            pdfModal.show();
            
            // Inicializar el canvas si no se ha hecho
            if (!canvas) {
                canvas = document.getElementById('pdfViewer');
                ctx = canvas.getContext('2d');
            }
            
            // Renderizar la primera página
            renderPage(pageNum);
        });
    }
}

// Event Listeners para controles de zoom
document.getElementById('zoomIn')?.addEventListener('click', function() {
    scale *= 1.2;
    renderPage(pageNum);
});

document.getElementById('zoomOut')?.addEventListener('click', function() {
    scale /= 1.2;
    renderPage(pageNum);
});

// Event Listeners para navegación de páginas
document.getElementById('prev')?.addEventListener('click', function() {
    if (pageNum <= 1) return;
    pageNum--;
    renderPage(pageNum);
});

document.getElementById('next')?.addEventListener('click', function() {
    if (pageNum >= pdfDoc?.numPages) return;
    pageNum++;
    renderPage(pageNum);
});

// Soporte para navegación con teclado
document.addEventListener('keydown', function(e) {
    if (!document.getElementById('pdfModal')?.classList.contains('show')) return;
    
    switch(e.key) {
        case 'ArrowLeft':
            if (pageNum > 1) {
                pageNum--;
                renderPage(pageNum);
            }
            break;
        case 'ArrowRight':
            if (pageNum < pdfDoc?.numPages) {
                pageNum++;
                renderPage(pageNum);
            }
            break;
        case '+':
            scale *= 1.2;
            renderPage(pageNum);
            break;
        case '-':
            scale /= 1.2;
            renderPage(pageNum);
            break;
    }
});

// Función para alternar filtros en móvil
function toggleFilters() {
    const sidebar = document.querySelector('.sidebar-filters');
    sidebar.classList.toggle('show');
}

// Cerrar sidebar al cambiar el tamaño de la ventana
window.addEventListener('resize', function() {
    if (window.innerWidth >= 768) {
        const sidebar = document.querySelector('.sidebar-filters');
        sidebar.classList.remove('show');
    }
});

// Búsqueda en tiempo real
document.getElementById('searchInput')?.addEventListener('input', function(e) {
    const searchTerm = e.target.value.toLowerCase();
    const items = document.querySelectorAll('.book-item');
    
    items.forEach(item => {
        const title = item.querySelector('.card-title')?.textContent.toLowerCase() || '';
        const author = item.querySelector('.card-text')?.textContent.toLowerCase() || '';
        
        if (title.includes(searchTerm) || author.includes(searchTerm)) {
            item.style.display = '';
        } else {
            item.style.display = 'none';
        }
    });
});
