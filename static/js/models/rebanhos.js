// =======================
// FUNÇÃO TOAST
// =======================
function mostrarMensagem(msg, tipo = 'info') {
    const toast = document.createElement('div');
    toast.style.cssText = `
        position: fixed; top: 20px; right: 20px;
        background: ${tipo === 'success' ? '#28a745' : tipo === 'error' ? '#dc3545' : '#17a2b8'};
        color: white; padding: 12px 20px; border-radius: 4px;
        z-index:10000; box-shadow:0 4px 6px rgba(0,0,0,0.1);
        max-width: 300px; font-family: Arial, sans-serif;
        opacity: 0; transform: translateY(-20px);
        transition: opacity 0.4s ease, transform 0.4s ease;
    `;
    toast.textContent = msg;
    document.body.appendChild(toast);

    requestAnimationFrame(() => {
        toast.style.opacity = '1';
        toast.style.transform = 'translateY(0)';
    });

    setTimeout(() => {
        toast.style.opacity = '0';
        toast.style.transform = 'translateY(-20px)';
        toast.addEventListener('transitionend', () => {
            if (toast.parentNode) document.body.removeChild(toast);
        });
    }, 4000);
}

// =======================
// VARIÁVEIS GLOBAIS
// =======================
let rebanhosCache = [];
let rebanhoAtualId = null;
let rebanhosPaginaAtual = 1;
const rebanhosPorPagina = 10;

// =======================
// INICIALIZAÇÃO
// =======================
document.addEventListener('DOMContentLoaded', () => {
    if (document.getElementById('rebanhos')) {
        initializeRebanhos();
    }

    // Fechar modais clicando fora do conteúdo
    document.addEventListener('click', e => {
        document.querySelectorAll('.modal.active').forEach(modal => {
            if (e.target === modal) fecharModal(modal.id);
        });
    });

    // Fechar modais com ESC
    document.addEventListener('keydown', e => {
        if (e.key === "Escape") {
            document.querySelectorAll('.modal.active').forEach(modal => fecharModal(modal.id));
        }
    });

    // Fechar modais via botão cancelar
    document.addEventListener('click', e => {
        const btnCancelar = e.target.closest('.btn-cancelar[data-modal]');
        if (btnCancelar) fecharModal(btnCancelar.dataset.modal);
    });
});

// =======================
// MODAIS
// =======================
function abrirModal(modalId) {
    const modal = document.getElementById(modalId);
    if (!modal) return;
    modal.style.display = 'flex';
    modal.classList.add('active');
    document.body.style.overflow = 'hidden';
}

function fecharModal(modalId) {
    const modal = document.getElementById(modalId);
    if (!modal) return;
    modal.style.display = 'none';
    modal.classList.remove('active');
    document.body.style.overflow = 'auto';
    if (modalId === 'rebanhoModal') {
        document.getElementById('rebanhoForm')?.reset();
        rebanhoAtualId = null;
    }
}

// =======================
// INICIALIZAÇÃO CRUD
// =======================
function initializeRebanhos() {
    carregarRebanhos();

    document.getElementById('addRebanho')?.addEventListener('click', () => {
        rebanhoAtualId = null;
        document.getElementById('rebanhoModalTitle').textContent = 'Novo Rebanho';
        document.getElementById('rebanhoForm')?.reset();
        abrirModal('rebanhoModal');
    });

    document.getElementById('rebanhoForm')?.addEventListener('submit', salvarRebanho);

    // Delegação para editar/excluir
    document.querySelector('#rebanhosTable tbody')?.addEventListener('click', e => {
        const btnEditar = e.target.closest('.btn-editar');
        const btnExcluir = e.target.closest('.btn-excluir');
        if (btnEditar) editarRebanho(btnEditar.dataset.rebanhoId);
        if (btnExcluir) solicitarExclusaoRebanho(btnExcluir.dataset.rebanhoId);
    });

    document.getElementById('confirmDeleteRebanhoBtn')?.addEventListener('click', confirmarExclusaoRebanho);
}

// =======================
// CRUD
// =======================
async function editarRebanho(id) {
    try {
        const res = await fetch(`/rebanho/rebanhos/${id}/`);
        if (!res.ok) throw new Error('Erro ao carregar dados do rebanho');
        const r = await res.json();

        document.getElementById('rebanho_id').value = r.id;
        document.getElementById('nome').value = r.nome_lote || '';
        document.getElementById('capacidade').value = r.capacidade || '';
        document.getElementById('status').value = r.ativo ? 'ativo' : 'inativo';
        document.getElementById('pastagem').value = r.pastagem_id || '';
        document.getElementById('descricao').value = r.descricao || '';

        rebanhoAtualId = id;
        document.getElementById('rebanhoModalTitle').textContent = 'Editar Rebanho';
        abrirModal('rebanhoModal');
    } catch (err) {
        console.error(err);
        mostrarMensagem('Erro ao carregar rebanho', 'error');
    }
}

function solicitarExclusaoRebanho(id) {
    rebanhoAtualId = id;
    abrirModal('confirmDeleteRebanho');
}

async function confirmarExclusaoRebanho() {
    if (!rebanhoAtualId) return;
    try {
        const res = await fetch(`/rebanho/rebanhos/${rebanhoAtualId}/excluir/`, {
            method: 'DELETE',
            headers: { 'X-CSRFToken': getCSRFToken() }
        });
        const data = await res.json();
        if (data.success) {
            fecharModal('confirmDeleteRebanho');
            mostrarMensagem('Rebanho excluído com sucesso', 'success');
            carregarRebanhos(rebanhosPaginaAtual);
        } else {
            mostrarMensagem(data.error || 'Erro ao excluir rebanho', 'error');
        }
    } catch (err) {
        console.error(err);
        mostrarMensagem('Erro ao excluir rebanho', 'error');
    }
}

async function salvarRebanho(e) {
    e.preventDefault();
    const form = document.getElementById('rebanhoForm');

    const dados = {
        nome_lote: form.nome.value.trim(),
        capacidade: parseInt(form.capacidade.value),
        ativo: form.status.value === 'ativo',
        pastagem_id: form.pastagem.value || null,
        descricao: form.descricao.value.trim()
    };

    try {
        const url = rebanhoAtualId
            ? `/rebanho/rebanhos/${rebanhoAtualId}/editar/`
            : '/rebanho/rebanhos/criar/';
        const method = rebanhoAtualId ? 'PUT' : 'POST';

        const res = await fetch(url, {
            method,
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCSRFToken()
            },
            body: JSON.stringify(dados)
        });
        const result = await res.json();

        if (result.success) {
            fecharModal('rebanhoModal');
            mostrarMensagem('Rebanho salvo com sucesso', 'success');
            carregarRebanhos(rebanhosPaginaAtual);
        } else {
            mostrarMensagem(result.error || 'Erro ao salvar rebanho', 'error');
        }
    } catch (err) {
        console.error(err);
        mostrarMensagem('Erro ao salvar rebanho', 'error');
    }
}

// =======================
// LISTAGEM E PAGINAÇÃO
// =======================
async function carregarRebanhos(pagina = 1) {
    try {
        const res = await fetch('/rebanho/rebanhos/');
        if (!res.ok) throw new Error('Erro ao carregar rebanhos');
        rebanhosCache = await res.json();
        rebanhosPaginaAtual = pagina;

        const start = (pagina - 1) * rebanhosPorPagina;
        const end = pagina * rebanhosPorPagina;
        renderizarTabelaRebanhos(rebanhosCache.slice(start, end));
        renderizarPaginacao(rebanhosCache.length, pagina);
    } catch (err) {
        console.error(err);
        mostrarMensagem('Erro ao carregar rebanhos', 'error');
    }
}

function renderizarTabelaRebanhos(rebanhos) {
    const tbody = document.querySelector('#rebanhosTable tbody');
    if (!tbody) return;

    if (!rebanhos.length) {
        tbody.innerHTML = `
            <tr>
                <td colspan="4" class="text-center">
                    <div class="empty-state">
                        <i class="fas fa-users fa-3x"></i>
                        <h3>Nenhum rebanho encontrado</h3>
                        <p>Clique em "Novo Rebanho" para adicionar.</p>
                    </div>
                </td>
            </tr>
        `;
        return;
    }

    tbody.innerHTML = rebanhos.map(r => `
        <tr>
            <td>${r.nome_lote}</td>
            <td>${r.capacidade} animais</td>
            <td><span class="badge ${r.ativo ? 'badge-success' : 'badge-secondary'}">${r.ativo ? 'Ativo' : 'Inativo'}</span></td>
            <td>
                <button class="btn btn-secondary btn-sm btn-editar" data-rebanho-id="${r.id}">
                    <i class="fas fa-edit"></i>
                </button>
                <button class="btn btn-danger btn-sm btn-excluir" data-rebanho-id="${r.id}">
                    <i class="fas fa-trash"></i>
                </button>
            </td>
        </tr>
    `).join('');
}

function renderizarPaginacao(totalItems, paginaAtual) {
    const totalPaginas = Math.ceil(totalItems / rebanhosPorPagina);
    const paginacaoContainer = document.getElementById('paginacaoRebanhos');
    if (!paginacaoContainer) return;
    if (totalPaginas <= 1) {
        paginacaoContainer.innerHTML = '';
        return;
    }

    const maxBtn = 5;
    let startPage = Math.max(1, paginaAtual - Math.floor(maxBtn / 2));
    let endPage = Math.min(totalPaginas, startPage + maxBtn - 1);
    if (endPage - startPage + 1 < maxBtn) startPage = Math.max(1, endPage - maxBtn + 1);

    let html = `<button class="page-btn" data-page="${paginaAtual - 1}" ${paginaAtual === 1 ? 'disabled' : ''}>&laquo;</button>`;
    for (let i = startPage; i <= endPage; i++) {
        html += `<button class="page-btn ${i === paginaAtual ? 'active' : ''}" data-page="${i}">${i}</button>`;
    }
    html += `<button class="page-btn" data-page="${paginaAtual + 1}" ${paginaAtual === totalPaginas ? 'disabled' : ''}>&raquo;</button>`;

    paginacaoContainer.innerHTML = html;
    paginacaoContainer.querySelectorAll('.page-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            const page = parseInt(btn.dataset.page);
            if (page >= 1 && page <= totalPaginas) carregarRebanhos(page);
        });
    });
}

// =======================
// CSRF
// =======================
function getCSRFToken() {
    const token = document.querySelector('[name=csrfmiddlewaretoken]');
    return token ? token.value : '';
}
