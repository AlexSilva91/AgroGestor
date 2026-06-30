(function () {
    if (!window.fetch) return;

    const originalFetch = window.fetch.bind(window);
    const writeMethods = new Set(['POST', 'PUT', 'PATCH', 'DELETE']);

    function getCookie(name) {
        const value = `; ${document.cookie}`;
        const parts = value.split(`; ${name}=`);
        if (parts.length === 2) return parts.pop().split(';').shift();
        return '';
    }

    function csrfToken() {
        return (
            document.querySelector('[name=csrfmiddlewaretoken]')?.value ||
            getCookie('csrftoken') ||
            ''
        );
    }

    function isSameOrigin(input) {
        const url = typeof input === 'string' ? input : input?.url;
        if (!url) return true;
        try {
            return new URL(url, window.location.origin).origin === window.location.origin;
        } catch (_) {
            return true;
        }
    }

    window.fetch = function (input, init = {}) {
        const method = (init.method || input?.method || 'GET').toUpperCase();
        const headers = new Headers(init.headers || input?.headers || {});

        if (writeMethods.has(method) && isSameOrigin(input) && !headers.has('X-CSRFToken')) {
            headers.set('X-CSRFToken', csrfToken());
        }

        return originalFetch(input, {
            credentials: 'same-origin',
            ...init,
            headers,
        });
    };
})();
