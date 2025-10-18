// Logout functionality - Versão unificada com confirmação e animação no mesmo card
document.addEventListener('DOMContentLoaded', function() {
    initializeLogout();
});

function initializeLogout() {
    // Múltiplas formas de encontrar o link de logout
    const logoutSelectors = [
        'a[data-page="Sair"]',
        'a[data-page="sair"]',
        'a[data-page="logout"]',
        'a[data-page="perfil"]',
        '#logout-link',
        '.logout-link'
    ];
    
    let logoutLink = null;
    
    // Tenta encontrar o link usando os seletores
    for (const selector of logoutSelectors) {
        logoutLink = document.querySelector(selector);
        if (logoutLink) {
            break;
        }
    }
    
    if (logoutLink) {
        // Remove qualquer evento anterior para evitar duplicação
        logoutLink.replaceWith(logoutLink.cloneNode(true));
        logoutLink = document.querySelector(logoutSelectors[0]);
        
        logoutLink.addEventListener('click', handleLogoutClick);
        
    } else {
        console.error('Nenhum link de logout encontrado');
    }
}

function handleLogoutClick(e) {
    e.preventDefault();
    e.stopImmediatePropagation();
    
    // Mostra o card de confirmação
    showConfirmationPopup();
}

function showConfirmationPopup() {
    // Remove qualquer popup anterior
    hideLogoutPopup();
    
    // Cria o overlay no estilo do sistema
    const overlay = document.createElement('div');
    overlay.id = 'logout-overlay';
    
    // Cria o card de confirmação no estilo do sistema
    const confirmationCard = document.createElement('div');
    confirmationCard.id = 'logout-card';
    confirmationCard.className = 'glass-effect';
    confirmationCard.innerHTML = `
        <div class="logout-content">
            <div class="logout-icon">
                <i class="fas fa-sign-out-alt"></i>
            </div>
            <div class="logout-text">
                <h3>Deseja sair do sistema?</h3>
                <p>Você será redirecionado para a página de login</p>
            </div>
            <div class="logout-actions">
                <button class="btn btn-secondary" id="cancel-logout">
                    <i class="fas fa-times"></i>
                    Cancelar
                </button>
                <button class="btn btn-primary" id="confirm-logout">
                    <i class="fas fa-check"></i>
                    Confirmar
                </button>
            </div>
        </div>
    `;
    
    // Estilos do overlay (usando as variáveis CSS do sistema)
    overlay.style.cssText = `
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background: rgba(12, 31, 20, 0.95);
        backdrop-filter: blur(10px);
        display: flex;
        justify-content: center;
        align-items: center;
        z-index: 9999;
        animation: fadeIn 0.3s ease-out;
    `;
    
    // Adiciona os estilos CSS específicos para o popup
    const style = document.createElement('style');
    style.textContent = `
        @keyframes fadeIn {
            from { opacity: 0; }
            to { opacity: 1; }
        }
        
        @keyframes slideInUp {
            from {
                opacity: 0;
                transform: translateY(30px) scale(0.9);
            }
            to {
                opacity: 1;
                transform: translateY(0) scale(1);
            }
        }
        
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
        
        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.7; }
        }
        
        @keyframes contentSwitch {
            from {
                opacity: 0;
                transform: translateY(10px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }
        
        #logout-card {
            background: var(--bg-card);
            border-radius: 16px;
            padding: 3rem;
            box-shadow: 0 20px 50px rgba(0, 0, 0, 0.5);
            border: 1px solid var(--border-light);
            backdrop-filter: blur(20px);
            min-width: 380px;
            max-width: 450px;
            animation: slideInUp 0.4s ease-out;
            position: relative;
            overflow: hidden;
        }
        
        #logout-card::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 4px;
            background: var(--gradient);
        }
        
        .logout-content {
            text-align: center;
        }
        
        .logout-icon {
            margin-bottom: 1.5rem;
        }
        
        .logout-icon i {
            font-size: 3.5rem;
            color: var(--secondary);
            text-shadow: 0 0 20px rgba(255, 152, 0, 0.4);
        }
        
        .logout-text h3 {
            color: var(--text-primary);
            font-size: 1.4rem;
            font-weight: 600;
            margin-bottom: 0.75rem;
        }
        
        .logout-text p {
            color: var(--text-secondary);
            font-size: 1rem;
            line-height: 1.5;
            margin-bottom: 2rem;
        }
        
        .logout-actions {
            display: flex;
            gap: 1rem;
            justify-content: center;
        }
        
        .logout-actions .btn {
            min-width: 120px;
            padding: 0.75rem 1.5rem;
            font-size: 0.95rem;
        }
        
        .logout-actions .btn i {
            margin-right: 0.5rem;
        }
        
        /* Estilos para a tela de "Saindo..." */
        .logout-processing .logout-icon i {
            animation: pulse 2s infinite ease-in-out;
        }
        
        .logout-processing .logout-text h3 {
            background: var(--gradient);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }
        
        .logout-spinner {
            display: flex;
            justify-content: center;
            margin-top: 1rem;
        }
        
        .logout-spinner .spinner {
            width: 50px;
            height: 50px;
            border: 3px solid rgba(255, 255, 255, 0.1);
            border-top: 3px solid var(--primary);
            border-radius: 50%;
            animation: spin 1s linear infinite;
            box-shadow: 0 0 15px rgba(46, 125, 50, 0.3);
        }
        
        /* Transição suave entre conteúdos */
        .logout-content > * {
            animation: contentSwitch 0.3s ease-out;
        }
        
        /* Efeitos de brilho sutil */
        #logout-card::after {
            content: '';
            position: absolute;
            top: -50%;
            left: -50%;
            width: 200%;
            height: 200%;
            background: radial-gradient(circle, rgba(46, 125, 50, 0.1) 0%, transparent 70%);
            animation: rotate 10s linear infinite;
            pointer-events: none;
        }
        
        @keyframes rotate {
            from { transform: rotate(0deg); }
            to { transform: rotate(360deg); }
        }
    `;
    
    // Adiciona tudo ao documento
    document.head.appendChild(style);
    overlay.appendChild(confirmationCard);
    document.body.appendChild(overlay);
    
    // Previne scroll do body
    document.body.style.overflow = 'hidden';
    
    // Adiciona event listeners aos botões
    document.getElementById('cancel-logout').addEventListener('click', function() {
        hideLogoutPopup();
    });
    
    document.getElementById('confirm-logout').addEventListener('click', function() {
        // Troca para a tela de "Saindo..."
        switchToProcessingScreen();
        // Inicia o processo de logout
        performLogout();
    });
    
    // Fecha ao clicar no overlay (fora do card)
    overlay.addEventListener('click', function(e) {
        if (e.target === overlay) {
            hideLogoutPopup();
        }
    });
}

function switchToProcessingScreen() {
    const logoutCard = document.getElementById('logout-card');
    const logoutContent = logoutCard.querySelector('.logout-content');
    
    // Atualiza o conteúdo para a tela de processamento
    logoutContent.innerHTML = `
        <div class="logout-icon">
            <i class="fas fa-sign-out-alt"></i>
        </div>
        <div class="logout-text">
            <h3>Saindo do sistema...</h3>
            <p>Redirecionando para a página de login</p>
        </div>
        <div class="logout-spinner">
            <div class="spinner"></div>
        </div>
    `;
    
    // Adiciona classe para estilos específicos do processamento
    logoutCard.classList.add('logout-processing');
}

function performLogout() {
    fetch('/dashboard/logout/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCSRFToken(),
            'X-Requested-With': 'XMLHttpRequest'
        },
        credentials: 'same-origin'
    })
    .then(response => {
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        return response.json();
    })
    .then(data => {
        // Redireciona após um breve delay para mostrar a mensagem
        setTimeout(() => {
            window.location.href = data.redirect_url || '/';
        }, 1500);
    })
    .catch(error => {
        // Fallback - redireciona mesmo com erro
        setTimeout(() => {
            window.location.href = '/';
        }, 1500);
    });
}

function getCSRFToken() {
    // Tenta várias formas de encontrar o token CSRF
    const csrfToken = 
        document.querySelector('[name=csrfmiddlewaretoken]') ||
        document.querySelector('input[name="csrfmiddlewaretoken"]') ||
        document.querySelector('[name="csrfmiddlewaretoken"]');
    
    return csrfToken ? csrfToken.value : '';
}

function hideLogoutPopup() {
    const overlay = document.getElementById('logout-overlay');
    const style = document.querySelector('style');
    
    if (overlay) {
        // Animação de saída suave
        overlay.style.animation = 'fadeOut 0.3s ease-out';
        setTimeout(() => {
            if (overlay.parentNode) {
                overlay.remove();
            }
        }, 300);
    }
    
    // Remove o estilo específico se existir
    if (style && style.textContent.includes('logout-card')) {
        style.remove();
    }
    
    // Restaura scroll do body
    document.body.style.overflow = '';
}

// Adiciona keyframes para fadeOut se não existirem
if (!document.querySelector('style[data-fadeout]')) {
    const fadeOutStyle = document.createElement('style');
    fadeOutStyle.setAttribute('data-fadeout', 'true');
    fadeOutStyle.textContent = `
        @keyframes fadeOut {
            from { opacity: 1; }
            to { opacity: 0; }
        }
    `;
    document.head.appendChild(fadeOutStyle);
}