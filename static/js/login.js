// Validação do formulário
document.getElementById('loginForm').addEventListener('submit', async function (e) {
    e.preventDefault();

    const email = document.getElementById('email').value.trim();
    const password = document.getElementById('password').value;
    const loginButton = document.getElementById('loginButton');
    const buttonText = loginButton.querySelector('.button-text');
    const spinner = document.getElementById('spinner');
    const messageDiv = document.getElementById('message');

    // Reset estados
    messageDiv.className = 'message hidden';
    messageDiv.textContent = '';

    // Validação básica
    if (!email || !password) {
        showMessage('Por favor, preencha todos os campos obrigatórios.', 'error');
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
                email: email,
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
