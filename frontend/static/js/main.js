// BGP Monitor - Frontend JavaScript

// Configuração
const API_BASE_URL = '';
const UPDATE_INTERVAL = 30000; // 30 segundos

// Inicialização
document.addEventListener('DOMContentLoaded', function() {
    console.log('BGP Monitor iniciado');

    // Carregar dados iniciais
    loadDashboardData();

    // Atualizar periodicamente
    setInterval(loadDashboardData, UPDATE_INTERVAL);
});

// Carregar todos os dados do dashboard
async function loadDashboardData() {
    console.log('Carregando dados do dashboard...');

    try {
        // Por enquanto, exibir mensagem de desenvolvimento
        displayDevelopmentMessage();
    } catch (error) {
        console.error('Erro ao carregar dados:', error);
    }
}

// Mensagem de desenvolvimento
function displayDevelopmentMessage() {
    document.getElementById('bgp-total').textContent = '0';
    document.getElementById('bgp-up').textContent = '0';
    document.getElementById('bgp-down').textContent = '0';
    document.getElementById('interfaces-up').textContent = '0';

    document.getElementById('bgp-sessions').innerHTML = `
        <p style="text-align: center; color: #666; padding: 2rem;">
            Sistema em desenvolvimento.<br>
            Configure o arquivo .env e inicie a coleta de dados.<br><br>
            <a href="/docs" style="color: #667eea;">Ver Documentação da API</a>
        </p>
    `;

    document.getElementById('events').innerHTML = `
        <p style="text-align: center; color: #666; padding: 2rem;">
            Nenhum evento registrado ainda.
        </p>
    `;

    document.getElementById('interfaces').innerHTML = `
        <p style="text-align: center; color: #666; padding: 2rem;">
            Nenhuma interface monitorada ainda.
        </p>
    `;
}

// Funções auxiliares para futuras implementações

function formatUptime(seconds) {
    const days = Math.floor(seconds / 86400);
    const hours = Math.floor((seconds % 86400) / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);

    if (days > 0) {
        return `${days}d ${hours}h ${minutes}m`;
    } else if (hours > 0) {
        return `${hours}h ${minutes}m`;
    } else {
        return `${minutes}m`;
    }
}

function formatBytes(bytes) {
    if (bytes >= 1e9) {
        return (bytes / 1e9).toFixed(2) + ' Gbps';
    } else if (bytes >= 1e6) {
        return (bytes / 1e6).toFixed(2) + ' Mbps';
    } else if (bytes >= 1e3) {
        return (bytes / 1e3).toFixed(2) + ' Kbps';
    } else {
        return bytes + ' bps';
    }
}

function getStatusClass(status) {
    const statusLower = status.toLowerCase();
    if (statusLower === 'established' || statusLower === 'up') {
        return 'up';
    } else if (statusLower === 'down') {
        return 'down';
    } else {
        return 'idle';
    }
}
