import React from 'react';
import { useNavigate, useLocation } from 'react-router-dom';

const Navbar = () => {
    const navigate = useNavigate();
    const location = useLocation();

    const navItems = [
        { label: 'Dashboard', path: '/' },
        { label: 'Transactions', path: '/transactions' },
        { label: 'Admin Panel', path: '/admin' },
        { label: 'Consent Portal', path: '/consent' },
        { label: 'Drift Monitor', path: '/drift' },
    ];

    return (
        <nav style={{
            background: '#0f172a',
            padding: '0 32px',
            display: 'flex',
            alignItems: 'center',
            height: '64px',
            boxShadow: '0 1px 3px rgba(0,0,0,0.3)',
            position: 'sticky',
            top: 0,
            zIndex: 100,
        }}>
            <div style={{
                display: 'flex',
                alignItems: 'center',
                gap: '10px',
                marginRight: '48px',
                cursor: 'pointer',
            }} onClick={() => navigate('/')}>
                <div style={{
                    width: '32px',
                    height: '32px',
                    background: 'linear-gradient(135deg, #2563eb, #1d4ed8)',
                    borderRadius: '8px',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    boxShadow: '0 2px 8px rgba(37,99,235,0.4)',
                }}>
                    <span style={{ color: '#ffffff', fontSize: '16px', fontWeight: '800' }}>S</span>
                </div>
                <div>
                    <div style={{
                        color: '#ffffff',
                        fontSize: '16px',
                        fontWeight: '700',
                        letterSpacing: '0.02em',
                        lineHeight: '1.2',
                    }}>
                        SuRaksha
                    </div>
                    <div style={{
                        color: '#475569',
                        fontSize: '10px',
                        letterSpacing: '0.05em',
                        textTransform: 'uppercase',
                    }}>
                        Fraud Detection
                    </div>
                </div>
            </div>

            <div style={{ display: 'flex', gap: '4px', flex: 1 }}>
                {navItems.map((item) => {
                    const isActive = location.pathname === item.path;
                    return (
                        <button
                            key={item.path}
                            onClick={() => navigate(item.path)}
                            style={{
                                background: isActive ? '#1e3a5f' : 'transparent',
                                color: isActive ? '#60a5fa' : '#94a3b8',
                                border: 'none',
                                padding: '8px 16px',
                                borderRadius: '6px',
                                cursor: 'pointer',
                                fontSize: '14px',
                                fontWeight: isActive ? '600' : '400',
                                transition: 'all 0.15s',
                            }}
                            onMouseEnter={(e) => {
                                if (!isActive) e.currentTarget.style.color = '#e2e8f0';
                            }}
                            onMouseLeave={(e) => {
                                if (!isActive) e.currentTarget.style.color = '#94a3b8';
                            }}
                        >
                            {item.label}
                        </button>
                    );
                })}
            </div>

            <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
                <div style={{ textAlign: 'right' }}>
                    <div style={{ color: '#94a3b8', fontSize: '12px', fontWeight: '500' }}>
                        Abhishek Shandilya
                    </div>
                </div>
                <div style={{ width: '1px', height: '32px', background: '#1e293b' }} />
                <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                    <div style={{
                        width: '8px',
                        height: '8px',
                        background: '#22c55e',
                        borderRadius: '50%',
                        boxShadow: '0 0 6px rgba(34,197,94,0.5)',
                    }} />
                    <span style={{ color: '#64748b', fontSize: '12px' }}>
                        Live
                    </span>
                </div>
            </div>
        </nav>
    );
};

export default Navbar;