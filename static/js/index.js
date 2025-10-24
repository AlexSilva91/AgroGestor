// Elementos DOM específicos do dashboard
const tabs = document.querySelectorAll('.tab');
const tabContents = document.querySelectorAll('.tab-content');
const navLinks = document.querySelectorAll('nav a');
const pageContents = document.querySelectorAll('.page-content');

// Inicialização do Dashboard
document.addEventListener('DOMContentLoaded', function () {
    initializeDashboard();
});

function initializeDashboard() {
    // Configurar eventos de tabs
    tabs.forEach(tab => {
        tab.addEventListener('click', () => {
            const tabId = tab.getAttribute('data-tab');
            activateTab(tabId);
        });
    });

    // Configurar eventos de navegação
    navLinks.forEach(link => {
        link.addEventListener('click', (e) => {
            e.preventDefault();
            const pageId = link.getAttribute('data-page');
            activatePage(pageId);
        });
    });

    // Configurar formulário de configurações
    const configForm = document.getElementById('configForm');
    if (configForm) {
        configForm.addEventListener('submit', function (e) {
            e.preventDefault();
            alert('Configurações salvas com sucesso!');
        });
    }
}

// Funções de controle de páginas e tabs
function activatePage(pageId) {
    pageContents.forEach(content => content.classList.remove('active'));
    navLinks.forEach(link => link.classList.remove('active'));

    document.getElementById(pageId).classList.add('active');
    document.querySelector(`nav a[data-page="${pageId}"]`).classList.add('active');
}

function activateTab(tabId) {
    tabs.forEach(tab => tab.classList.remove('active'));
    tabContents.forEach(content => content.classList.remove('active'));

    document.querySelector(`.tab[data-tab="${tabId}"]`).classList.add('active');
    document.getElementById(tabId).classList.add('active');
}
