import React from 'react';

const StatsCard = ({ title, value, subtitle, color }) => {
    const borderColors = {
        red: '#ef4444',
        yellow: '#f59e0b',
        green: '#22c55e',
        blue: '#3b82f6',
    };

    const borderColor = borderColors[color] || borderColors.blue;

    return (
        <div style={{
            background: '#ffffff',
            border: '1px solid #e5e7eb',
            borderLeft: `4px solid ${borderColor}`,
            borderRadius: '8px',
            padding: '20px 24px',
            flex: 1,
            minWidth: '180px',
        }}>
            <p style={{
                fontSize: '13px',
                color: '#6b7280',
                margin: '0 0 8px 0',
                fontWeight: '500',
                textTransform: 'uppercase',
                letterSpacing: '0.05em',
            }}>
                {title}
            </p>
            <p style={{
                fontSize: '28px',
                fontWeight: '700',
                color: '#111827',
                margin: '0 0 4px 0',
            }}>
                {value}
            </p>
            {subtitle && (
                <p style={{
                    fontSize: '12px',
                    color: '#9ca3af',
                    margin: '0',
                }}>
                    {subtitle}
                </p>
            )}
        </div>
    );
};

export default StatsCard;