document.addEventListener('DOMContentLoaded', () => {
    if (!document.getElementById('modulosFazendaTable')) return;
    carregarModulosFazenda();
    carregarAcessosFazenda();
    carregarLogsAuditoria();
    carregarBackupConfig();
    document.getElementById('novaFazendaForm')?.addEventListener('submit', criarFazendaComAdmin);
    document.getElementById('salvarModulosFazenda')?.addEventListener('click', salvarModulosFazenda);
    document.getElementById('backupConfigForm')?.addEventListener('submit', salvarBackupConfig);
    document.getElementById('executarBackupManual')?.addEventListener('click', executarBackupManual);
});

function cfgFarmQuery() {
    const farmId = window.AGROGESTOR_CONTEXT?.activeFarmId;
    return farmId ? `?farm_id=${farmId}` : '';
}

function cfgAuditQuery() {
    if (window.AGROGESTOR_CONTEXT?.isSuperAdmin) return '';
    return cfgFarmQuery();
}

async function cfgJson(url, options = {}) {
    const response = await fetch(url, options);
    const data = await response.json();
    if (!response.ok || data.success === false) throw new Error(data.error || 'Erro na operação.');
    return data;
}

function cfgDate(value) {
    if (!value) return '-';
    return new Date(value).toLocaleString('pt-BR');
}

async function carregarModulosFazenda() {
    try {
        const data = await cfgJson(`/api/fazendas/modulos/${cfgFarmQuery()}`);
        const tbody = document.querySelector('#modulosFazendaTable tbody');
        tbody.innerHTML = data.modulos.map(m => `
            <tr>
                <td>${m.nome}</td>
                <td>${m.descricao || '-'}</td>
                <td><input type="checkbox" class="modulo-check" value="${m.codigo}" ${m.liberado ? 'checked' : ''}></td>
            </tr>
        `).join('');
    } catch (error) {
        console.warn(error.message);
    }
}

async function salvarModulosFazenda() {
    try {
        const modulos = Array.from(document.querySelectorAll('.modulo-check:checked')).map(input => input.value);
        await cfgJson('/api/fazendas/modulos/salvar/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]')?.value || ''
            },
            body: JSON.stringify({ farm_id: window.AGROGESTOR_CONTEXT?.activeFarmId, modulos })
        });
        alert('Módulos salvos.');
    } catch (error) {
        alert(error.message);
    }
}

async function carregarAcessosFazenda() {
    try {
        const data = await cfgJson(`/api/fazendas/acessos/${cfgFarmQuery()}`);
        const tbody = document.querySelector('#acessosFazendaTable tbody');
        tbody.innerHTML = data.acessos.map(a => `
            <tr data-acesso="${a.id}">
                <td>${a.usuario}<br><small>${a.email}</small></td>
                <td>
                    <select data-field="perfil">
                        <option value="ADMIN" ${a.perfil === 'ADMIN' ? 'selected' : ''}>Admin</option>
                        <option value="OPERADOR" ${a.perfil === 'OPERADOR' ? 'selected' : ''}>Operador</option>
                        <option value="VETERINARIO" ${a.perfil === 'VETERINARIO' ? 'selected' : ''}>Veterinário</option>
                        <option value="CONSULTOR" ${a.perfil === 'CONSULTOR' ? 'selected' : ''}>Consultor</option>
                    </select>
                </td>
                ${cfgModuloPermissao(a, 'gestao')}
                ${cfgModuloPermissao(a, 'manejo')}
                ${cfgModuloPermissao(a, 'nutricao')}
                ${cfgModuloPermissao(a, 'sanidade')}
                ${cfgModuloPermissao(a, 'producao')}
                ${cfgModuloPermissao(a, 'financeiro')}
                <td><button type="button" class="btn btn-primary btn-sm" onclick="salvarAcessoFazenda('${a.id}')">Salvar</button></td>
            </tr>
        `).join('');
    } catch (error) {
        console.warn(error.message);
    }
}

function cfgModuloPermissao(acesso, modulo) {
    return `
        <td>
            <label><input type="checkbox" data-field="can_view_${modulo}" ${acesso[`can_view_${modulo}`] ? 'checked' : ''}> Ver</label>
            <label><input type="checkbox" data-field="can_create_${modulo}" ${acesso[`can_create_${modulo}`] ? 'checked' : ''}> Criar</label>
            <label><input type="checkbox" data-field="can_update_${modulo}" ${acesso[`can_update_${modulo}`] ? 'checked' : ''}> Editar</label>
            <label><input type="checkbox" data-field="can_delete_${modulo}" ${acesso[`can_delete_${modulo}`] ? 'checked' : ''}> Excluir</label>
        </td>
    `;
}

async function salvarAcessoFazenda(id) {
    const row = document.querySelector(`[data-acesso="${id}"]`);
    const payload = {};
    row.querySelectorAll('[data-field]').forEach(input => {
        payload[input.dataset.field] = input.type === 'checkbox' ? input.checked : input.value;
    });
    try {
        await cfgJson(`/api/fazendas/acessos/${id}/editar/`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]')?.value || ''
            },
            body: JSON.stringify(payload)
        });
        alert('Permissões salvas.');
    } catch (error) {
        alert(error.message);
    }
}

async function carregarLogsAuditoria() {
    try {
        const data = await cfgJson(`/api/auditoria/logs/${cfgAuditQuery()}`);
        const tbody = document.querySelector('#auditoriaTable tbody');
        if (!tbody) return;
        tbody.innerHTML = data.logs.map(log => `
            <tr>
                <td>${cfgDate(log.data_hora)}</td>
                <td>${log.usuario || '-'}</td>
                <td>${log.farm || '-'}</td>
                <td><span class="badge badge-secondary">${log.acao}</span></td>
                <td>${log.descricao || '-'}</td>
                <td>${log.metodo || ''} ${log.caminho || ''}</td>
                <td>${log.status_code || '-'}</td>
                <td>${log.ip || '-'}</td>
            </tr>
        `).join('');
    } catch (error) {
        console.warn(error.message);
    }
}

async function criarFazendaComAdmin(event) {
    event.preventDefault();
    const form = event.target;
    const payload = {};
    new FormData(form).forEach((value, key) => {
        payload[key] = String(value || '').trim();
    });

    try {
        const data = await cfgJson('/api/fazendas/criar-com-admin/', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        alert(`Fazenda cadastrada: ${data.farm.nome}. Admin: ${data.admin.email}.`);
        form.reset();
        window.location.reload();
    } catch (error) {
        alert(error.message);
    }
}

async function carregarBackupConfig() {
    try {
        const data = await cfgJson(`/api/backups/config/${cfgFarmQuery()}`);
        const config = data.config;
        document.getElementById('backupAtivo').checked = !!config.ativo;
        document.getElementById('backupFrequencia').value = config.frequencia || 'DIARIO';
        document.getElementById('backupHora').value = config.hora_execucao || '02:00';
        document.getElementById('backupDestino').value = config.destino || 'backups';
        document.getElementById('backupManter').value = config.manter_ultimos || 7;
        renderBackupExecucoes(data.execucoes || []);
    } catch (error) {
        console.warn(error.message);
    }
}

function renderBackupExecucoes(execucoes) {
    const tbody = document.querySelector('#backupExecucoesTable tbody');
    if (!tbody) return;
    tbody.innerHTML = execucoes.map(item => `
        <tr>
            <td>${cfgDate(item.iniciado_em)}</td>
            <td><span class="badge ${item.status === 'SUCESSO' ? 'badge-success' : 'badge-danger'}">${item.status}</span></td>
            <td>${item.arquivo || '-'}</td>
            <td>${item.mensagem || '-'}</td>
        </tr>
    `).join('');
}

async function salvarBackupConfig(event) {
    event.preventDefault();
    try {
        await cfgJson('/api/backups/config/', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                farm_id: window.AGROGESTOR_CONTEXT?.activeFarmId,
                ativo: document.getElementById('backupAtivo').checked,
                frequencia: document.getElementById('backupFrequencia').value,
                hora_execucao: document.getElementById('backupHora').value,
                destino: document.getElementById('backupDestino').value,
                manter_ultimos: document.getElementById('backupManter').value
            })
        });
        alert('Configuração de backup salva.');
        carregarBackupConfig();
    } catch (error) {
        alert(error.message);
    }
}

async function executarBackupManual() {
    try {
        const data = await cfgJson('/api/backups/executar/', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ farm_id: window.AGROGESTOR_CONTEXT?.activeFarmId })
        });
        alert(data.mensagem || 'Backup executado.');
        carregarBackupConfig();
    } catch (error) {
        alert(error.message);
    }
}
