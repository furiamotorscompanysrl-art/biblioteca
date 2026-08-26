// Efectos modernos para el login
document.addEventListener('DOMContentLoaded', function() {
    // Funciones para el manejo de contraseña y anuncio
    window.togglePasswordVisibility = function(element) {
        const input = element.parentElement.querySelector('input');
        const icon = element.querySelector('i');
        
        if (input.type === 'password') {
            input.type = 'text';
            icon.classList.remove('fa-eye');
            icon.classList.add('fa-eye-slash');
        } else {
            input.type = 'password';
            icon.classList.remove('fa-eye-slash');
            icon.classList.add('fa-eye');
        }
    };

    window.toggleAnnouncement = function() {
        const announcement = document.getElementById('announcement');
        if (announcement) {
            announcement.style.display = announcement.style.display === 'flex' ? 'none' : 'flex';
        }
    };

    // Cerrar automáticamente las alertas después de 5 segundos
    const alerts = document.querySelectorAll('.alert');
    if (alerts.length > 0) {
        setTimeout(function() {
            alerts.forEach(function(alert) {
                alert.classList.add('animate__fadeOut');
                setTimeout(function() {
                    alert.remove();
                }, 1000);
            });
        }, 5000);
    }

    // Efectos de animación para el login box
    const loginBox = document.querySelector('.login-box');
    const loginLogo = document.querySelector('.login-logo');
    const loginHeader = document.querySelector('.login-header h2');

    if (loginBox && loginLogo && loginHeader) {
        // Efecto parallax suave
        document.addEventListener('mousemove', function(e) {
            let xAxis = (window.innerWidth / 2 - e.pageX) / 50;
            let yAxis = (window.innerHeight / 2 - e.pageY) / 50;
            loginBox.style.transform = `rotateY(${xAxis}deg) rotateX(${yAxis}deg)`;
        });

        // Efecto hover
        loginBox.addEventListener('mouseenter', function() {
            loginBox.style.transition = 'none';
            if (loginLogo) loginLogo.style.transform = 'translateZ(20px)';
            if (loginHeader) loginHeader.style.transform = 'translateZ(15px)';
        });

        loginBox.addEventListener('mouseleave', function() {
            loginBox.style.transition = 'all 0.5s ease';
            loginBox.style.transform = 'rotateY(0deg) rotateX(0deg)';
            if (loginLogo) loginLogo.style.transform = 'translateZ(0px)';
            if (loginHeader) loginHeader.style.transform = 'translateZ(0px)';
        });
    }
});
