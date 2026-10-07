import React from 'react';

const Footer = () => {
    return (
        <div style={{
            background: '#0f172a',
            borderTop: '1px solid #1e293b',
            padding: '16px 32px',
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
        }}>
            <div>
                <span style={{ color: '#475569', fontSize: '12px' }}>
                    SuRaksha Fraud Detection System v1.0
                </span>
            </div>
            <div>
                <span style={{ color: '#475569', fontSize: '12px' }}>
                    Developed by
                </span>
                <span style={{ color: '#60a5fa', fontSize: '12px', fontWeight: '600', marginLeft: '4px' }}>
                    Abhishek Shandilya
                </span>
            </div>
        </div>
    );
};

export default Footer;