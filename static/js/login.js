// Validação do formulário
document.getElementById('loginForm').addEventListener('submit', async function (e) {
    e.preventDefault();

    const login = document.getElementById('login').value;
    const password = document.getElementById('password').value;
    const loginButton = document.getElementById('loginButton');
    const buttonText = loginButton.querySelector('.button-text');
    const spinner = document.getElementById('spinner');
    const messageDiv = document.getElementById('message');

    // Reset estados
    messageDiv.className = 'message hidden';
    messageDiv.textContent = '';

    // Validação básica
    if (!login || !password) {
        showMessage('Por favor, preencha todos os campos obrigatórios.', 'error');
        return;
    }

    // Validação do formato do login (first_name.last_name)
    const loginRegex = /^[a-zA-Z]+\.[a-zA-Z]+$/;
    if (!loginRegex.test(login)) {
        showMessage('Por favor, insira um login válido no formato: primeiro_nome.ultimo_nome', 'error');
        return;
    }

    // Mostrar loading
    loginButton.disabled = true;
    buttonText.textContent = 'Entrando...';
    spinner.classList.remove('hidden');

    try {
        const response = await fetch('/login/ajax/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCSRFToken()
            },
            body: JSON.stringify({
                login: login,
                password: password
            })
        });

        const data = await response.json();

        if (data.success) {
            showMessage(data.message, 'success');
            // Redirecionamento será feito pela rota
            window.location.href = data.redirect_url;
        } else {
            showMessage(data.message, 'error');
        }

    } catch (error) {
        console.error('Erro:', error);
        showMessage('Erro de conexão. Tente novamente.', 'error');
    } finally {
        // Restaurar botão
        loginButton.disabled = false;
        buttonText.textContent = 'Entrar';
        spinner.classList.add('hidden');
    }
});

// Função para obter o token CSRF
function getCSRFToken() {
    const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]');
    return csrfToken ? csrfToken.value : '';
}

// Função para mostrar mensagens
function showMessage(message, type) {
    const messageDiv = document.getElementById('message');
    messageDiv.textContent = message;
    messageDiv.className = `message ${type}`;
}

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