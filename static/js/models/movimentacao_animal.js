// =======================
// Variáveis
// =======================
let movimentacaoAtualId = null;
let movimentacoesCache = [];
let movimentacoesPaginaAtual = 1;
const movimentacoesPorPagina = 15;

// =======================
// Inicialização
// =======================
document.addEventListener('DOMContentLoaded', () => {
    console.log('DOM Carregado - Inicializando movimentações...');

    const movimentacoesTab = document.getElementById('movimentacoes');

    const observer = new MutationObserver(() => {
        if (movimentacoesTab && movimentacoesTab.style.display !== 'none' && !window.movimentacoesInicializadas) {
            initializeMovimentacoes();
            window.movimentacoesInicializadas = true;
        }
    });

    if (movimentacoesTab) {
        observer.observe(movimentacoesTab, { attributes: true });
        if (movimentacoesTab.style.display !== 'none') {
            initializeMovimentacoes();
            window.movimentacoesInicializadas = true;
        }
    }

    // Event listeners para modais
    document.addEventListener('click', e => {
        const modalAberto = e.target.closest('.modal.active');
        if (modalAberto && e.target === modalAberto) {
            fecharModal(modalAberto.id);
        }
    });

    document.addEventListener('keydown', e => {
        if (e.key === 'Escape') {
            document.querySelectorAll('.modal.active').forEach(m => fecharModal(m.id));
        }
    });

    document.querySelectorAll('.btn-cancelar[data-modal]').forEach(btn => {
        btn.addEventListener('click', () => {
            const modalId = btn.getAttribute('data-modal');
            if (modalId) {
                fecharModal(modalId);
            }
        });
    });
});

// =======================
// Modais
// =======================
function abrirModal(id) {
    console.log('Abrindo modal:', id);
    const modal = document.getElementById(id);
    if (!modal) {
        console.error('Modal não encontrado:', id);
        return;
    }

    modal.style.display = 'flex';
    modal.classList.add('active');
    document.body.style.overflow = 'hidden';
}

function fecharModal(id) {
    console.log('Fechando modal:', id);
    const modal = document.getElementById(id);
    if (!modal) return;
    modal.style.display = 'none';
    modal.classList.remove('active');
    document.body.style.overflow = 'auto';
    if (id === 'movimentacaoModal') {
        document.getElementById('movimentacaoForm')?.reset();
        movimentacaoAtualId = null;
    }
}

// =======================
// Inicialização CRUD
// =======================
function initializeMovimentacoes() {
    console.log('Inicializando sistema de movimentações...');

    // Carregar movimentações
    carregarMovimentacoes();

    // Configurar event listeners
    const addBtn = document.getElementById('addMovimentacao');
    if (addBtn) {
        addBtn.addEventListener('click', abrirModalNovaMovimentacao);
    }

    const form = document.getElementById('movimentacaoForm');
    if (form) {
        form.addEventListener('submit', salvarMovimentacao);
    }

    const deleteBtn = document.getElementById('confirmDeleteMovimentacaoBtn');
    if (deleteBtn) {
        deleteBtn.addEventListener('click', confirmarExclusaoMovimentacao);
    }

    const tbody = document.querySelector('#movimentacoesTable tbody');
    if (tbody) {
        tbody.addEventListener('click', e => {
            const editarBtn = e.target.closest('.btn-editar');
            const excluirBtn = e.target.closest('.btn-excluir');
            if (editarBtn) {
                editarMovimentacao(editarBtn.dataset.movId);
            }
            if (excluirBtn) {
                solicitarExclusaoMovimentacao(excluirBtn.dataset.movId);
            }
        });
    }
}

// =======================
// CRUD
// =======================
function abrirModalNovaMovimentacao() {
    console.log('Abrindo modal nova movimentação');
    movimentacaoAtualId = null;
    document.getElementById('movimentacaoModalTitle').textContent = 'Nova Movimentação';
    document.getElementById('movimentacaoForm')?.reset();
    abrirModal('movimentacaoModal');
}

async function editarMovimentacao(id) {
    try {
        console.log('Editando movimentação ID:', id);
        const res = await fetch(`/pastagem/movimentacoes/${id}/`);
        if (!res.ok) throw new Error('Erro ao carregar movimentação');
        const mov = await res.json();
        console.log('Dados da movimentação para edição:', mov);

        movimentacaoAtualId = id;
        document.getElementById('movimentacaoModalTitle').textContent = 'Editar Movimentação';

        // DEFINIR OS VALORES NOS SELECTS (que já estão carregados via Django template)
        document.getElementById('animal').value = mov.animal_id || '';
        document.getElementById('pastagem').value = mov.pastagem_id || '';
        document.getElementById('data_entrada').value = mov.data_entrada || '';
        document.getElementById('data_saida').value = mov.data_saida || '';
        document.getElementById('observacoes').value = mov.observacoes || '';

        abrirModal('movimentacaoModal');
    } catch (err) {
        console.error('Erro ao editar movimentação:', err);
        mostrarMensagem('Erro ao carregar movimentação para edição', 'error');
    }
}

function solicitarExclusaoMovimentacao(id) {
    movimentacaoAtualId = id;
    abrirModal('confirmDeleteMovimentacao');
}

async function confirmarExclusaoMovimentacao() {
    if (!movimentacaoAtualId) return;
    try {
        const res = await fetch(`/pastagem/movimentacoes/${movimentacaoAtualId}/excluir/`, {
            method: 'DELETE',
            headers: { 'X-CSRFToken': getCSRFToken() }
        });
        const data = await res.json();
        if (data.success) {
            fecharModal('confirmDeleteMovimentacao');
            mostrarMensagem('Movimentação excluída com sucesso', 'success');
            carregarMovimentacoes(movimentacoesPaginaAtual);
        } else {
            mostrarMensagem(data.error || 'Erro ao excluir', 'error');
        }
    } catch (err) {
        console.error(err);
        mostrarMensagem('Erro ao excluir', 'error');
    }
}

async function salvarMovimentacao(e) {
    e.preventDefault();
    console.log('Salvando movimentação...');

    const form = document.getElementById('movimentacaoForm');
    const dados = {
        animal: form.animal.value,
        pastagem: form.pastagem.value,
        data_entrada: form.data_entrada.value,
        data_saida: form.data_saida.value,
        observacoes: form.observacoes.value
    };

    console.log('Dados do formulário:', dados);

    // Validação básica
    if (!dados.animal || !dados.pastagem || !dados.data_entrada) {
        mostrarMensagem('Preencha os campos obrigatórios', 'error');
        return;
    }

    try {
        const url = movimentacaoAtualId
            ? `/pastagem/movimentacoes/${movimentacaoAtualId}/editar/`
            : '/pastagem/movimentacoes/criar/';
        const method = movimentacaoAtualId ? 'PUT' : 'POST';

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
            fecharModal('movimentacaoModal');
            mostrarMensagem('Movimentação salva com sucesso', 'success');
            carregarMovimentacoes(movimentacoesPaginaAtual);
        } else {
            mostrarMensagem(result.error || 'Erro ao salvar', 'error');
        }
    } catch (err) {
        console.error(err);
        mostrarMensagem('Erro ao salvar', 'error');
    }
}

// =======================
// Listar e Paginação
// =======================
async function carregarMovimentacoes(pagina = 1) {
    try {
        const res = await fetch('/pastagem/movimentacoes/');
        if (!res.ok) throw new Error('Erro ao carregar movimentações');
        const movimentacoes = await res.json();

        movimentacoesCache = movimentacoes;
        movimentacoesPaginaAtual = pagina;

        const start = (pagina - 1) * movimentacoesPorPagina;
        const end = pagina * movimentacoesPorPagina;

        renderizarTabelaMovimentacoes(movimentacoes.slice(start, end));
        renderizarPaginacaoMovimentacoes(movimentacoes.length, pagina);
    } catch (err) {
        console.error(err);
        mostrarMensagem('Erro ao carregar movimentações', 'error');
    }
}

function renderizarTabelaMovimentacoes(movs) {
    const tbody = document.querySelector('#movimentacoesTable tbody');
    if (!tbody) return;

    if (!movs.length) {
        tbody.innerHTML = `
            <tr>
                <td colspan="5" class="text-center">
                    <div class="empty-state">
                        <i class="fas fa-exchange-alt fa-3x"></i>
                        <h3>Nenhuma movimentação encontrada</h3>
                        <p>Clique em "Nova Movimentação" para adicionar.</p>
                    </div>
                </td>
            </tr>
        `;
        return;
    }

    tbody.innerHTML = movs.map(m => `
        <tr>
            <td>${m.animal_codigo || '-'}</td>
            <td>${m.pastagem_nome || '-'}</td>
            <td>${m.data_entrada || '-'}</td>
            <td>${m.data_saida || '-'}</td>
            <td>
                <button class="btn btn-secondary btn-sm btn-editar" data-mov-id="${m.id}">
                    <i class="fas fa-edit"></i>
                </button>
                <button class="btn btn-danger btn-sm btn-excluir" data-mov-id="${m.id}">
                    <i class="fas fa-trash"></i>
                </button>
            </td>
        </tr>
    `).join('');
}

function renderizarPaginacaoMovimentacoes(totalItems, paginaAtual) {
    const totalPaginas = Math.ceil(totalItems / movimentacoesPorPagina);
    const container = document.getElementById('paginacaoMovimentacoes');
    if (!container) return;

    if (totalPaginas <= 1) {
        container.innerHTML = '';
        return;
    }

    let html = `<button class="page-btn" data-page="${paginaAtual - 1}" ${paginaAtual === 1 ? 'disabled' : ''}>&laquo;</button>`;

    for (let i = 1; i <= totalPaginas; i++) {
        html += `<button class="page-btn ${i === paginaAtual ? 'active' : ''}" data-page="${i}">${i}</button>`;
    }

    html += `<button class="page-btn" data-page="${paginaAtual + 1}" ${paginaAtual === totalPaginas ? 'disabled' : ''}>&raquo;</button>`;

    container.innerHTML = html;

    container.querySelectorAll('.page-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            const page = parseInt(btn.dataset.page);
            if (page >= 1 && page <= totalPaginas) {
                carregarMovimentacoes(page);
            }
        });
    });
}

// =======================
// Funções Auxiliares
// =======================
function getCSRFToken() {
    const token = document.querySelector('[name=csrfmiddlewaretoken]');
    return token ? token.value : '';
}

function mostrarMensagem(msg, tipo = 'info') {
    const toast = document.createElement('div');
    toast.style.cssText = `
        position: fixed; top: 20px; right: 20px;
        background: ${tipo === 'success' ? '#28a745' : tipo === 'error' ? '#dc3545' : '#17a2b8'};
        color: white; padding: 12px 20px; border-radius: 4px;
        z-index: 10000; box-shadow: 0 4px 6px rgba(0,0,0,0.1);
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
            if (toast.parentNode) {
                document.body.removeChild(toast);
            }
        });
    }, 4000);
}