document.addEventListener('DOMContentLoaded', function () {
    initializeDashboard();
});

function initializeDashboard() {
    applyModuleVisibility();

    document.querySelectorAll('.tab').forEach(tab => {
        tab.addEventListener('click', () => {
            activatePage('dashboard');
            activateTab(tab.getAttribute('data-tab'));
        });
    });

    document.querySelectorAll('nav a').forEach(link => {
        link.addEventListener('click', (e) => {
            e.preventDefault();
            const pageId = link.getAttribute('data-page');
            activatePage(pageId);
            if (pageId === 'dashboard') {
                activateDashboardOverview();
            }
        });
    });

    activateDashboardOverview();

    const configForm = document.getElementById('configForm');
    if (configForm) {
        configForm.addEventListener('submit', function (e) {
            e.preventDefault();
            alert('Configurações salvas com sucesso!');
        });
    }
}

function applyModuleVisibility() {
    const context = window.AGROGESTOR_CONTEXT || {};
    if (context.isSuperAdmin) return;

    const allowedModules = new Set(context.modulosLiberados || []);
    document.querySelectorAll('.tab[data-module]').forEach(tab => {
        const moduleCode = tab.dataset.module;
        const shouldShow = !moduleCode || moduleCode === 'usuarios' || allowedModules.has(moduleCode);
        tab.hidden = !shouldShow;

        const content = document.getElementById(tab.dataset.tab);
        if (content) {
            content.hidden = !shouldShow;
        }
    });
}

function activatePage(pageId) {
    const page = document.getElementById(pageId);
    const link = document.querySelector(`nav a[data-page="${pageId}"]`);
    if (!page || !link) return;

    document.querySelectorAll('.page-content').forEach(content => content.classList.remove('active'));
    document.querySelectorAll('nav a').forEach(navLink => navLink.classList.remove('active'));

    page.classList.add('active');
    link.classList.add('active');
    setNavTheme(pageId);

    if (pageId !== 'dashboard') {
        setDashboardWorkspace(false);
    }
}

function activateTab(tabId) {
    const tab = document.querySelector(`.tab[data-tab="${tabId}"]`);
    const content = document.getElementById(tabId);
    if (!tab || !content || tab.hidden || content.hidden) return;

    document.querySelectorAll('.tab').forEach(item => item.classList.remove('active'));
    document.querySelectorAll('.tab-content').forEach(item => item.classList.remove('active'));
    document.querySelectorAll('nav a').forEach(navLink => navLink.classList.remove('active'));

    tab.classList.add('active');
    content.classList.add('active');
    setNavTheme(tabId);
    setDashboardWorkspace(true);
    setDashboardOverview(false);
}

function activateDashboardOverview() {
    document.querySelectorAll('.tab').forEach(item => item.classList.remove('active'));
    document.querySelectorAll('.tab-content').forEach(item => item.classList.remove('active'));
    document.querySelector('nav a[data-page="dashboard"]')?.classList.add('active');
    setNavTheme('dashboard');
    setDashboardWorkspace(false);
    setDashboardOverview(true);
}

function setDashboardOverview(visible) {
    const overview = document.querySelector('.analytics-dashboard');
    if (overview) {
        overview.hidden = !visible;
    }
}

function setDashboardWorkspace(visible) {
    const workspace = document.querySelector('.dashboard-workspace');
    if (workspace) {
        workspace.hidden = !visible;
    }
}

function setNavTheme(key) {
    const themes = {
        dashboard: 'dashboard',
        lancamentos: 'financeiro',
        financeiro: 'financeiro',
        animais: 'rebanho',
        rebanhos: 'rebanho',
        pastagens: 'pastagem',
        movimentacoes: 'pastagem',
        'gestao-integrada': 'gestao',
        'manejo-operacional': 'manejo',
        'nutricao-operacional': 'nutricao',
        'sanidade-operacional': 'sanidade',
        'producao-operacional': 'producao',
        usuarios: 'usuarios',
        relatorios: 'relatorios',
        configuracoes: 'configuracoes',
        cadastros: 'cadastros',
        ajuda: 'ajuda',
        Sair: 'sair'
    };
    document.documentElement.dataset.navTheme = themes[key] || 'dashboard';
}
