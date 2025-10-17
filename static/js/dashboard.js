// Elementos DOM específicos do dashboard
const tabs = document.querySelectorAll('.tab');
const tabContents = document.querySelectorAll('.tab-content');
const navLinks = document.querySelectorAll('nav a');
const pageContents = document.querySelectorAll('.page-content');

// Inicialização do Dashboard
document.addEventListener('DOMContentLoaded', function () {
    initializeDashboard();
});

function initializeDashboard() {
    // Carregar dados iniciais
    loadTableData('lancamentos', sampleData.lancamentos);
    loadTableData('animais', sampleData.animais);
    loadTableData('rebanhos', sampleData.rebanhos);
    loadTableData('pastagens', sampleData.pastagens);
    loadTableData('movimentacoes', sampleData.movimentacoes);

    // Configurar eventos de tabs
    tabs.forEach(tab => {
        tab.addEventListener('click', () => {
            const tabId = tab.getAttribute('data-tab');
            activateTab(tabId);
        });
    });

    // Configurar eventos dos botões de adicionar
    if (document.getElementById('addLancamento')) {
        document.getElementById('addLancamento').addEventListener('click', () => showLancamentoForm());
    }
    if (document.getElementById('addAnimal')) {
        document.getElementById('addAnimal').addEventListener('click', () => showAnimalForm());
    }
    if (document.getElementById('addRebanho')) {
        document.getElementById('addRebanho').addEventListener('click', () => showRebanhoForm());
    }
    if (document.getElementById('addPastagem')) {
        document.getElementById('addPastagem').addEventListener('click', () => showPastagemForm());
    }
    if (document.getElementById('addMovimentacao')) {
        document.getElementById('addMovimentacao').addEventListener('click', () => showMovimentacaoForm());
    }

    // Configurar eventos de navegação
    navLinks.forEach(link => {
        link.addEventListener('click', (e) => {
            e.preventDefault();
            const pageId = link.getAttribute('data-page');
            activatePage(pageId);
        });
    });

    // Configurar formulário de configurações
    const configForm = document.getElementById('configForm');
    if (configForm) {
        configForm.addEventListener('submit', function (e) {
            e.preventDefault();
            alert('Configurações salvas com sucesso!');
        });
    }
}

// Funções de controle de páginas e tabs
function activatePage(pageId) {
    pageContents.forEach(content => content.classList.remove('active'));
    navLinks.forEach(link => link.classList.remove('active'));

    document.getElementById(pageId).classList.add('active');
    document.querySelector(`nav a[data-page="${pageId}"]`).classList.add('active');
}

function activateTab(tabId) {
    tabs.forEach(tab => tab.classList.remove('active'));
    tabContents.forEach(content => content.classList.remove('active'));

    document.querySelector(`.tab[data-tab="${tabId}"]`).classList.add('active');
    document.getElementById(tabId).classList.add('active');
}

// Função para carregar dados nas tabelas
function loadTableData(tableId, data) {
    const tableBody = document.querySelector(`#${tableId}Table tbody`);
    if (!tableBody) return;

    tableBody.innerHTML = '';

    data.forEach(item => {
        const row = document.createElement('tr');

        switch (tableId) {
            case 'lancamentos':
                row.innerHTML = `
                    <td><span class="badge ${item.tipo === 'CUSTO' ? 'badge-danger' : 'badge-success'}">${item.tipo}</span></td>
                    <td>${item.categoria}</td>
                    <td>R$ ${item.valor.toFixed(2)}</td>
                    <td>${formatDate(item.data_movimento)}</td>
                    <td>${item.animal || '-'}</td>
                    <td class="actions">
                        <button class="btn btn-secondary" onclick="editLancamento(${item.id})">
                            <i class="fas fa-edit"></i>
                        </button>
                        <button class="btn btn-danger" onclick="deleteLancamento(${item.id})">
                            <i class="fas fa-trash"></i>
                        </button>
                    </td>
                `;
                break;
            case 'animais':
                row.innerHTML = `
                    <td>${item.codigo_brincos}</td>
                    <td>${item.sexo === 'M' ? 'Macho' : 'Fêmea'}</td>
                    <td>${formatDate(item.nascimento)}</td>
                    <td>${item.peso_atual ? `${item.peso_atual} kg` : '-'}</td>
                    <td>${item.raca || '-'}</td>
                    <td><span class="badge ${item.status === 'ativo' ? 'badge-success' : 'badge-secondary'}">${item.status}</span></td>
                    <td class="actions">
                        <button class="btn btn-secondary" onclick="editAnimal(${item.id})">
                            <i class="fas fa-edit"></i>
                        </button>
                        <button class="btn btn-danger" onclick="deleteAnimal(${item.id})">
                            <i class="fas fa-trash"></i>
                        </button>
                    </td>
                `;
                break;
            case 'rebanhos':
                row.innerHTML = `
                    <td>${item.nome_lote}</td>
                    <td>${item.capacidade}</td>
                    <td><span class="badge ${item.ativo ? 'badge-success' : 'badge-secondary'}">${item.ativo ? 'Ativo' : 'Inativo'}</span></td>
                    <td class="actions">
                        <button class="btn btn-secondary" onclick="editRebanho(${item.id})">
                            <i class="fas fa-edit"></i>
                        </button>
                        <button class="btn btn-danger" onclick="deleteRebanho(${item.id})">
                            <i class="fas fa-trash"></i>
                        </button>
                    </td>
                `;
                break;
            case 'pastagens':
                row.innerHTML = `
                    <td>${item.nome}</td>
                    <td>${item.area || '-'}</td>
                    <td>${item.capacidade_suporte || '-'}</td>
                    <td><span class="badge ${item.ativo ? 'badge-success' : 'badge-secondary'}">${item.ativo ? 'Ativa' : 'Inativa'}</span></td>
                    <td class="actions">
                        <button class="btn btn-secondary" onclick="editPastagem(${item.id})">
                            <i class="fas fa-edit"></i>
                        </button>
                        <button class="btn btn-danger" onclick="deletePastagem(${item.id})">
                            <i class="fas fa-trash"></i>
                        </button>
                    </td>
                `;
                break;
            case 'movimentacoes':
                const animal = sampleData.animais.find(a => a.id === item.animal_id);
                const pastagem = sampleData.pastagens.find(p => p.id === item.pastagem_id);
                row.innerHTML = `
                    <td>${animal ? animal.codigo_brincos : 'N/A'}</td>
                    <td>${pastagem ? pastagem.nome : 'N/A'}</td>
                    <td>${formatDate(item.data_entrada)}</td>
                    <td>${item.data_saida ? formatDate(item.data_saida) : '-'}</td>
                    <td class="actions">
                        <button class="btn btn-secondary" onclick="editMovimentacao(${item.id})">
                            <i class="fas fa-edit"></i>
                        </button>
                        <button class="btn btn-danger" onclick="deleteMovimentacao(${item.id})">
                            <i class="fas fa-trash"></i>
                        </button>
                    </td>
                `;
                break;
        }

        tableBody.appendChild(row);
    });
}

// Funções para mostrar formulários
function showLancamentoForm(lancamento = null) {
    const isEdit = lancamento !== null;
    const title = isEdit ? 'Editar Lançamento Financeiro' : 'Novo Lançamento Financeiro';

    modalTitle.textContent = title;
    modalBody.innerHTML = `
        <div class="form-container">
            <form id="lancamentoForm">
                <div class="form-group">
                    <label for="tipo">Tipo</label>
                    <select id="tipo" required>
                        <option value="">Selecione...</option>
                        <option value="CUSTO" ${isEdit && lancamento.tipo === 'CUSTO' ? 'selected' : ''}>Custo</option>
                        <option value="RECEITA" ${isEdit && lancamento.tipo === 'RECEITA' ? 'selected' : ''}>Receita</option>
                    </select>
                </div>
                <div class="form-group">
                    <label for="categoria">Categoria</label>
                    <input type="text" id="categoria" value="${isEdit ? lancamento.categoria : ''}" required>
                </div>
                <div class="form-group">
                    <label for="valor">Valor (R$)</label>
                    <input type="number" id="valor" step="0.01" min="0" value="${isEdit ? lancamento.valor : ''}" required>
                </div>
                <div class="form-group">
                    <label for="data_movimento">Data do Movimento</label>
                    <input type="date" id="data_movimento" value="${isEdit ? lancamento.data_movimento : ''}" required>
                </div>
                <div class="form-group">
                    <label for="animal">Animal (opcional)</label>
                    <select id="animal">
                        <option value="">Nenhum</option>
                        ${sampleData.animais.map(animal =>
        `<option value="${animal.id}" ${isEdit && lancamento.animal === animal.codigo_brincos ? 'selected' : ''}>
                                ${animal.codigo_brincos}
                            </option>`
    ).join('')}
                    </select>
                </div>
                <div class="form-group">
                    <label for="descricao">Descrição</label>
                    <textarea id="descricao" rows="3">${isEdit ? lancamento.descricao : ''}</textarea>
                </div>
                <div class="form-actions">
                    <button type="button" class="btn btn-secondary" onclick="modal.style.display='none'">Cancelar</button>
                    <button type="submit" class="btn btn-primary">${isEdit ? 'Atualizar' : 'Salvar'}</button>
                </div>
            </form>
        </div>
    `;

    document.getElementById('lancamentoForm').addEventListener('submit', function (e) {
        e.preventDefault();

        const animalSelect = document.getElementById('animal');
        const selectedAnimalId = animalSelect.value;
        const selectedAnimal = sampleData.animais.find(a => a.id == selectedAnimalId);

        const newLancamento = {
            id: isEdit ? lancamento.id : sampleData.lancamentos.length + 1,
            tipo: document.getElementById('tipo').value,
            categoria: document.getElementById('categoria').value,
            valor: parseFloat(document.getElementById('valor').value),
            data_movimento: document.getElementById('data_movimento').value,
            animal: selectedAnimal ? selectedAnimal.codigo_brincos : null,
            descricao: document.getElementById('descricao').value
        };

        if (isEdit) {
            const index = sampleData.lancamentos.findIndex(l => l.id === lancamento.id);
            sampleData.lancamentos[index] = newLancamento;
        } else {
            sampleData.lancamentos.push(newLancamento);
        }

        loadTableData('lancamentos', sampleData.lancamentos);
        modal.style.display = 'none';
        alert(isEdit ? 'Lançamento atualizado com sucesso!' : 'Lançamento criado com sucesso!');
    });

    modal.style.display = 'flex';
}

function showAnimalForm(animal = null) {
    const isEdit = animal !== null;
    const title = isEdit ? 'Editar Animal' : 'Novo Animal';

    modalTitle.textContent = title;
    modalBody.innerHTML = `
        <div class="form-container">
            <form id="animalForm">
                <div class="form-group">
                    <label for="codigo_brincos">Código/Brinco</label>
                    <input type="text" id="codigo_brincos" value="${isEdit ? animal.codigo_brincos : ''}" required>
                </div>
                <div class="form-group">
                    <label for="sexo">Sexo</label>
                    <select id="sexo" required>
                        <option value="">Selecione...</option>
                        <option value="M" ${isEdit && animal.sexo === 'M' ? 'selected' : ''}>Macho</option>
                        <option value="F" ${isEdit && animal.sexo === 'F' ? 'selected' : ''}>Fêmea</option>
                    </select>
                </div>
                <div class="form-group">
                    <label for="nascimento">Data de Nascimento</label>
                    <input type="date" id="nascimento" value="${isEdit ? animal.nascimento : ''}" required>
                </div>
                <div class="form-group">
                    <label for="peso_atual">Peso Atual (kg)</label>
                    <input type="number" id="peso_atual" step="0.01" min="0" value="${isEdit ? animal.peso_atual || '' : ''}">
                </div>
                <div class="form-group">
                    <label for="raca">Raça</label>
                    <input type="text" id="raca" value="${isEdit ? animal.raca || '' : ''}">
                </div>
                <div class="form-group">
                    <label for="rebanho">Rebanho</label>
                    <select id="rebanho" required>
                        <option value="">Selecione...</option>
                        ${sampleData.rebanhos.map(rebanho =>
        `<option value="${rebanho.id}" ${isEdit && animal.rebanho_id === rebanho.id ? 'selected' : ''}>
                                ${rebanho.nome_lote}
                            </option>`
    ).join('')}
                    </select>
                </div>
                <div class="form-group">
                    <label for="status">Status</label>
                    <select id="status" required>
                        <option value="ativo" ${isEdit && animal.status === 'ativo' ? 'selected' : ''}>Ativo</option>
                        <option value="inativo" ${isEdit && animal.status === 'inativo' ? 'selected' : ''}>Inativo</option>
                        <option value="vendido" ${isEdit && animal.status === 'vendido' ? 'selected' : ''}>Vendido</option>
                    </select>
                </div>
                <div class="form-actions">
                    <button type="button" class="btn btn-secondary" onclick="modal.style.display='none'">Cancelar</button>
                    <button type="submit" class="btn btn-primary">${isEdit ? 'Atualizar' : 'Salvar'}</button>
                </div>
            </form>
        </div>
    `;

    document.getElementById('animalForm').addEventListener('submit', function (e) {
        e.preventDefault();

        const newAnimal = {
            id: isEdit ? animal.id : sampleData.animais.length + 1,
            codigo_brincos: document.getElementById('codigo_brincos').value,
            sexo: document.getElementById('sexo').value,
            nascimento: document.getElementById('nascimento').value,
            peso_atual: document.getElementById('peso_atual').value ? parseFloat(document.getElementById('peso_atual').value) : null,
            raca: document.getElementById('raca').value,
            rebanho_id: parseInt(document.getElementById('rebanho').value),
            status: document.getElementById('status').value
        };

        if (isEdit) {
            const index = sampleData.animais.findIndex(a => a.id === animal.id);
            sampleData.animais[index] = newAnimal;
        } else {
            sampleData.animais.push(newAnimal);
        }

        loadTableData('animais', sampleData.animais);
        modal.style.display = 'none';
        alert(isEdit ? 'Animal atualizado com sucesso!' : 'Animal criado com sucesso!');
    });

    modal.style.display = 'flex';
}

function showRebanhoForm(rebanho = null) {
    const isEdit = rebanho !== null;
    const title = isEdit ? 'Editar Rebanho' : 'Novo Rebanho';

    modalTitle.textContent = title;
    modalBody.innerHTML = `
        <div class="form-container">
            <form id="rebanhoForm">
                <div class="form-group">
                    <label for="nome_lote">Nome do Lote</label>
                    <input type="text" id="nome_lote" value="${isEdit ? rebanho.nome_lote : ''}" required>
                </div>
                <div class="form-group">
                    <label for="capacidade">Capacidade</label>
                    <input type="number" id="capacidade" min="1" value="${isEdit ? rebanho.capacidade : ''}" required>
                </div>
                <div class="form-group">
                    <label for="ativo">Status</label>
                    <select id="ativo" required>
                        <option value="true" ${isEdit && rebanho.ativo ? 'selected' : ''}>Ativo</option>
                        <option value="false" ${isEdit && !rebanho.ativo ? 'selected' : ''}>Inativo</option>
                    </select>
                </div>
                <div class="form-actions">
                    <button type="button" class="btn btn-secondary" onclick="modal.style.display='none'">Cancelar</button>
                    <button type="submit" class="btn btn-primary">${isEdit ? 'Atualizar' : 'Salvar'}</button>
                </div>
            </form>
        </div>
    `;

    document.getElementById('rebanhoForm').addEventListener('submit', function (e) {
        e.preventDefault();

        const newRebanho = {
            id: isEdit ? rebanho.id : sampleData.rebanhos.length + 1,
            nome_lote: document.getElementById('nome_lote').value,
            capacidade: parseInt(document.getElementById('capacidade').value),
            ativo: document.getElementById('ativo').value === 'true'
        };

        if (isEdit) {
            const index = sampleData.rebanhos.findIndex(r => r.id === rebanho.id);
            sampleData.rebanhos[index] = newRebanho;
        } else {
            sampleData.rebanhos.push(newRebanho);
        }

        loadTableData('rebanhos', sampleData.rebanhos);
        modal.style.display = 'none';
        alert(isEdit ? 'Rebanho atualizado com sucesso!' : 'Rebanho criado com sucesso!');
    });

    modal.style.display = 'flex';
}

function showPastagemForm(pastagem = null) {
    const isEdit = pastagem !== null;
    const title = isEdit ? 'Editar Pastagem' : 'Nova Pastagem';

    modalTitle.textContent = title;
    modalBody.innerHTML = `
        <div class="form-container">
            <form id="pastagemForm">
                <div class="form-group">
                    <label for="nome">Nome da Pastagem</label>
                    <input type="text" id="nome" value="${isEdit ? pastagem.nome : ''}" required>
                </div>
                <div class="form-group">
                    <label for="area">Área (hectares)</label>
                    <input type="number" id="area" step="0.01" min="0" value="${isEdit ? pastagem.area || '' : ''}">
                </div>
                <div class="form-group">
                    <label for="capacidade_suporte">Capacidade de Suporte</label>
                    <input type="number" id="capacidade_suporte" min="0" value="${isEdit ? pastagem.capacidade_suporte || '' : ''}">
                </div>
                <div class="form-group">
                    <label for="ativo">Status</label>
                    <select id="ativo" required>
                        <option value="true" ${isEdit && pastagem.ativo ? 'selected' : ''}>Ativa</option>
                        <option value="false" ${isEdit && !pastagem.ativo ? 'selected' : ''}>Inativa</option>
                    </select>
                </div>
                <div class="form-actions">
                    <button type="button" class="btn btn-secondary" onclick="modal.style.display='none'">Cancelar</button>
                    <button type="submit" class="btn btn-primary">${isEdit ? 'Atualizar' : 'Salvar'}</button>
                </div>
            </form>
        </div>
    `;

    document.getElementById('pastagemForm').addEventListener('submit', function (e) {
        e.preventDefault();

        const newPastagem = {
            id: isEdit ? pastagem.id : sampleData.pastagens.length + 1,
            nome: document.getElementById('nome').value,
            area: document.getElementById('area').value ? parseFloat(document.getElementById('area').value) : null,
            capacidade_suporte: document.getElementById('capacidade_suporte').value ? parseInt(document.getElementById('capacidade_suporte').value) : null,
            ativo: document.getElementById('ativo').value === 'true'
        };

        if (isEdit) {
            const index = sampleData.pastagens.findIndex(p => p.id === pastagem.id);
            sampleData.pastagens[index] = newPastagem;
        } else {
            sampleData.pastagens.push(newPastagem);
        }

        loadTableData('pastagens', sampleData.pastagens);
        modal.style.display = 'none';
        alert(isEdit ? 'Pastagem atualizada com sucesso!' : 'Pastagem criada com sucesso!');
    });

    modal.style.display = 'flex';
}

function showMovimentacaoForm(movimentacao = null) {
    const isEdit = movimentacao !== null;
    const title = isEdit ? 'Editar Movimentação' : 'Nova Movimentação';

    modalTitle.textContent = title;
    modalBody.innerHTML = `
        <div class="form-container">
            <form id="movimentacaoForm">
                <div class="form-group">
                    <label for="animal_id">Animal</label>
                    <select id="animal_id" required>
                        <option value="">Selecione...</option>
                        ${sampleData.animais.map(animal =>
        `<option value="${animal.id}" ${isEdit && movimentacao.animal_id === animal.id ? 'selected' : ''}>
                                ${animal.codigo_brincos}
                            </option>`
    ).join('')}
                    </select>
                </div>
                <div class="form-group">
                    <label for="pastagem_id">Pastagem</label>
                    <select id="pastagem_id" required>
                        <option value="">Selecione...</option>
                        ${sampleData.pastagens.map(pastagem =>
        `<option value="${pastagem.id}" ${isEdit && movimentacao.pastagem_id === pastagem.id ? 'selected' : ''}>
                                ${pastagem.nome}
                            </option>`
    ).join('')}
                    </select>
                </div>
                <div class="form-group">
                    <label for="data_entrada">Data de Entrada</label>
                    <input type="date" id="data_entrada" value="${isEdit ? movimentacao.data_entrada : ''}" required>
                </div>
                <div class="form-group">
                    <label for="data_saida">Data de Saída (opcional)</label>
                    <input type="date" id="data_saida" value="${isEdit ? movimentacao.data_saida || '' : ''}">
                </div>
                <div class="form-actions">
                    <button type="button" class="btn btn-secondary" onclick="modal.style.display='none'">Cancelar</button>
                    <button type="submit" class="btn btn-primary">${isEdit ? 'Atualizar' : 'Salvar'}</button>
                </div>
            </form>
        </div>
    `;

    document.getElementById('movimentacaoForm').addEventListener('submit', function (e) {
        e.preventDefault();

        const newMovimentacao = {
            id: isEdit ? movimentacao.id : sampleData.movimentacoes.length + 1,
            animal_id: parseInt(document.getElementById('animal_id').value),
            pastagem_id: parseInt(document.getElementById('pastagem_id').value),
            data_entrada: document.getElementById('data_entrada').value,
            data_saida: document.getElementById('data_saida').value || null
        };

        if (isEdit) {
            const index = sampleData.movimentacoes.findIndex(m => m.id === movimentacao.id);
            sampleData.movimentacoes[index] = newMovimentacao;
        } else {
            sampleData.movimentacoes.push(newMovimentacao);
        }

        loadTableData('movimentacoes', sampleData.movimentacoes);
        modal.style.display = 'none';
        alert(isEdit ? 'Movimentação atualizada com sucesso!' : 'Movimentação criada com sucesso!');
    });

    modal.style.display = 'flex';
}

// Funções de edição
function editLancamento(id) {
    const lancamento = sampleData.lancamentos.find(l => l.id === id);
    if (lancamento) {
        showLancamentoForm(lancamento);
    }
}

function editAnimal(id) {
    const animal = sampleData.animais.find(a => a.id === id);
    if (animal) {
        showAnimalForm(animal);
    }
}

function editRebanho(id) {
    const rebanho = sampleData.rebanhos.find(r => r.id === id);
    if (rebanho) {
        showRebanhoForm(rebanho);
    }
}

function editPastagem(id) {
    const pastagem = sampleData.pastagens.find(p => p.id === id);
    if (pastagem) {
        showPastagemForm(pastagem);
    }
}

function editMovimentacao(id) {
    const movimentacao = sampleData.movimentacoes.find(m => m.id === id);
    if (movimentacao) {
        showMovimentacaoForm(movimentacao);
    }
}

// Funções de exclusão
function deleteLancamento(id) {
    if (confirm('Tem certeza que deseja excluir este lançamento?')) {
        sampleData.lancamentos = sampleData.lancamentos.filter(l => l.id !== id);
        loadTableData('lancamentos', sampleData.lancamentos);
        alert('Lançamento excluído com sucesso!');
    }
}

function deleteAnimal(id) {
    if (confirm('Tem certeza que deseja excluir este animal?')) {
        sampleData.animais = sampleData.animais.filter(a => a.id !== id);
        loadTableData('animais', sampleData.animais);
        alert('Animal excluído com sucesso!');
    }
}

function deleteRebanho(id) {
    if (confirm('Tem certeza que deseja excluir este rebanho?')) {
        sampleData.rebanhos = sampleData.rebanhos.filter(r => r.id !== id);
        loadTableData('rebanhos', sampleData.rebanhos);
        alert('Rebanho excluído com sucesso!');
    }
}

function deletePastagem(id) {
    if (confirm('Tem certeza que deseja excluir esta pastagem?')) {
        sampleData.pastagens = sampleData.pastagens.filter(p => p.id !== id);
        loadTableData('pastagens', sampleData.pastagens);
        alert('Pastagem excluída com sucesso!');
    }
}

function deleteMovimentacao(id) {
    if (confirm('Tem certeza que deseja excluir esta movimentação?')) {
        sampleData.movimentacoes = sampleData.movimentacoes.filter(m => m.id !== id);
        loadTableData('movimentacoes', sampleData.movimentacoes);
        alert('Movimentação excluída com sucesso!');
    }
}