document.addEventListener('DOMContentLoaded', () => {
    if (!document.getElementById('gestao-integrada')) return;
    initializeGestaoIntegrada();
});

const giState = {
    culturas: [],
    instalacoes: [],
    planteis: [],
    protocolos: [],
    formulas: [],
    finalidades: [],
};

function giFarmId() {
    return window.AGROGESTOR_CONTEXT?.activeFarmId || '';
}

function giHeaders() {
    return {
        'Content-Type': 'application/json',
        'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]')?.value || ''
    };
}

function giToday() {
    return new Date().toISOString().slice(0, 10);
}

async function giFetchJson(url, options = {}) {
    const response = await fetch(url, options);
    const data = await response.json();
    if (!response.ok || data.success === false) {
        throw new Error(data.error || 'Erro na operação.');
    }
    return data;
}

async function initializeGestaoIntegrada() {
    document.querySelectorAll('#gestao-integrada input[type="date"]').forEach(input => {
        if (!input.value) input.value = giToday();
    });

    await giCarregarBase();
    giBindForms();
    await giAtualizarDashboard();
    await giAtualizarRelatorio();
}

async function giCarregarBase() {
    const suffix = giFarmId() ? `?farm_id=${giFarmId()}` : '';
    const [culturas, instalacoes, planteis, protocolos, formulas, finalidades] = await Promise.all([
        giFetchJson('/gestao/culturas/'),
        giFetchJson(`/gestao/instalacoes/${suffix}`),
        giFetchJson(`/gestao/planteis/${suffix}`),
        giFetchJson('/gestao/protocolos/'),
        giFetchJson(`/gestao/formulas-racao/${suffix}`),
        fetch('/gestao/finalidades/').then(r => r.ok ? r.json() : []),
    ]);

    giState.culturas = culturas;
    giState.instalacoes = instalacoes;
    giState.planteis = planteis;
    giState.protocolos = protocolos;
    giState.formulas = formulas;
    giState.finalidades = Array.isArray(finalidades) ? finalidades : [];
    giRenderSelects();
}

function giOptions(items, labelField = 'nome') {
    return '<option value="">Selecione</option>' + items.map(item => (
        `<option value="${item.id}">${item[labelField] || item.codigo || item.id}</option>`
    )).join('');
}

function giRenderSelects() {
    document.querySelectorAll('.gi-culturas').forEach(select => {
        select.innerHTML = giOptions(giState.culturas);
    });
    document.querySelectorAll('.gi-planteis').forEach(select => {
        select.innerHTML = giOptions(giState.planteis, 'codigo');
    });
    document.getElementById('giInstalacoes').innerHTML = giOptions(giState.instalacoes);
    document.getElementById('giProtocolos').innerHTML = giOptions(giState.protocolos);
    document.getElementById('giFormulas').innerHTML = giOptions(giState.formulas);
    const finalidade = document.getElementById('giFinalidade');
    if (finalidade) finalidade.innerHTML = giOptions(giState.finalidades);
}

function giFormPayload(form) {
    const payload = { farm_id: giFarmId() };
    new FormData(form).forEach((value, key) => {
        if (value !== '') payload[key] = value;
    });
    return payload;
}

function giBindForms() {
    giBindJsonForm('giInstalacaoForm', '/gestao/instalacoes/criar/');
    giBindJsonForm('giPlantelForm', '/gestao/planteis/criar/', giCalcularCapacidade, giPlantelSubmitOptions);
    giBindJsonForm('giProtocoloForm', '/gestao/manejo/aplicar-protocolo/');
    giBindJsonForm('giConsumoRacaoForm', '/gestao/nutricao/consumo-racao/');
    giBindJsonForm('giOcorrenciaForm', '/gestao/ocorrencias-sanitarias/criar/');
    giBindJsonForm('giProducaoOvosForm', '/gestao/producao-ovos/criar/');

    document.getElementById('giPlantelForm')?.addEventListener('input', giCalcularCapacidade);
}

function giPlantelSubmitOptions(form) {
    if (!form.dataset.editingId) return null;
    return {
        url: `/gestao/planteis/${form.dataset.editingId}/editar/`,
        method: 'PUT',
        successMessage: 'Plantel atualizado com sucesso.'
    };
}

function giBindJsonForm(formId, url, beforeSubmit = null, optionsFactory = null) {
    const form = document.getElementById(formId);
    if (!form) return;
    form.addEventListener('submit', async (event) => {
        event.preventDefault();
        try {
            if (beforeSubmit) await beforeSubmit();
            const options = optionsFactory ? optionsFactory(form) : null;
            await giFetchJson(options?.url || url, {
                method: options?.method || 'POST',
                headers: giHeaders(),
                body: JSON.stringify(giFormPayload(form))
            });
            form.reset();
            delete form.dataset.editingId;
            const submitButton = form.querySelector('button[type="submit"]');
            if (formId === 'giPlantelForm' && submitButton) submitButton.textContent = 'Salvar Plantel';
            form.querySelectorAll('input[type="date"]').forEach(input => input.value = giToday());
            await giCarregarBase();
            await giAtualizarDashboard();
            await giAtualizarRelatorio();
            alert(options?.successMessage || 'Operação realizada com sucesso.');
        } catch (error) {
            alert(error.message);
        }
    });
}

async function giCalcularCapacidade() {
    const form = document.getElementById('giPlantelForm');
    const box = document.getElementById('giCapacidade');
    if (!form || !box || !form.instalacao.value || !form.quantidade_atual.value) return;
    try {
        const params = new URLSearchParams({
            farm_id: giFarmId(),
            instalacao: form.instalacao.value,
            cultura: form.cultura.value,
            finalidade: form.finalidade.value,
            quantidade: form.quantidade_atual.value,
        });
        const data = await giFetchJson(`/gestao/capacidade/calcular/?${params}`);
        box.className = `message ${data.superlotado ? 'error' : 'success'}`;
        box.textContent = `Capacidade recomendada: ${data.capacidade_recomendada || '-'} | Quantidade: ${data.quantidade} | Excedente: ${data.excedente}`;
    } catch (error) {
        box.className = 'message error';
        box.textContent = error.message;
    }
}

async function giAtualizarDashboard() {
    try {
        const params = giFarmId() ? `?farm_id=${giFarmId()}` : '';
        const data = await giFetchJson(`/gestao/dashboard-operacional/${params}`);
        document.getElementById('giPlanteis').textContent = data.planteis_ativos;
        document.getElementById('giPendentes').textContent = data.tarefas_pendentes;
        document.getElementById('giAtrasadas').textContent = data.tarefas_atrasadas;
        document.getElementById('giSanidade').textContent = data.ocorrencias_abertas;
        document.getElementById('giOvos').textContent = data.producoes_ovos_hoje;
    } catch (error) {
        console.warn(error.message);
    }
}

async function giAtualizarRelatorio() {
    try {
        const params = giFarmId() ? `?farm_id=${giFarmId()}` : '';
        const data = await giFetchJson(`/gestao/relatorios/plantel/${params}`);
        const tbody = document.querySelector('#giRelatorioTable tbody');
        tbody.innerHTML = data.map(row => `
            <tr>
                <td>${row.codigo} - ${row.nome}</td>
                <td>${row.cultura}</td>
                <td>${row.quantidade_atual}</td>
                <td>R$ ${Number(row.receita).toFixed(2)}</td>
                <td>R$ ${Number(row.custo).toFixed(2)}</td>
                <td>R$ ${Number(row.lucro).toFixed(2)}</td>
                <td>${row.ovos_total}</td>
                <td>${Number(row.consumo_racao_kg).toFixed(3)}</td>
                <td class="actions">
                    <button type="button" class="btn btn-secondary btn-sm" onclick="giDetalharPlantel('${row.plantel_id}')">Detalhes</button>
                    <button type="button" class="btn btn-primary btn-sm" onclick="giEditarPlantel('${row.plantel_id}')">Editar</button>
                </td>
            </tr>
        `).join('');
    } catch (error) {
        console.warn(error.message);
    }
}

async function giDetalharPlantel(id) {
    try {
        const plantel = await giFetchJson(`/gestao/planteis/${id}/${giFarmId() ? `?farm_id=${giFarmId()}` : ''}`);
        const cultura = giState.culturas.find(item => item.id === plantel.cultura)?.nome || plantel.cultura || '-';
        const instalacao = giState.instalacoes.find(item => item.id === plantel.instalacao)?.nome || plantel.instalacao || '-';
        const body = document.getElementById('giPlantelDetalhesBody');
        body.innerHTML = `
            ${giDetailItem('Código', plantel.codigo)}
            ${giDetailItem('Nome', plantel.nome)}
            ${giDetailItem('Cultura', cultura)}
            ${giDetailItem('Instalação', instalacao)}
            ${giDetailItem('Data de alojamento', plantel.data_alojamento)}
            ${giDetailItem('Quantidade inicial', plantel.quantidade_inicial)}
            ${giDetailItem('Quantidade atual', plantel.quantidade_atual)}
            ${giDetailItem('Status', plantel.status)}
            ${giDetailItem('Origem', plantel.origem || '-')}
            ${giDetailItem('Observações', plantel.observacoes || '-')}
        `;
        document.getElementById('giPlantelDetalhes').style.display = 'flex';
    } catch (error) {
        alert(error.message);
    }
}

function giDetailItem(label, value) {
    return `<div class="details-item"><span>${label}</span><strong>${value || '-'}</strong></div>`;
}

function giFecharDetalhesPlantel() {
    document.getElementById('giPlantelDetalhes').style.display = 'none';
}

async function giEditarPlantel(id) {
    try {
        const plantel = await giFetchJson(`/gestao/planteis/${id}/${giFarmId() ? `?farm_id=${giFarmId()}` : ''}`);
        const form = document.getElementById('giPlantelForm');
        form.dataset.editingId = id;
        ['codigo', 'nome', 'cultura', 'finalidade', 'instalacao', 'data_alojamento', 'quantidade_inicial', 'quantidade_atual'].forEach(field => {
            if (form.elements[field]) form.elements[field].value = plantel[field] || '';
        });
        const submitButton = form.querySelector('button[type="submit"]');
        if (submitButton) submitButton.textContent = 'Atualizar Plantel';
        form.scrollIntoView({ behavior: 'smooth', block: 'center' });
    } catch (error) {
        alert(error.message);
    }
}
