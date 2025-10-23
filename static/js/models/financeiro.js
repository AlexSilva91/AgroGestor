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
    }, 5000);
}

// =======================
// JS FINANCEIRO ISOLADO
// =======================
document.addEventListener('DOMContentLoaded', function () {
    const lancamentosContainer = document.getElementById('lancamentos');
    if (lancamentosContainer) {
        initializeFinanceiro();
    }
});

let lancamentoAtualId = null;
let lancamentosCache = [];
let lancamentosPaginaAtual = 1;
const lancamentosPorPagina = 15;

function initializeFinanceiro() {
    carregarLancamentos();

    const addBtn = document.getElementById('addLancamento');
    if (addBtn) addBtn.addEventListener('click', abrirModalNovoLancamento);

    const form = document.getElementById('lancamentoForm');
    if (form) form.addEventListener('submit', salvarLancamento);

    const confirmDeleteBtn = document.getElementById('confirmDeleteLancamentoBtn');
    if (confirmDeleteBtn) confirmDeleteBtn.addEventListener('click', confirmarExclusaoLancamento);

    const tbody = document.querySelector('#lancamentosTable tbody');
    if (tbody) {
        tbody.addEventListener('click', function (e) {
            const editarBtn = e.target.closest('.btn-editar');
            const excluirBtn = e.target.closest('.btn-excluir');
            if (editarBtn) editarLancamento(editarBtn.dataset.lancamentoId);
            if (excluirBtn) solicitarExclusaoLancamento(excluirBtn.dataset.lancamentoId);
        });
    }

    document.addEventListener('click', function (e) {
        const closeBtn = e.target.closest('.close-btn, .btn-secondary[data-modal]');
        if (closeBtn && closeBtn.dataset.modal) {
            e.preventDefault();
            fecharModalLancamento(closeBtn.dataset.modal);
        }

        document.querySelectorAll('.modal.active').forEach(modal => {
            if (e.target === modal) fecharModalLancamento(modal.id);
        });
    });

    document.addEventListener('keydown', function (e) {
        if (e.key === 'Escape') {
            document.querySelectorAll('.modal.active').forEach(modal => fecharModalLancamento(modal.id));
        }
    });
}

// =======================
// MODAIS
// =======================
function abrirModalLancamento(modalId) {
    const modal = document.getElementById(modalId);
    if (!modal) return;
    modal.style.display = 'flex';
    modal.classList.add('active');
    document.body.style.overflow = 'hidden';
}

function fecharModalLancamento(modalId) {
    const modal = document.getElementById(modalId);
    if (!modal) return;
    modal.style.display = 'none';
    modal.classList.remove('active');
    document.body.style.overflow = 'auto';
    if (modalId === 'lancamentoModal') {
        document.getElementById('lancamentoForm')?.reset();
        lancamentoAtualId = null;
    }
}

// =======================
// CRUD
// =======================
function abrirModalNovoLancamento() {
    lancamentoAtualId = null;
    document.getElementById('lancamentoModalTitle').textContent = 'Novo Lançamento';
    document.getElementById('lancamentoForm')?.reset();
    document.getElementById('lancamento_id').value = '';
    document.getElementById('data').value = new Date().toISOString().split('T')[0];
    abrirModalLancamento('lancamentoModal');
}

async function editarLancamento(id) {
    try {
        const res = await fetch(`/financeiro/lancamentos/${id}/`);
        if (!res.ok) throw new Error('Erro ao carregar lançamento');
        const lancamento = await res.json();

        document.getElementById('lancamento_id').value = lancamento.id;
        document.getElementById('tipo').value = lancamento.tipo;
        document.getElementById('categoria').value = lancamento.categoria;
        document.getElementById('valor').value = lancamento.valor;
        document.getElementById('data').value = lancamento.data_movimento;
        document.getElementById('animal').value = lancamento.animal || '';
        document.getElementById('descricao').value = lancamento.descricao || '';

        lancamentoAtualId = id;
        document.getElementById('lancamentoModalTitle').textContent = 'Editar Lançamento';
        abrirModalLancamento('lancamentoModal');
    } catch (err) {
        console.error(err);
        mostrarMensagem('Erro ao carregar lançamento', 'error');
    }
}

function solicitarExclusaoLancamento(id) {
    lancamentoAtualId = id;
    abrirModalLancamento('confirmDeleteLancamento');
}

async function confirmarExclusaoLancamento() {
    if (!lancamentoAtualId) return;
    try {
        const res = await fetch(`/financeiro/lancamentos/${lancamentoAtualId}/excluir/`, {
            method: 'DELETE',
            headers: { 'X-CSRFToken': getCSRFToken() }
        });
        const data = await res.json();
        if (data.success) {
            fecharModalLancamento('confirmDeleteLancamento');
            lancamentoAtualId = null;
            carregarLancamentos(lancamentosPaginaAtual);
            mostrarMensagem('Lançamento excluído com sucesso', 'success');
        } else {
            mostrarMensagem(data.error || 'Erro ao excluir lançamento', 'error');
        }
    } catch (err) {
        console.error(err);
        mostrarMensagem('Erro ao excluir lançamento', 'error');
    }
}

async function salvarLancamento(e) {
    e.preventDefault();
    const form = document.getElementById('lancamentoForm');
    const formData = new FormData(form);
    const isEdit = !!lancamentoAtualId;

    const dados = {
        tipo: formData.get('tipo'),
        categoria: formData.get('categoria'),
        valor: parseFloat(formData.get('valor')),
        data_movimento: formData.get('data'),
        animal: formData.get('animal') || null,
        descricao: formData.get('descricao') || ''
    };

    try {
        const url = isEdit
            ? `/financeiro/lancamentos/${lancamentoAtualId}/editar/`
            : '/financeiro/lancamentos/criar/';
        const method = isEdit ? 'PUT' : 'POST';

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
            fecharModalLancamento('lancamentoModal');
            lancamentoAtualId = null;
            carregarLancamentos(lancamentosPaginaAtual);
            mostrarMensagem(result.message || 'Lançamento salvo com sucesso', 'success');
        } else {
            mostrarMensagem(result.error || 'Erro ao salvar lançamento', 'error');
        }
    } catch (err) {
        console.error(err);
        mostrarMensagem('Erro ao salvar lançamento', 'error');
    }
}

// =======================
// CARREGAR TABELA COM PAGINAÇÃO
// =======================
async function carregarLancamentos(pagina = 1) {
    try {
        const res = await fetch('/financeiro/lancamentos/');
        if (!res.ok) throw new Error('Erro ao carregar lançamentos');
        const lancamentos = await res.json();

        lancamentosCache = lancamentos;
        lancamentosPaginaAtual = pagina;

        const start = (pagina - 1) * lancamentosPorPagina;
        const end = pagina * lancamentosPorPagina;

        renderizarTabela(lancamentos.slice(start, end));
        renderizarPaginacao(lancamentos.length, pagina);
    } catch (err) {
        console.error(err);
        mostrarMensagem('Erro ao carregar lançamentos', 'error');
    }
}

function renderizarTabela(lancamentos) {
    const tbody = document.querySelector('#lancamentosTable tbody');
    if (!tbody) return;

    if (!lancamentos.length) {
        tbody.innerHTML = `
            <tr>
                <td colspan="6" class="text-center">
                    <div class="empty-state">
                        <i class="fas fa-receipt fa-3x"></i>
                        <h3>Nenhum lançamento encontrado</h3>
                        <p>Clique no botão "Novo Lançamento" para adicionar o primeiro registro.</p>
                    </div>
                </td>
            </tr>
        `;
        return;
    }

    tbody.innerHTML = lancamentos.map(l => `
        <tr>
            <td><span class="badge ${l.tipo === 'receita' ? 'badge-success' : 'badge-danger'}">
                ${l.tipo === 'receita' ? 'Receita' : 'Despesa'}
            </span></td>
            <td>${l.categoria}</td>
            <td>R$ ${parseFloat(l.valor).toLocaleString('pt-BR', { minimumFractionDigits: 2 })}</td>
            <td>${l.data_movimento}</td>
            <td>${l.animal || '-'}</td>
            <td class="actions">
                <button class="btn btn-secondary btn-sm btn-editar" data-lancamento-id="${l.id}">
                    <i class="fas fa-edit"></i>
                </button>
                <button class="btn btn-danger btn-sm btn-excluir" data-lancamento-id="${l.id}">
                    <i class="fas fa-trash"></i>
                </button>
            </td>
        </tr>
    `).join('');
}

function renderizarPaginacao(totalItems, paginaAtual) {
    const totalPaginas = Math.ceil(totalItems / lancamentosPorPagina);
    const paginacaoContainer = document.getElementById('paginacaoLancamentos');
    if (!paginacaoContainer) return;

    if (totalPaginas <= 1) {
        paginacaoContainer.innerHTML = '';
        return;
    }

    const maxBtn = 5; // máximo de botões visíveis
    let startPage = Math.max(1, paginaAtual - Math.floor(maxBtn / 2));
    let endPage = Math.min(totalPaginas, startPage + maxBtn - 1);

    if (endPage - startPage + 1 < maxBtn) {
        startPage = Math.max(1, endPage - maxBtn + 1);
    }

    let html = '';

    // Botão anterior
    html += `<button class="page-btn" data-page="${paginaAtual - 1}" ${paginaAtual === 1 ? 'disabled' : ''}>
                <span class="arrow">&laquo;</span>
             </button>`;

    // Botões numéricos
    for (let i = startPage; i <= endPage; i++) {
        html += `<button class="page-btn ${i === paginaAtual ? 'active' : ''}" data-page="${i}">${i}</button>`;
    }

    // Botão próximo
    html += `<button class="page-btn" data-page="${paginaAtual + 1}" ${paginaAtual === totalPaginas ? 'disabled' : ''}>
                <span class="arrow">&raquo;</span>
             </button>`;

    paginacaoContainer.innerHTML = html;

    // Eventos dos botões
    paginacaoContainer.querySelectorAll('.page-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            const pagina = parseInt(btn.dataset.page);
            if (!isNaN(pagina) && pagina >= 1 && pagina <= totalPaginas) {
                carregarLancamentos(pagina);
            }
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
