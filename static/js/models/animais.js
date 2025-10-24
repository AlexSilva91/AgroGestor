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
// INICIALIZAÇÃO
// =======================
document.addEventListener('DOMContentLoaded', function () {
    const animaisContainer = document.getElementById('animais');
    if (animaisContainer) initializeAnimais();

    // Fechar modais clicando fora do conteúdo
    document.addEventListener('click', (e) => {
        document.querySelectorAll('.modal.active').forEach(modal => {
            if (e.target === modal) fecharModal(modal.id);
        });
    });

    // Fechar modais com ESC
    document.addEventListener('keydown', (e) => {
        if (e.key === "Escape") {
            document.querySelectorAll('.modal.active').forEach(m => fecharModal(m.id));
        }
    });

    // Delegação para fechar modais pelos botões Cancelar
    document.addEventListener('click', (e) => {
        const btnCancelar = e.target.closest('.btn-cancelar[data-modal]');
        if (btnCancelar) {
            fecharModal(btnCancelar.dataset.modal);
        }
    });
});

let animalAtualId = null;
let animaisCache = [];
let animaisPaginaAtual = 1;
const animaisPorPagina = 15;

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
    if (modalId === 'animalModal') {
        document.getElementById('animalForm')?.reset();
        animalAtualId = null;
    }
}

// =======================
// INICIALIZAÇÃO CRUD
// =======================
function initializeAnimais() {
    carregarAnimais();

    document.getElementById('addAnimal')?.addEventListener('click', abrirModalNovoAnimal);
    document.getElementById('animalForm')?.addEventListener('submit', salvarAnimal);
    document.getElementById('confirmDeleteAnimalBtn')?.addEventListener('click', confirmarExclusaoAnimal);

    // Delegação de eventos para editar/excluir
    const tbody = document.querySelector('#animaisTable tbody');
    if (tbody) {
        tbody.addEventListener('click', (e) => {
            const editarBtn = e.target.closest('.btn-editar');
            const excluirBtn = e.target.closest('.btn-excluir');
            if (editarBtn) editarAnimal(editarBtn.dataset.animalId);
            if (excluirBtn) solicitarExclusaoAnimal(excluirBtn.dataset.animalId);
        });
    }
}

// =======================
// CRUD
// =======================
function abrirModalNovoAnimal() {
    animalAtualId = null;
    document.getElementById('animalModalTitle').textContent = 'Novo Animal';
    document.getElementById('animalForm')?.reset();
    abrirModal('animalModal');
}

async function editarAnimal(id) {
    try {
        const res = await fetch(`/rebanho/animais/${id}/`);
        if (!res.ok) throw new Error('Erro ao carregar dados do animal');
        const animal = await res.json();

        document.getElementById('animal_id').value = animal.id;
        document.getElementById('codigo').value = animal.codigo_brincos;
        document.getElementById('sexo').value = animal.sexo.toLowerCase();
        document.getElementById('data_nascimento').value = animal.nascimento;
        document.getElementById('peso_atual').value = animal.peso_atual || '';
        document.getElementById('raca').value = animal.raca || '';
        document.getElementById('status').value = animal.status || 'ativo';
        document.getElementById('observacoes').value = animal.descricao || '';

        animalAtualId = id;
        document.getElementById('animalModalTitle').textContent = 'Editar Animal';
        abrirModal('animalModal');
    } catch (err) {
        console.error(err);
        mostrarMensagem('Erro ao carregar dados do animal', 'error');
    }
}

function solicitarExclusaoAnimal(id) {
    animalAtualId = id;
    abrirModal('confirmDeleteAnimal');
}

async function confirmarExclusaoAnimal() {
    if (!animalAtualId) return;
    try {
        const res = await fetch(`/rebanho/animais/${animalAtualId}/excluir/`, {
            method: 'DELETE',
            headers: { 'X-CSRFToken': getCSRFToken() }
        });
        const data = await res.json();

        if (data.success) {
            fecharModal('confirmDeleteAnimal');
            mostrarMensagem('Animal excluído com sucesso', 'success');
            carregarAnimais(animaisPaginaAtual);
        } else {
            mostrarMensagem(data.error || 'Erro ao excluir animal', 'error');
        }
    } catch (err) {
        console.error(err);
        mostrarMensagem('Erro ao excluir animal', 'error');
    }
}

async function salvarAnimal(e) {
    e.preventDefault();

    const form = document.getElementById('animalForm');
    const dados = {
        codigo_brincos: form.codigo.value.trim(),
        sexo: form.sexo.value.toUpperCase(),
        nascimento: form.data_nascimento.value,
        peso_atual: parseFloat(form.peso_atual.value),
        raca: form.raca.value.trim(),
        status: form.status.value,
        descricao: form.observacoes.value.trim(),
    };

    try {
        const url = animalAtualId
            ? `/rebanho/animais/${animalAtualId}/editar/`
            : '/rebanho/animais/criar/';
        const method = animalAtualId ? 'PUT' : 'POST';

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
            fecharModal('animalModal');
            mostrarMensagem('Animal salvo com sucesso', 'success');
            carregarAnimais(animaisPaginaAtual);
        } else {
            mostrarMensagem(result.error || 'Erro ao salvar animal', 'error');
        }
    } catch (err) {
        console.error(err);
        mostrarMensagem('Erro ao salvar animal', 'error');
    }
}

// =======================
// LISTAR E PAGINAÇÃO
// =======================
async function carregarAnimais(pagina = 1) {
    try {
        const res = await fetch('/rebanho/animais/');
        if (!res.ok) throw new Error('Erro ao carregar animais');
        const animais = await res.json();

        animaisCache = animais;
        animaisPaginaAtual = pagina;

        const start = (pagina - 1) * animaisPorPagina;
        const end = pagina * animaisPorPagina;

        renderizarTabelaAnimais(animais.slice(start, end));
        renderizarPaginacaoAnimais(animais.length, pagina);
    } catch (err) {
        console.error(err);
        mostrarMensagem('Erro ao carregar animais', 'error');
    }
}

function renderizarTabelaAnimais(animais) {
    const tbody = document.querySelector('#animaisTable tbody');
    if (!tbody) return;

    if (!animais.length) {
        tbody.innerHTML = `
            <tr>
                <td colspan="7" class="text-center">
                    <div class="empty-state">
                        <i class="fas fa-horse fa-3x"></i>
                        <h3>Nenhum animal encontrado</h3>
                        <p>Clique em "Novo Animal" para adicionar.</p>
                    </div>
                </td>
            </tr>
        `;
        return;
    }

    tbody.innerHTML = animais.map(a => `
        <tr>
            <td>${a.codigo_brincos}</td>
            <td>${a.sexo === 'M' ? 'Macho' : 'Fêmea'}</td>
            <td>${a.nascimento}</td>
            <td>${a.peso_atual || '-'}</td>
            <td>${a.raca || '-'}</td>
            <td><span class="badge ${a.status === 'ativo' ? 'badge-success' : 'badge-secondary'}">${a.status}</span></td>
            <td>
                <button class="btn btn-secondary btn-sm btn-editar" data-animal-id="${a.id}">
                    <i class="fas fa-edit"></i>
                </button>
                <button class="btn btn-danger btn-sm btn-excluir" data-animal-id="${a.id}">
                    <i class="fas fa-trash"></i>
                </button>
            </td>
        </tr>
    `).join('');
}

function renderizarPaginacaoAnimais(totalItems, paginaAtual) {
    const totalPaginas = Math.ceil(totalItems / animaisPorPagina);
    const paginacaoContainer = document.getElementById('paginacaoAnimais');
    if (!paginacaoContainer) return;

    if (totalPaginas <= 1) {
        paginacaoContainer.innerHTML = '';
        return;
    }

    const maxBtn = 5;
    let startPage = Math.max(1, paginaAtual - Math.floor(maxBtn / 2));
    let endPage = Math.min(totalPaginas, startPage + maxBtn - 1);

    if (endPage - startPage + 1 < maxBtn) {
        startPage = Math.max(1, endPage - maxBtn + 1);
    }

    let html = `
        <button class="page-btn" data-page="${paginaAtual - 1}" ${paginaAtual === 1 ? 'disabled' : ''}>
            <span>&laquo;</span>
        </button>
    `;

    for (let i = startPage; i <= endPage; i++) {
        html += `<button class="page-btn ${i === paginaAtual ? 'active' : ''}" data-page="${i}">${i}</button>`;
    }

    html += `
        <button class="page-btn" data-page="${paginaAtual + 1}" ${paginaAtual === totalPaginas ? 'disabled' : ''}>
            <span>&raquo;</span>
        </button>
    `;

    paginacaoContainer.innerHTML = html;
    paginacaoContainer.querySelectorAll('.page-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            const page = parseInt(btn.dataset.page);
            if (page >= 1 && page <= totalPaginas) carregarAnimais(page);
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
