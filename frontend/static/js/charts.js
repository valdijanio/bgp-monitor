// Gerenciamento de gráficos com Chart.js
// BGP Monitor - Dashboard de visualização

// Configuração global do Chart.js
Chart.defaults.font.family = "'Segoe UI', Tahoma, Geneva, Verdana, sans-serif";
Chart.defaults.color = '#666';
Chart.defaults.plugins.legend.display = true;
Chart.defaults.plugins.legend.position = 'bottom';

// Paleta de cores
const COLORS = {
    green: '#10b981',
    red: '#ef4444',
    yellow: '#f59e0b',
    blue: '#3b82f6',
    purple: '#8b5cf6',
    orange: '#f97316',
    cyan: '#06b6d4',
    pink: '#ec4899'
};

// Instâncias dos gráficos
let bgpStatusChart = null;
let interfaceUtilizationChart = null;
let trafficHistoryChart = null;
let eventsTimelineChart = null;

// === GRÁFICO 1: Pizza - Distribuição de Status BGP ===

function createBGPStatusChart() {
    const ctx = document.getElementById('bgp-status-chart');
    if (!ctx) return;

    if (bgpStatusChart) {
        bgpStatusChart.destroy();
    }

    bgpStatusChart = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: ['Established', 'Down', 'Idle'],
            datasets: [{
                label: 'Sessões BGP',
                data: [0, 0, 0],
                backgroundColor: [
                    COLORS.green,
                    COLORS.red,
                    COLORS.yellow
                ],
                borderWidth: 2,
                borderColor: '#fff'
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            plugins: {
                legend: {
                    position: 'bottom'
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            const label = context.label || '';
                            const value = context.parsed || 0;
                            const total = context.dataset.data.reduce((a, b) => a + b, 0);
                            const percentage = total > 0 ? ((value / total) * 100).toFixed(1) : 0;
                            return `${label}: ${value} (${percentage}%)`;
                        }
                    }
                }
            }
        }
    });
}

async function updateBGPStatusChart() {
    if (!bgpStatusChart) return;

    try {
        const stats = await apiClient.getBGPStats();

        const established = stats.established_sessions || 0;
        const down = stats.down_sessions || 0;
        const idle = stats.idle_sessions || 0;

        bgpStatusChart.data.datasets[0].data = [established, down, idle];
        bgpStatusChart.update('none'); // Update sem animação

    } catch (error) {
        console.error('Erro ao atualizar gráfico BGP:', error);
    }
}

// === GRÁFICO 2: Barras - Top Interfaces por Utilização ===

function createInterfaceUtilizationChart() {
    const ctx = document.getElementById('interface-utilization-chart');
    if (!ctx) return;

    if (interfaceUtilizationChart) {
        interfaceUtilizationChart.destroy();
    }

    interfaceUtilizationChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: [],
            datasets: [
                {
                    label: 'Utilização IN (%)',
                    data: [],
                    backgroundColor: COLORS.blue,
                    borderColor: COLORS.blue,
                    borderWidth: 1
                },
                {
                    label: 'Utilização OUT (%)',
                    data: [],
                    backgroundColor: COLORS.purple,
                    borderColor: COLORS.purple,
                    borderWidth: 1
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            scales: {
                y: {
                    beginAtZero: true,
                    max: 100,
                    ticks: {
                        callback: function(value) {
                            return value + '%';
                        }
                    }
                }
            },
            plugins: {
                legend: {
                    position: 'bottom'
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            return context.dataset.label + ': ' + context.parsed.y.toFixed(1) + '%';
                        }
                    }
                }
            }
        }
    });
}

async function updateInterfaceUtilizationChart() {
    if (!interfaceUtilizationChart) return;

    try {
        const interfaces = await apiClient.getInterfaces();

        // Ordenar por utilização total (IN + OUT) e pegar top 10
        const sorted = interfaces
            .map(iface => ({
                name: iface.name,
                utilizationIn: iface.utilization_in_percent || 0,
                utilizationOut: iface.utilization_out_percent || 0,
                total: (iface.utilization_in_percent || 0) + (iface.utilization_out_percent || 0)
            }))
            .sort((a, b) => b.total - a.total)
            .slice(0, 10);

        const labels = sorted.map(i => i.name);
        const utilizationIn = sorted.map(i => i.utilizationIn);
        const utilizationOut = sorted.map(i => i.utilizationOut);

        interfaceUtilizationChart.data.labels = labels;
        interfaceUtilizationChart.data.datasets[0].data = utilizationIn;
        interfaceUtilizationChart.data.datasets[1].data = utilizationOut;
        interfaceUtilizationChart.update('none');

    } catch (error) {
        console.error('Erro ao atualizar gráfico de interfaces:', error);
    }
}

// === GRÁFICO 3: Linha - Histórico de Tráfego ===

function createTrafficHistoryChart() {
    const ctx = document.getElementById('traffic-history-chart');
    if (!ctx) return;

    if (trafficHistoryChart) {
        trafficHistoryChart.destroy();
    }

    trafficHistoryChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: [],
            datasets: [
                {
                    label: 'Tráfego IN (Mbps)',
                    data: [],
                    borderColor: COLORS.green,
                    backgroundColor: COLORS.green + '20',
                    borderWidth: 2,
                    fill: true,
                    tension: 0.4
                },
                {
                    label: 'Tráfego OUT (Mbps)',
                    data: [],
                    borderColor: COLORS.blue,
                    backgroundColor: COLORS.blue + '20',
                    borderWidth: 2,
                    fill: true,
                    tension: 0.4
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            interaction: {
                mode: 'index',
                intersect: false
            },
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: {
                        callback: function(value) {
                            return value.toLocaleString('pt-BR') + ' Mbps';
                        }
                    }
                }
            },
            plugins: {
                legend: {
                    position: 'bottom'
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            return context.dataset.label + ': ' +
                                   context.parsed.y.toLocaleString('pt-BR') + ' Mbps';
                        }
                    }
                }
            }
        }
    });
}

async function updateTrafficHistoryChart() {
    if (!trafficHistoryChart) return;

    try {
        // Pegar todas interfaces (UP primeiro)
        const interfaces = await apiClient.getInterfaces();

        if (!interfaces || interfaces.length === 0) {
            console.warn('Nenhuma interface encontrada');
            // Limpar gráfico
            trafficHistoryChart.data.labels = [];
            trafficHistoryChart.data.datasets[0].data = [];
            trafficHistoryChart.data.datasets[1].data = [];
            trafficHistoryChart.update('none');
            return;
        }

        // Ordenar: UP primeiro, depois DOWN
        const sortedInterfaces = interfaces.sort((a, b) => {
            if (a.status === 'up' && b.status !== 'up') return -1;
            if (a.status !== 'up' && b.status === 'up') return 1;
            return 0;
        });

        // Tentar pegar histórico da primeira interface que tiver dados
        let history = [];
        let selectedInterface = null;

        for (const iface of sortedInterfaces) {
            try {
                const ifaceHistory = await apiClient.getInterfaceHistory(iface.name, 20);
                if (ifaceHistory && ifaceHistory.length > 0) {
                    history = ifaceHistory;
                    selectedInterface = iface;
                    break;
                }
            } catch (e) {
                // Continuar tentando próxima interface
                continue;
            }
        }

        if (!history || history.length === 0) {
            console.warn('Nenhuma interface com histórico disponível');
            // Limpar gráfico
            trafficHistoryChart.data.labels = [];
            trafficHistoryChart.data.datasets[0].data = [];
            trafficHistoryChart.data.datasets[1].data = [];
            trafficHistoryChart.data.datasets[0].label = 'Tráfego IN (Mbps)';
            trafficHistoryChart.data.datasets[1].label = 'Tráfego OUT (Mbps)';
            trafficHistoryChart.update('none');
            return;
        }

        // Ordenar por timestamp (mais antigo primeiro)
        const sorted = history.sort((a, b) =>
            new Date(a.timestamp) - new Date(b.timestamp)
        );

        const labels = sorted.map(h => {
            const date = new Date(h.timestamp);
            return date.toLocaleTimeString('pt-BR', {
                hour: '2-digit',
                minute: '2-digit'
            });
        });

        const trafficIn = sorted.map(h => (h.bandwidth_in_bps / 1e6).toFixed(2));
        const trafficOut = sorted.map(h => (h.bandwidth_out_bps / 1e6).toFixed(2));

        trafficHistoryChart.data.labels = labels;
        trafficHistoryChart.data.datasets[0].data = trafficIn;
        trafficHistoryChart.data.datasets[0].label = `${selectedInterface.name} - IN (Mbps)`;
        trafficHistoryChart.data.datasets[1].data = trafficOut;
        trafficHistoryChart.data.datasets[1].label = `${selectedInterface.name} - OUT (Mbps)`;
        trafficHistoryChart.update('none');

    } catch (error) {
        console.error('Erro ao atualizar histórico de tráfego:', error);
    }
}

// === GRÁFICO 4: Linha/Área - Timeline de Eventos ===

function createEventsTimelineChart() {
    const ctx = document.getElementById('events-timeline-chart');
    if (!ctx) return;

    if (eventsTimelineChart) {
        eventsTimelineChart.destroy();
    }

    eventsTimelineChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: [],
            datasets: [
                {
                    label: 'Critical',
                    data: [],
                    borderColor: COLORS.red,
                    backgroundColor: COLORS.red + '30',
                    borderWidth: 2,
                    fill: true,
                    tension: 0.4
                },
                {
                    label: 'Warning',
                    data: [],
                    borderColor: COLORS.yellow,
                    backgroundColor: COLORS.yellow + '30',
                    borderWidth: 2,
                    fill: true,
                    tension: 0.4
                },
                {
                    label: 'Info',
                    data: [],
                    borderColor: COLORS.blue,
                    backgroundColor: COLORS.blue + '30',
                    borderWidth: 2,
                    fill: true,
                    tension: 0.4
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            interaction: {
                mode: 'index',
                intersect: false
            },
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: {
                        stepSize: 1
                    }
                }
            },
            plugins: {
                legend: {
                    position: 'bottom'
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            return context.dataset.label + ': ' + context.parsed.y + ' eventos';
                        }
                    }
                }
            }
        }
    });
}

async function updateEventsTimelineChart() {
    if (!eventsTimelineChart) return;

    try {
        const events = await apiClient.getRecentEvents(100);

        if (!events || events.length === 0) {
            console.warn('Nenhum evento encontrado');
            return;
        }

        // Agrupar eventos por hora e severidade
        const eventsByHour = {};

        events.forEach(event => {
            const date = new Date(event.timestamp);
            const hourKey = `${date.getHours().toString().padStart(2, '0')}:00`;

            if (!eventsByHour[hourKey]) {
                eventsByHour[hourKey] = {
                    critical: 0,
                    warning: 0,
                    info: 0
                };
            }

            const severity = event.severity.toLowerCase();
            if (severity === 'critical') {
                eventsByHour[hourKey].critical++;
            } else if (severity === 'warning') {
                eventsByHour[hourKey].warning++;
            } else {
                eventsByHour[hourKey].info++;
            }
        });

        // Ordenar por hora
        const hours = Object.keys(eventsByHour).sort();
        const critical = hours.map(h => eventsByHour[h].critical);
        const warning = hours.map(h => eventsByHour[h].warning);
        const info = hours.map(h => eventsByHour[h].info);

        eventsTimelineChart.data.labels = hours;
        eventsTimelineChart.data.datasets[0].data = critical;
        eventsTimelineChart.data.datasets[1].data = warning;
        eventsTimelineChart.data.datasets[2].data = info;
        eventsTimelineChart.update('none');

    } catch (error) {
        console.error('Erro ao atualizar timeline de eventos:', error);
    }
}

// === FUNÇÕES DE INICIALIZAÇÃO E ATUALIZAÇÃO ===

function initializeCharts() {
    console.log('Inicializando gráficos...');

    createBGPStatusChart();
    createInterfaceUtilizationChart();
    createTrafficHistoryChart();
    createEventsTimelineChart();

    console.log('Gráficos inicializados');
}

async function updateAllCharts() {
    console.log('Atualizando todos os gráficos...');

    try {
        await Promise.all([
            updateBGPStatusChart(),
            updateInterfaceUtilizationChart(),
            updateTrafficHistoryChart(),
            updateEventsTimelineChart()
        ]);

        console.log('Gráficos atualizados com sucesso');
    } catch (error) {
        console.error('Erro ao atualizar gráficos:', error);
    }
}

// Exportar funções globais
window.initializeCharts = initializeCharts;
window.updateAllCharts = updateAllCharts;
