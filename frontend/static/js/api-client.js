// API Client para BGP Monitor
// Gerencia todas as chamadas à API REST

class APIClient {
    constructor(baseURL = '') {
        this.baseURL = baseURL;
        this.defaultHeaders = {
            'Content-Type': 'application/json',
        };
    }

    // Método genérico para fazer requisições
    async request(endpoint, options = {}) {
        const url = `${this.baseURL}${endpoint}`;

        const config = {
            ...options,
            headers: {
                ...this.defaultHeaders,
                ...options.headers,
            },
        };

        try {
            const response = await fetch(url, config);

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            return await response.json();
        } catch (error) {
            console.error(`Erro na requisição ${endpoint}:`, error);
            throw error;
        }
    }

    // === Endpoints BGP ===

    async getBGPSessions(status = null) {
        let endpoint = '/api/bgp/sessions';
        if (status) {
            endpoint += `?status=${status}`;
        }
        return await this.request(endpoint);
    }

    async getBGPSession(peerIP) {
        return await this.request(`/api/bgp/sessions/${peerIP}`);
    }

    async getBGPStats() {
        return await this.request('/api/bgp/stats');
    }

    async getBGPHistory(peerIP, limit = 100) {
        return await this.request(`/api/bgp/history/${peerIP}?limit=${limit}`);
    }

    // === Endpoints Interfaces ===

    async getInterfaces(status = null) {
        let endpoint = '/api/interfaces';
        if (status) {
            endpoint += `?status=${status}`;
        }
        return await this.request(endpoint);
    }

    async getInterface(name) {
        return await this.request(`/api/interfaces/${encodeURIComponent(name)}`);
    }

    async getInterfaceStats(name) {
        return await this.request(`/api/interfaces/${encodeURIComponent(name)}/stats`);
    }

    async getInterfaceHistory(name, limit = 100) {
        return await this.request(`/api/interfaces/${encodeURIComponent(name)}/history?limit=${limit}`);
    }

    // === Endpoints Eventos ===

    async getEvents(filters = {}) {
        const params = new URLSearchParams();

        if (filters.event_type) params.append('event_type', filters.event_type);
        if (filters.severity) params.append('severity', filters.severity);
        if (filters.source) params.append('source', filters.source);
        if (filters.limit) params.append('limit', filters.limit);

        const queryString = params.toString();
        const endpoint = queryString ? `/api/events?${queryString}` : '/api/events';

        return await this.request(endpoint);
    }

    async getRecentEvents(limit = 50) {
        return await this.request(`/api/events/recent?limit=${limit}`);
    }

    async getCriticalEvents(limit = 50) {
        return await this.request(`/api/events/critical?limit=${limit}`);
    }

    async getEventsStats() {
        return await this.request('/api/events/stats');
    }
}

// Exportar instância global
const apiClient = new APIClient();
