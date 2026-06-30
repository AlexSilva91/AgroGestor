(function () {
    const select = document.getElementById('activeFarmSelect');
    if (!select) return;

    window.AGROGESTOR_CONTEXT = window.AGROGESTOR_CONTEXT || {};
    window.AGROGESTOR_CONTEXT.activeFarmId = select.value || null;

    select.addEventListener('change', async function () {
        const farmId = this.value;
        try {
            const response = await fetch('/api/fazendas/ativa/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]')?.value || ''
                },
                body: JSON.stringify({ farm_id: farmId })
            });
            const data = await response.json();
            if (!data.success) {
                alert(data.error || 'Erro ao trocar fazenda ativa.');
                return;
            }
            window.AGROGESTOR_CONTEXT.activeFarmId = data.active_farm_id;
            window.location.reload();
        } catch (error) {
            alert('Erro ao trocar fazenda ativa.');
        }
    });
})();

