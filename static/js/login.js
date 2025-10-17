// Validação do formulário
document.getElementById('loginForm').addEventListener('submit', function (e) {
    e.preventDefault();

    const login = document.getElementById('login').value;
    const password = document.getElementById('password').value;

    if (!login || !password) {
        alert('Por favor, preencha todos os campos obrigatórios.');
        return;
    }

    // Validação do formato do login (first_name.last_name)
    const loginRegex = /^[a-zA-Z]+\.+[a-zA-Z]+$/;
    if (!loginRegex.test(login)) {
        alert('Por favor, insira um login válido no formato: primeiro_nome.ultimo_nome');
        return;
    }

    // Aqui seria feita a validação com o backend
    console.log('Tentativa de login:', { login, password });

    // Simulação de login bem-sucedido
    alert('Login realizado com sucesso! Redirecionando...');
    // window.location.href = 'dashboard.html';
});

// Efeito de foco nos campos
const inputs = document.querySelectorAll('input');
inputs.forEach(input => {
    input.addEventListener('focus', function () {
        this.parentElement.style.transform = 'scale(1.02)';
    });

    input.addEventListener('blur', function () {
        this.parentElement.style.transform = 'scale(1)';
    });
});

// Formatação automática do campo de login
document.getElementById('login').addEventListener('input', function (e) {
    let value = e.target.value.toLowerCase();
    // Remove caracteres especiais, mantendo apenas letras e ponto
    value = value.replace(/[^a-zA-Z.]/g, '');
    // Garante que há apenas um ponto
    const parts = value.split('.');
    if (parts.length > 2) {
        value = parts[0] + '.' + parts.slice(1).join('');
    }
    e.target.value = value;
});