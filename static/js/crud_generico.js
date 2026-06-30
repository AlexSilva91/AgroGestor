(function () {
    const state = { entity: null, fields: [], rows: [], editingId: null };

    document.addEventListener('DOMContentLoaded', initCrud);

    async function initCrud() {
        const select = document.getElementById('crudEntitySelect');
        if (!select) return;
        try {
            const schema = await crudJson('/api/crud/');
            select.innerHTML = schema.entities.map(item => `<option value="${item.key}">${item.label}</option>`).join('');
            select.addEventListener('change', () => loadEntity(select.value));
            document.getElementById('crudNewBtn')?.addEventListener('click', () => showForm());
            document.getElementById('crudForm')?.addEventListener('submit', saveCrud);
            if (schema.entities[0]) loadEntity(schema.entities[0].key);
        } catch (error) {
            console.warn(error.message);
        }
    }

    async function crudJson(url, options = {}) {
        const response = await fetch(url, options);
        const data = await response.json();
        if (!response.ok || data.success === false) throw new Error(data.error || 'Erro na operação.');
        return data;
    }

    async function loadEntity(entity) {
        state.entity = entity;
        state.editingId = null;
        const data = await crudJson(`/api/crud/${entity}/`);
        state.fields = data.fields;
        state.rows = data.rows;
        document.getElementById('crudTitle').textContent = data.label;
        document.getElementById('crudSubtitle').textContent = `${data.rows.length} registro(s) carregado(s).`;
        document.getElementById('crudFormPanel').hidden = true;
        document.getElementById('crudDetailPanel').hidden = true;
        renderTable();
    }

    function renderTable() {
        const table = document.getElementById('crudTable');
        const visibleFields = state.fields.slice(0, 6);
        table.querySelector('thead').innerHTML = `
            <tr>
                <th>Registro</th>
                ${visibleFields.map(field => `<th>${field.label}</th>`).join('')}
                <th>Ações</th>
            </tr>
        `;
        table.querySelector('tbody').innerHTML = state.rows.map(row => `
            <tr>
                <td>${escapeHtml(row.display)}</td>
                ${visibleFields.map(field => `<td>${formatValue(row.data[field.name])}</td>`).join('')}
                <td class="actions">
                    <button type="button" class="btn btn-secondary btn-sm" onclick="crudDetail('${row.id}')">Detalhes</button>
                    <button type="button" class="btn btn-primary btn-sm" onclick="crudEdit('${row.id}')">Editar</button>
                    <button type="button" class="btn btn-danger btn-sm" onclick="crudDelete('${row.id}')">Excluir</button>
                </td>
            </tr>
        `).join('');
    }

    function showForm(row = null) {
        state.editingId = row?.id || null;
        const panel = document.getElementById('crudFormPanel');
        const form = document.getElementById('crudForm');
        document.getElementById('crudFormTitle').textContent = row ? 'Editar Registro' : 'Novo Registro';
        panel.hidden = false;
        form.innerHTML = state.fields.map(field => renderField(field, row?.data?.[field.name])).join('') + `
            <div class="form-actions">
                <button type="button" class="btn btn-secondary" onclick="crudCancelForm()">Cancelar</button>
                <button type="submit" class="btn btn-primary">Salvar</button>
            </div>
        `;
        panel.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }

    function renderField(field, value) {
        const val = value ?? '';
        if (field.type === 'checkbox') {
            return `<label class="crud-check"><input type="checkbox" name="${field.name}" ${val ? 'checked' : ''}> ${field.label}</label>`;
        }
        if (field.type === 'textarea') {
            return `<div class="form-group"><label>${field.label}</label><textarea name="${field.name}">${escapeHtml(val)}</textarea></div>`;
        }
        if (field.type === 'select') {
            return `<div class="form-group"><label>${field.label}</label><select name="${field.name}"><option value="">Selecione</option>${field.choices.map(choice => `<option value="${choice.value}" ${String(choice.value) === String(val) ? 'selected' : ''}>${choice.label}</option>`).join('')}</select></div>`;
        }
        return `<div class="form-group"><label>${field.label}</label><input type="${field.type === 'relation' ? 'text' : field.type}" name="${field.name}" value="${escapeHtml(val)}" placeholder="${field.type === 'relation' ? 'ID do registro relacionado' : ''}"></div>`;
    }

    async function saveCrud(event) {
        event.preventDefault();
        const payload = {};
        const form = event.target;
        state.fields.forEach(field => {
            const input = form.elements[field.name];
            if (!input) return;
            payload[field.name] = input.type === 'checkbox' ? input.checked : input.value;
        });
        const url = state.editingId ? `/api/crud/${state.entity}/${state.editingId}/editar/` : `/api/crud/${state.entity}/criar/`;
        const method = state.editingId ? 'PUT' : 'POST';
        await crudJson(url, {
            method,
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload),
        });
        await loadEntity(state.entity);
    }

    window.crudDetail = async function (id) {
        const data = await crudJson(`/api/crud/${state.entity}/${id}/`);
        const body = document.getElementById('crudDetailBody');
        body.innerHTML = Object.entries(data.data).map(([key, value]) => `
            <div class="details-item"><span>${key}</span><strong>${formatValue(value)}</strong></div>
        `).join('');
        document.getElementById('crudDetailPanel').hidden = false;
    };

    window.crudEdit = function (id) {
        const row = state.rows.find(item => String(item.id) === String(id));
        if (row) showForm(row);
    };

    window.crudDelete = async function (id) {
        if (!confirm('Excluir este registro?')) return;
        await crudJson(`/api/crud/${state.entity}/${id}/excluir/`, { method: 'DELETE' });
        await loadEntity(state.entity);
    };

    window.crudCancelForm = function () {
        document.getElementById('crudFormPanel').hidden = true;
        state.editingId = null;
    };

    function formatValue(value) {
        if (value === null || value === undefined || value === '') return '-';
        if (typeof value === 'boolean') return value ? 'Sim' : 'Não';
        return escapeHtml(String(value));
    }

    function escapeHtml(value) {
        return String(value ?? '').replace(/[&<>"']/g, char => ({
            '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#039;'
        }[char]));
    }
})();
