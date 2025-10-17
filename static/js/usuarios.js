// Controle de tabs
document.addEventListener('DOMContentLoaded', function () {
    // Configurar tabs
    const tabs = document.querySelectorAll('.tab');
    const tabContents = document.querySelectorAll('.tab-content');

    tabs.forEach(tab => {
        tab.addEventListener('click', () => {
            const tabId = tab.getAttribute('data-tab');
            ativarTab(tabId);
        });
    });

    // Botão adicionar usuário
    document.getElementById('addUsuario').addEventListener('click', () => {
        abrirModalUsuario();
    });

    // Fechar modal
    document.getElementById('closeUserModal').addEventListener('click', fecharModal);

    // Configurar formulário
    document.getElementById('userForm').addEventListener('submit', salvarUsuario);
});

function ativarTab(tabId) {
    // Desativar todas as tabs
    document.querySelectorAll('.tab').forEach(tab => tab.classList.remove('active'));
    document.querySelectorAll('.tab-content').forEach(content => content.classList.remove('active'));

    // Ativar tab selecionada
    document.querySelector(`.tab[data-tab="${tabId}"]`).classList.add('active');
    document.getElementById(tabId).classList.add('active');
}

function abrirModalUsuario(usuarioId = null) {
    const modal = document.getElementById('userModal');
    const title = document.getElementById('userModalTitle');
    const form = document.getElementById('userForm');

    if (usuarioId) {
        title.textContent = 'Editar Usuário';
        carregarDadosUsuario(usuarioId);
    } else {
        title.textContent = 'Novo Usuário';
        form.reset();
    }

    modal.style.display = 'flex';
}

function fecharModal() {
    document.getElementById('userModal').style.display = 'none';
}

function carregarDadosUsuario(usuarioId) {
    // Fazer requisição AJAX para buscar dados do usuário
    fetch(`/api/usuarios/${usuarioId}/`)
        .then(response => response.json())
        .then(usuario => {
            document.getElementById('username').value = usuario.username;
            document.getElementById('email').value = usuario.email;
            document.getElementById('first_name').value = usuario.first_name || '';
            document.getElementById('last_name').value = usuario.last_name || '';
            document.getElementById('is_active').checked = usuario.is_active;
            document.getElementById('is_staff').checked = usuario.is_staff;

            // Configurar grupos
            const groupsSelect = document.getElementById('groups');
            Array.from(groupsSelect.options).forEach(option => {
                option.selected = usuario.groups.includes(parseInt(option.value));
            });
        })
        .catch(error => {
            console.error('Erro ao carregar usuário:', error);
            alert('Erro ao carregar dados do usuário');
        });
}

function salvarUsuario(event) {
    event.preventDefault();

    const formData = new FormData(event.target);
    const usuarioId = document.getElementById('userForm').dataset.usuarioId;

    const url = usuarioId ? `/api/usuarios/${usuarioId}/` : '/api/usuarios/';
    const method = usuarioId ? 'PUT' : 'POST';

    fetch(url, {
        method: method,
        body: formData,
        headers: {
            'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
        }
    })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                fecharModal();
                location.reload(); // Recarregar a página para atualizar a lista
            } else {
                alert('Erro ao salvar usuário: ' + (data.error || 'Erro desconhecido'));
            }
        })
        .catch(error => {
            console.error('Erro:', error);
            alert('Erro ao salvar usuário');
        });
}

function editarUsuario(usuarioId) {
    abrirModalUsuario(usuarioId);
}

function ativarUsuario(usuarioId) {
    if (confirm('Deseja ativar este usuário?')) {
        fetch(`/api/usuarios/${usuarioId}/ativar/`, {
            method: 'POST',
            headers: {
                'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
            }
        })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    location.reload();
                } else {
                    alert('Erro ao ativar usuário');
                }
            });
    }
}

function desativarUsuario(usuarioId) {
    if (confirm('Deseja desativar este usuário?')) {
        fetch(`/api/usuarios/${usuarioId}/desativar/`, {
            method: 'POST',
            headers: {
                'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
            }
        })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    location.reload();
                } else {
                    alert('Erro ao desativar usuário');
                }
            });
    }
}

function excluirUsuario(usuarioId) {
    if (confirm('Tem certeza que deseja excluir este usuário? Esta ação não pode ser desfeita.')) {
        fetch(`/api/usuarios/${usuarioId}/`, {
            method: 'DELETE',
            headers: {
                'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
            }
        })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    location.reload();
                } else {
                    alert('Erro ao excluir usuário: ' + (data.error || 'Erro desconhecido'));
                }
            });
    }
}

function filtrarLogs() {
    const usuarioId = document.getElementById('filterUser').value;
    const data = document.getElementById('filterDate').value;

    // Fazer requisição AJAX para filtrar logs
    const params = new URLSearchParams();
    if (usuarioId) params.append('usuario', usuarioId);
    if (data) params.append('data', data);

    window.location.search = params.toString();
}