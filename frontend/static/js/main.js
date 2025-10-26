// BGP Monitor - Frontend JavaScript
// Gerencia o dashboard principal

// Configura\u00e7\u00e3o
const UPDATE_INTERVAL = 10000; // 10 segundos
let lastUpdate = null;
let updateTimer = null;

// Inicializa\u00e7\u00e3o
document.addEventListener('DOMContentLoaded', function() {
    console.log('BGP Monitor iniciado');

    // Inicializar gráficos
    if (typeof initializeCharts === 'function') {
        initializeCharts();
    }

    // Carregar dados iniciais
    loadDashboardData();

    // Atualizar periodicamente
    startAutoUpdate();

    // Bot\u00e3o de refresh manual (se existir)
    const refreshBtn = document.getElementById('refresh-btn');
    if (refreshBtn) {
        refreshBtn.addEventListener('click', () => {
            loadDashboardData();
        });
    }
});

// Iniciar atualiza\u00e7\u00e3o autom\u00e1tica
function startAutoUpdate() {
    if (updateTimer) {
        clearInterval(updateTimer);
    }
    updateTimer = setInterval(loadDashboardData, UPDATE_INTERVAL);
}

// Parar atualiza\u00e7\u00e3o autom\u00e1tica
function stopAutoUpdate() {
    if (updateTimer) {
        clearInterval(updateTimer);
        updateTimer = null;
    }
}

// Carregar todos os dados do dashboard
async function loadDashboardData() {
    console.log('Carregando dados do dashboard...');

    try {
        // Carregar em paralelo para melhor performance
        await Promise.all([
            loadBGPStats(),
            loadBGPSessions(),
            loadInterfaces(),
            loadRecentEvents()
        ]);

        // Atualizar gráficos
        if (typeof updateAllCharts === 'function') {
            await updateAllCharts();
        }

        // Atualizar timestamp da \u00faltima atualiza\u00e7\u00e3o
        lastUpdate = new Date();
        updateLastUpdateIndicator();

    } catch (error) {
        console.error('Erro ao carregar dados do dashboard:', error);
        handleDashboardError(error);
    }
}

// Carregar estat\u00edsticas BGP (cards do topo)
async function loadBGPStats() {
    try {
        const stats = await apiClient.getBGPStats();

        // Atualizar cards
        document.getElementById('bgp-total').textContent = stats.total_sessions || 0;
        document.getElementById('bgp-up').textContent = stats.established_sessions || 0;
        document.getElementById('bgp-down').textContent = stats.down_sessions || 0;

        // Atualizar interfaces UP (contar do retorno de interfaces)
        const interfaces = await apiClient.getInterfaces('up');
        document.getElementById('interfaces-up').textContent = interfaces.length || 0;

    } catch (error) {
        console.error('Erro ao carregar estat\u00edsticas BGP:', error);
        // Manter valores existentes em caso de erro
    }
}

// Carregar sess\u00f5es BGP
async function loadBGPSessions() {
    const container = document.getElementById('bgp-sessions');

    try {
        showLoading('bgp-sessions');

        const sessions = await apiClient.getBGPSessions();

        if (!sessions || sessions.length === 0) {
            container.innerHTML = '<p class="no-data">Nenhuma sess\u00e3o BGP encontrada</p>';
            return;
        }

        // Renderizar tabela de sess\u00f5es
        let html = `
            <table class="data-table">
                <thead>
                    <tr>
                        <th>Status</th>
                        <th>Peer IP</th>
                        <th>ASN</th>
                        <th>Uptime</th>
                        <th>Prefixos RX</th>
                        <th>Prefixos TX</th>
                    </tr>
                </thead>
                <tbody>
        `;

        sessions.forEach(session => {
            html += `
                <tr class="${getStatusClass(session.status)}">
                    <td>${createStatusIndicator(session.status)} ${session.status}</td>
                    <td><strong>${escapeHtml(session.peer_ip)}</strong></td>
                    <td>${escapeHtml(session.peer_asn)}</td>
                    <td>${formatUptime(session.uptime_seconds)}</td>
                    <td>${session.prefixes_received.toLocaleString('pt-BR')}</td>
                    <td>${session.prefixes_sent.toLocaleString('pt-BR')}</td>
                </tr>
            `;
        });

        html += `
                </tbody>
            </table>
        `;

        container.innerHTML = html;

    } catch (error) {
        console.error('Erro ao carregar sess\u00f5es BGP:', error);
        showError('bgp-sessions', 'Erro ao carregar sess\u00f5es BGP. Tente novamente.');
    }
}

// Carregar interfaces
async function loadInterfaces() {
    const container = document.getElementById('interfaces');

    try {
        showLoading('interfaces');

        const interfaces = await apiClient.getInterfaces();

        if (!interfaces || interfaces.length === 0) {
            container.innerHTML = '<p class="no-data">Nenhuma interface encontrada</p>';
            return;
        }

        // Renderizar tabela de interfaces
        let html = `
            <table class="data-table">
                <thead>
                    <tr>
                        <th>Status</th>
                        <th>Interface</th>
                        <th>Descri\u00e7\u00e3o</th>
                        <th>Banda IN</th>
                        <th>Banda OUT</th>
                        <th>Utiliza\u00e7\u00e3o IN</th>
                        <th>Utiliza\u00e7\u00e3o OUT</th>
                        <th>Erros</th>
                    </tr>
                </thead>
                <tbody>
        `;

        interfaces.forEach(iface => {
            const utilizationInClass = iface.utilization_in_percent > 80 ? 'high-usage' : '';
            const utilizationOutClass = iface.utilization_out_percent > 80 ? 'high-usage' : '';

            html += `
                <tr class="${getStatusClass(iface.status)}">
                    <td>${createStatusIndicator(iface.status)} ${iface.status}</td>
                    <td><strong>${escapeHtml(iface.name)}</strong></td>
                    <td>${escapeHtml(iface.description || '-')}</td>
                    <td>${formatBytes(iface.bandwidth_in_bps)}</td>
                    <td>${formatBytes(iface.bandwidth_out_bps)}</td>
                    <td class="${utilizationInClass}">${iface.utilization_in_percent.toFixed(1)}%</td>
                    <td class="${utilizationOutClass}">${iface.utilization_out_percent.toFixed(1)}%</td>
                    <td>${iface.total_errors.toLocaleString('pt-BR')}</td>
                </tr>
            `;
        });

        html += `
                </tbody>
            </table>
        `;

        container.innerHTML = html;

    } catch (error) {
        console.error('Erro ao carregar interfaces:', error);
        showError('interfaces', 'Erro ao carregar interfaces. Tente novamente.');
    }
}

// Carregar eventos recentes
async function loadRecentEvents() {
    const container = document.getElementById('events');

    try {
        showLoading('events');

        const events = await apiClient.getRecentEvents(20);

        if (!events || events.length === 0) {
            container.innerHTML = '<p class="no-data">Nenhum evento registrado</p>';
            return;
        }

        // Renderizar lista de eventos
        let html = '<ul class="events-list">';

        events.forEach(event => {
            const severityColor = getSeverityColor(event.severity);

            html += `
                <li class="event-item">
                    <span class="event-severity" style="background-color: ${severityColor}">
                        ${event.severity}
                    </span>
                    <div class="event-content">
                        <strong>${escapeHtml(event.message)}</strong>
                        <div class="event-meta">
                            <span>${event.event_type}</span> \u2022
                            <span>${formatTimestamp(event.timestamp)}</span> \u2022
                            <span>${escapeHtml(event.source)}</span>
                        </div>
                    </div>
                </li>
            `;
        });

        html += '</ul>';

        container.innerHTML = html;

    } catch (error) {
        console.error('Erro ao carregar eventos:', error);
        showError('events', 'Erro ao carregar eventos. Tente novamente.');
    }
}

// Atualizar indicador de \u00faltima atualiza\u00e7\u00e3o
function updateLastUpdateIndicator() {
    const indicator = document.getElementById('last-update');
    if (indicator && lastUpdate) {
        const timeAgo = timeSinceUpdate(lastUpdate);
        indicator.textContent = `\u00daltima atualiza\u00e7\u00e3o: ${timeAgo}`;
    }
}

// Tratar erros gerais do dashboard
function handleDashboardError(error) {
    console.error('Erro no dashboard:', error);

    // Exibir mensagem de erro amig\u00e1vel
    const errorBanner = document.createElement('div');
    errorBanner.className = 'error-banner';
    errorBanner.innerHTML = `
        <p>\u26A0 N\u00e3o foi poss\u00edvel carregar alguns dados. Verifique a conex\u00e3o.</p>
    `;

    // Adicionar no topo do container principal
    const main = document.querySelector('main.container');
    if (main && !document.querySelector('.error-banner')) {
        main.insertBefore(errorBanner, main.firstChild);

        // Remover ap\u00f3s 5 segundos
        setTimeout(() => {
            errorBanner.remove();
        }, 5000);
    }
}

// Atualizar indicador de \u00faltima atualiza\u00e7\u00e3o a cada segundo
setInterval(updateLastUpdateIndicator, 1000);
