let pastagemAtualId = null;
let pastagensCache = [];
let pastagensPaginaAtual = 1;
const pastagensPorPagina = 15;

document.addEventListener('DOMContentLoaded', function () {
    const pastagensContainer = document.getElementById('pastagens');
    if (pastagensContainer) initializePastagens();

    document.addEventListener('click', (e) => {
        document.querySelectorAll('.modal.active').forEach(modal => {
            if (e.target === modal) fecharModal(modal.id);
        });
    });

    document.addEventListener('keydown', (e) => {
        if (e.key === "Escape") {
            document.querySelectorAll('.modal.active').forEach(m => fecharModal(m.id));
        }
    });

    document.addEventListener('click', (e) => {
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
    if (modalId === 'pastagemModal') {
        document.getElementById('pastagemForm')?.reset();
        pastagemAtualId = null;
    }
}

// =======================
// CRUD
// =======================
function initializePastagens() {
    carregarPastagens();
    document.getElementById('addPastagem')?.addEventListener('click', abrirModalNovaPastagem);
    document.getElementById('pastagemForm')?.addEventListener('submit', salvarPastagem);
    document.getElementById('confirmDeletePastagemBtn')?.addEventListener('click', confirmarExclusaoPastagem);

    const tbody = document.querySelector('#pastagensTable tbody');
    if (tbody) {
        tbody.addEventListener('click', (e) => {
            const editarBtn = e.target.closest('.btn-editar');
            const excluirBtn = e.target.closest('.btn-excluir');
            if (editarBtn) editarPastagem(editarBtn.dataset.pastagemId);
            if (excluirBtn) solicitarExclusaoPastagem(excluirBtn.dataset.pastagemId);
        });
    }
}

function abrirModalNovaPastagem() {
    pastagemAtualId = null;
    document.getElementById('pastagemModalTitle').textContent = 'Nova Pastagem';
    document.getElementById('pastagemForm')?.reset();
    abrirModal('pastagemModal');
}

async function editarPastagem(id) {
    try {
        const res = await fetch(`/pastagem/pastagens/${id}/`);
        if (!res.ok) throw new Error('Erro ao carregar pastagem');
        const pastagem = await res.json();

        pastagemAtualId = id;
        document.getElementById('pastagem_id').value = pastagem.id;
        document.getElementById('nome').value = pastagem.nome;
        document.getElementById('area').value = pastagem.area || '';
        document.getElementById('capacidade').value = pastagem.capacidade_suporte || '';
        document.getElementById('status').value = pastagem.ativo;

        document.getElementById('pastagemModalTitle').textContent = 'Editar Pastagem';
        abrirModal('pastagemModal');
    } catch (err) {
        console.error(err);
        mostrarMensagem('Erro ao carregar pastagem', 'error');
    }
}

function solicitarExclusaoPastagem(id) {
    pastagemAtualId = id;
    abrirModal('confirmDeletePastagem');
}

async function confirmarExclusaoPastagem() {
    if (!pastagemAtualId) return;
    try {
        const res = await fetch(`/pastagem/pastagens/${pastagemAtualId}/excluir/`, {
            method: 'DELETE',
            headers: { 'X-CSRFToken': getCSRFToken() }
        });
        const data = await res.json();

        if (data.success) {
            fecharModal('confirmDeletePastagem');
            mostrarMensagem('Pastagem excluída com sucesso', 'success');
            carregarPastagens(pastagensPaginaAtual);
        } else {
            mostrarMensagem(data.error || 'Erro ao excluir pastagem', 'error');
        }
    } catch (err) {
        console.error(err);
        mostrarMensagem('Erro ao excluir pastagem', 'error');
    }
}

async function salvarPastagem(e) {
    e.preventDefault();
    const form = document.getElementById('pastagemForm');
    const dados = {
        nome: form.nome.value.trim(),
        area: parseFloat(form.area.value),
        capacidade_suporte: parseInt(form.capacidade.value),
        ativo: form.status.value === 'true'
    };

    try {
        const url = pastagemAtualId
            ? `/pastagem/pastagens/${pastagemAtualId}/editar/`
            : '/pastagem/pastagens/criar/';
        const method = pastagemAtualId ? 'PUT' : 'POST';

        const res = await fetch(url, {
            method: method,
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCSRFToken()
            },
            body: JSON.stringify(dados)
        });

        const result = await res.json();
        if (result.success) {
            fecharModal('pastagemModal');
            mostrarMensagem('Pastagem salva com sucesso', 'success');
            carregarPastagens(pastagensPaginaAtual);
        } else {
            mostrarMensagem(result.error || 'Erro ao salvar pastagem', 'error');
        }
    } catch (err) {
        console.error(err);
        mostrarMensagem('Erro ao salvar pastagem', 'error');
    }
}

// =======================
// LISTAR E PAGINAÇÃO
// =======================
async function carregarPastagens(pagina = 1) {
    try {
        const res = await fetch('/pastagem/pastagens/');
        if (!res.ok) throw new Error('Erro ao carregar pastagens');
        const pastagens = await res.json();

        pastagensCache = pastagens;
        pastagensPaginaAtual = pagina;

        const start = (pagina - 1) * pastagensPorPagina;
        const end = pagina * pastagensPorPagina;

        renderizarTabelaPastagens(pastagens.slice(start, end));
        renderizarPaginacaoPastagens(pastagens.length, pagina);
    } catch (err) {
        console.error(err);
        mostrarMensagem('Erro ao carregar pastagens', 'error');
    }
}

function renderizarTabelaPastagens(pastagens) {
    const tbody = document.querySelector('#pastagensTable tbody');
    if (!tbody) return;

    if (!pastagens.length) {
        tbody.innerHTML = `
            <tr>
                <td colspan="5" class="text-center">
                    <div class="empty-state">
                        <i class="fas fa-seedling fa-3x"></i>
                        <h3>Nenhuma pastagem encontrada</h3>
                        <p>Clique em "Nova Pastagem" para adicionar.</p>
                    </div>
                </td>
            </tr>
        `;
        return;
    }

    tbody.innerHTML = pastagens.map(p => `
        <tr>
            <td>${p.nome}</td>
            <td>${p.area || '-'}</td>
            <td>${p.capacidade_suporte || '-'}</td>
            <td><span class="badge ${p.ativo ? 'badge-success' : 'badge-secondary'}">${p.ativo ? 'Disponível' : 'Indisponível'}</span></td>
            <td>
                <button class="btn btn-secondary btn-sm btn-editar" data-pastagem-id="${p.id}"><i class="fas fa-edit"></i></button>
                <button class="btn btn-danger btn-sm btn-excluir" data-pastagem-id="${p.id}"><i class="fas fa-trash"></i></button>
            </td>
        </tr>
    `).join('');
}

function renderizarPaginacaoPastagens(totalItems, paginaAtual) {
    const totalPaginas = Math.ceil(totalItems / pastagensPorPagina);
    const paginacaoContainer = document.getElementById('paginacaoPastagens');
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
            if (page >= 1 && page <= totalPaginas) carregarPastagens(page);
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