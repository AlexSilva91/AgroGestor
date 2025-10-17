// Scroll suave para as seções
document.querySelectorAll('nav a, .auth-buttons a').forEach(anchor => {
    anchor.addEventListener('click', function (e) {
        e.preventDefault();

        const targetId = this.getAttribute('href');
        if (targetId.startsWith('#')) {
            const targetElement = document.querySelector(targetId);
            if (targetElement) {
                window.scrollTo({
                    top: targetElement.offsetTop - 80,
                    behavior: 'smooth'
                });
            }
        }
    });
});

// Botão de login no header
document.getElementById('loginBtn').addEventListener('click', function () {
    document.getElementById('login').scrollIntoView({
        behavior: 'smooth'
    });
});

// Validação do formulário de login
document.getElementById('loginForm').addEventListener('submit', function (e) {
    e.preventDefault();

    const email = document.getElementById('email').value;
    const password = document.getElementById('password').value;

    // Validação básica
    if (email && password) {
        // Aqui você implementaria a lógica de autenticação
        alert('Login realizado com sucesso! Redirecionando para o sistema...');
        // Redirecionar para o sistema principal
        // window.location.href = 'sistema.html';
    } else {
        alert('Por favor, preencha todos os campos.');
    }
});

// Botão de cadastro
document.getElementById('registerBtn').addEventListener('click', function () {
    alert('Funcionalidade de cadastro será implementada em breve!');
});

// Link para cadastro no formulário de login
document.getElementById('showRegister').addEventListener('click', function (e) {
    e.preventDefault();
    alert('Funcionalidade de cadastro será implementada em breve!');
});

// Efeito de destaque no header ao rolar
window.addEventListener('scroll', function () {
    const header = document.querySelector('header');
    if (window.scrollY > 100) {
        header.style.boxShadow = '0 4px 10px rgba(0, 0, 0, 0.1)';
    } else {
        header.style.boxShadow = 'var(--shadow)';
    }
});