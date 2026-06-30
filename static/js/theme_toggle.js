(function () {
    const storageKey = 'agrogestor-theme';
    const root = document.documentElement;

    function preferredTheme() {
        const saved = localStorage.getItem(storageKey);
        if (saved === 'dark' || saved === 'light') return saved;
        return window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
    }

    function applyTheme(theme) {
        root.setAttribute('data-theme', theme);
        localStorage.setItem(storageKey, theme);
        document.querySelectorAll('[data-theme-toggle]').forEach(button => {
            const isDark = theme === 'dark';
            button.setAttribute('aria-label', isDark ? 'Ativar tema claro' : 'Ativar tema escuro');
            button.setAttribute('title', isDark ? 'Tema claro' : 'Tema escuro');
            button.innerHTML = isDark ? '<i class="fas fa-sun"></i>' : '<i class="fas fa-moon"></i>';
        });
    }

    applyTheme(preferredTheme());

    document.addEventListener('DOMContentLoaded', () => {
        applyTheme(root.getAttribute('data-theme') || preferredTheme());
        document.querySelectorAll('[data-theme-toggle]').forEach(button => {
            button.addEventListener('click', () => {
                applyTheme(root.getAttribute('data-theme') === 'dark' ? 'light' : 'dark');
            });
        });
    });
})();

