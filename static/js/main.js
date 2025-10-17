// Dados de exemplo para demonstração
let sampleData = {
    lancamentos: [
        { id: 1, tipo: "CUSTO", categoria: "Alimentação", valor: 1500.00, data_movimento: "2023-05-15", animal: "Boi-001", descricao: "Compra de ração" },
        { id: 2, tipo: "RECEITA", categoria: "Venda", valor: 3200.00, data_movimento: "2023-05-20", animal: "Vaca-005", descricao: "Venda de animal" },
        { id: 3, tipo: "CUSTO", categoria: "Medicamentos", valor: 450.00, data_movimento: "2023-05-22", animal: null, descricao: "Vacinas" }
    ],
    animais: [
        { id: 1, codigo_brincos: "Boi-001", sexo: "M", nascimento: "2020-03-10", peso_atual: 450.5, raca: "Nelore", status: "ativo", rebanho_id: 1 },
        { id: 2, codigo_brincos: "Vaca-005", sexo: "F", nascimento: "2019-07-22", peso_atual: 380.0, raca: "Angus", status: "ativo", rebanho_id: 2 },
        { id: 3, codigo_brincos: "Bez-012", sexo: "F", nascimento: "2023-01-15", peso_atual: 120.0, raca: "Nelore", status: "ativo", rebanho_id: 1 }
    ],
    rebanhos: [
        { id: 1, nome_lote: "Lote de Engorda", capacidade: 100, ativo: true },
        { id: 2, nome_lote: "Lote de Cria", capacidade: 50, ativo: true },
        { id: 3, nome_lote: "Lote de Descanso", capacidade: 30, ativo: false }
    ],
    pastagens: [
        { id: 1, nome: "Pastagem Norte", area: 25.5, capacidade_suporte: 80, ativo: true },
        { id: 2, nome: "Pastagem Sul", area: 18.0, capacidade_suporte: 60, ativo: true },
        { id: 3, nome: "Pastagem Oeste", area: 12.5, capacidade_suporte: 40, ativo: false }
    ],
    movimentacoes: [
        { id: 1, animal_id: 1, pastagem_id: 1, data_entrada: "2023-05-01", data_saida: null },
        { id: 2, animal_id: 2, pastagem_id: 2, data_entrada: "2023-05-10", data_saida: "2023-05-20" },
        { id: 3, animal_id: 3, pastagem_id: 3, data_entrada: "2023-05-15", data_saida: null }
    ]
};

// Elementos DOM
const modal = document.getElementById('modal');
const modalTitle = document.getElementById('modalTitle');
const modalBody = document.getElementById('modalBody');
const closeModal = document.getElementById('closeModal');

// Funções auxiliares
function formatDate(dateString) {
    const options = { day: '2-digit', month: '2-digit', year: 'numeric' };
    return new Date(dateString).toLocaleDateString('pt-BR', options);
}

// Configuração básica do modal
if (closeModal) {
    closeModal.addEventListener('click', () => {
        modal.style.display = 'none';
    });
}

if (modal) {
    modal.addEventListener('click', (e) => {
        if (e.target === modal) {
            modal.style.display = 'none';
        }
    });
}

// Exportar para uso em outros arquivos
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { sampleData, formatDate };
}