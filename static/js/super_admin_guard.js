(function () {
    const context = window.AGROGESTOR_CONTEXT || {};
    if (!context.isSuperAdmin || !window.fetch) return;

    const originalFetch = window.fetch.bind(window);
    const writeMethods = new Set(['POST', 'PUT', 'PATCH', 'DELETE']);

    window.fetch = function (input, init = {}) {
        const method = (init.method || (input && input.method) || 'GET').toUpperCase();
        if (!writeMethods.has(method)) {
            return originalFetch(input, init);
        }

        const confirmed = window.confirm(
            'Atenção: você está como SUPER ADMIN e esta ação pode alterar dados de uma fazenda. Deseja continuar?'
        );
        if (!confirmed) {
            return Promise.reject(new Error('Ação cancelada pelo super admin.'));
        }

        const headers = new Headers(init.headers || (input && input.headers) || {});
        headers.set('X-Super-Admin-Confirm', '1');

        return originalFetch(input, {
            ...init,
            headers,
        });
    };
})();

