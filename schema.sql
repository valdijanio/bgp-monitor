-- Schema para BGP Monitor - Huawei NE8000
-- SQLite Database

-- Tabela de sessões BGP
CREATE TABLE IF NOT EXISTS bgp_sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    peer_ip TEXT NOT NULL UNIQUE,
    peer_asn TEXT NOT NULL,
    peer_description TEXT,
    status TEXT NOT NULL CHECK(status IN ('Established', 'Idle', 'Active', 'Connect', 'OpenSent', 'OpenConfirm', 'Down')),
    uptime_seconds INTEGER DEFAULT 0,
    prefixes_received INTEGER DEFAULT 0,
    prefixes_sent INTEGER DEFAULT 0,
    last_state_change TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Índices para bgp_sessions
CREATE INDEX IF NOT EXISTS idx_bgp_peer_ip ON bgp_sessions(peer_ip);
CREATE INDEX IF NOT EXISTS idx_bgp_status ON bgp_sessions(status);
CREATE INDEX IF NOT EXISTS idx_bgp_last_updated ON bgp_sessions(last_updated);

-- Tabela de interfaces
CREATE TABLE IF NOT EXISTS interfaces (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    description TEXT,
    status TEXT NOT NULL CHECK(status IN ('up', 'down', 'admin_down')),
    bandwidth_capacity INTEGER DEFAULT 0,
    bandwidth_in_bps INTEGER DEFAULT 0,
    bandwidth_out_bps INTEGER DEFAULT 0,
    packets_in_pps INTEGER DEFAULT 0,
    packets_out_pps INTEGER DEFAULT 0,
    errors_in INTEGER DEFAULT 0,
    errors_out INTEGER DEFAULT 0,
    discards_in INTEGER DEFAULT 0,
    discards_out INTEGER DEFAULT 0,
    utilization_in_percent REAL DEFAULT 0.0,
    utilization_out_percent REAL DEFAULT 0.0,
    last_state_change TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Índices para interfaces
CREATE INDEX IF NOT EXISTS idx_interface_name ON interfaces(name);
CREATE INDEX IF NOT EXISTS idx_interface_status ON interfaces(status);
CREATE INDEX IF NOT EXISTS idx_interface_last_updated ON interfaces(last_updated);

-- Tabela de eventos
CREATE TABLE IF NOT EXISTS events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    event_type TEXT NOT NULL CHECK(event_type IN ('bgp_up', 'bgp_down', 'interface_up', 'interface_down', 'high_errors', 'flapping', 'system', 'info')),
    severity TEXT NOT NULL CHECK(severity IN ('critical', 'warning', 'info')),
    source TEXT NOT NULL,
    message TEXT NOT NULL,
    details TEXT
);

-- Índices para events
CREATE INDEX IF NOT EXISTS idx_event_timestamp ON events(timestamp);
CREATE INDEX IF NOT EXISTS idx_event_type ON events(event_type);
CREATE INDEX IF NOT EXISTS idx_event_severity ON events(severity);
CREATE INDEX IF NOT EXISTS idx_event_source ON events(source);

-- Tabela de histórico de status BGP (para gráficos temporais)
CREATE TABLE IF NOT EXISTS bgp_status_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    peer_ip TEXT NOT NULL,
    status TEXT NOT NULL,
    prefixes_received INTEGER DEFAULT 0,
    prefixes_sent INTEGER DEFAULT 0,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (peer_ip) REFERENCES bgp_sessions(peer_ip) ON DELETE CASCADE
);

-- Índices para bgp_status_history
CREATE INDEX IF NOT EXISTS idx_bgp_history_peer ON bgp_status_history(peer_ip);
CREATE INDEX IF NOT EXISTS idx_bgp_history_timestamp ON bgp_status_history(timestamp);

-- Tabela de histórico de tráfego de interfaces (para gráficos temporais)
CREATE TABLE IF NOT EXISTS interface_traffic_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    interface_name TEXT NOT NULL,
    bandwidth_in_bps INTEGER DEFAULT 0,
    bandwidth_out_bps INTEGER DEFAULT 0,
    packets_in_pps INTEGER DEFAULT 0,
    packets_out_pps INTEGER DEFAULT 0,
    errors_in INTEGER DEFAULT 0,
    errors_out INTEGER DEFAULT 0,
    utilization_in_percent REAL DEFAULT 0.0,
    utilization_out_percent REAL DEFAULT 0.0,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (interface_name) REFERENCES interfaces(name) ON DELETE CASCADE
);

-- Índices para interface_traffic_history
CREATE INDEX IF NOT EXISTS idx_traffic_history_interface ON interface_traffic_history(interface_name);
CREATE INDEX IF NOT EXISTS idx_traffic_history_timestamp ON interface_traffic_history(timestamp);

-- Tabela de comandos SSH executados (auditoria)
CREATE TABLE IF NOT EXISTS ssh_commands_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    command TEXT NOT NULL,
    execution_time_ms INTEGER,
    success BOOLEAN NOT NULL,
    error_message TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Índice para ssh_commands_log
CREATE INDEX IF NOT EXISTS idx_ssh_log_timestamp ON ssh_commands_log(timestamp);
CREATE INDEX IF NOT EXISTS idx_ssh_log_success ON ssh_commands_log(success);
