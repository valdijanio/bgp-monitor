// Utilit\u00e1rios gerais do BGP Monitor

// Formatar uptime em formato leg\u00edvel
function formatUptime(seconds) {
    if (!seconds || seconds === 0) return 'Never';

    const days = Math.floor(seconds / 86400);
    const hours = Math.floor((seconds % 86400) / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);

    const parts = [];
    if (days > 0) parts.push(`${days}d`);
    if (hours > 0) parts.push(`${hours}h`);
    if (minutes > 0) parts.push(`${minutes}m`);

    return parts.join(' ') || '< 1m';
}

// Formatar bytes para unidades leg\u00edveis
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

// Formatar timestamp para formato leg\u00edvel
function formatTimestamp(timestamp) {
    if (!timestamp) return '-';

    const date = new Date(timestamp);
    const now = new Date();
    const diff = Math.floor((now - date) / 1000);

    // Se for menos de 1 minuto
    if (diff < 60) return 'agora';

    // Se for menos de 1 hora
    if (diff < 3600) {
        const minutes = Math.floor(diff / 60);
        return `${minutes} min atr\u00e1s`;
    }

    // Se for menos de 24 horas
    if (diff < 86400) {
        const hours = Math.floor(diff / 3600);
        return `${hours}h atr\u00e1s`;
    }

    // Sen\u00e3o, mostrar data completa
    return date.toLocaleString('pt-BR', {
        day: '2-digit',
        month: '2-digit',
        year: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    });
}

// Obter classe CSS baseada no status
function getStatusClass(status) {
    const statusLower = status.toLowerCase();
    if (statusLower === 'established' || statusLower === 'up') {
        return 'status-up';
    } else if (statusLower === 'down') {
        return 'status-down';
    } else {
        return 'status-idle';
    }
}

// Obter \u00edcone baseado no status
function getStatusIcon(status) {
    const statusLower = status.toLowerCase();
    if (statusLower === 'established' || statusLower === 'up') {
        return '\u2713'; // Check
    } else if (statusLower === 'down') {
        return '\u2717'; // X
    } else {
        return '\u26A0'; // Warning
    }
}

// Obter cor baseada na severidade
function getSeverityColor(severity) {
    const severityLower = severity.toLowerCase();
    switch (severityLower) {
        case 'critical':
            return '#ef4444'; // Vermelho
        case 'warning':
            return '#f59e0b'; // Amarelo
        case 'info':
            return '#3b82f6'; // Azul
        default:
            return '#6b7280'; // Cinza
    }
}

// Truncar texto longo
function truncateText(text, maxLength = 50) {
    if (!text || text.length <= maxLength) return text;
    return text.substring(0, maxLength) + '...';
}

// Escapar HTML para prevenir XSS
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Criar indicador de status visual
function createStatusIndicator(status) {
    const icon = getStatusIcon(status);
    const cssClass = getStatusClass(status);
    return `<span class="status-indicator ${cssClass}">${icon}</span>`;
}

// Calcular tempo desde \u00faltima atualiza\u00e7\u00e3o
function timeSinceUpdate(lastUpdate) {
    if (!lastUpdate) return null;

    const now = new Date();
    const last = new Date(lastUpdate);
    const diff = Math.floor((now - last) / 1000);

    if (diff < 60) return `${diff}s`;
    if (diff < 3600) return `${Math.floor(diff / 60)}m`;
    return `${Math.floor(diff / 3600)}h`;
}

// Mostrar mensagem de erro
function showError(containerId, message) {
    const container = document.getElementById(containerId);
    if (container) {
        container.innerHTML = `
            <div class="error-message">
                <p>\u26A0 ${escapeHtml(message)}</p>
            </div>
        `;
    }
}

// Mostrar loading
function showLoading(containerId) {
    const container = document.getElementById(containerId);
    if (container) {
        container.innerHTML = '<p class="loading">Carregando...</p>';
    }
}

// Debounce function (para busca)
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}
