import React from 'react';

const RiskBadge = ({ riskLevel, level, score }) => {
    let currentRisk = (riskLevel || level || (score >= 0.8 ? "high" : score >= 0.5 ? "medium" : "low")).toLowerCase();
    const styles = {
        high: {
            background: '#fee2e2',
            color: '#991b1b',
            border: '1px solid #fca5a5',
        },
        medium: {
            background: '#fef9c3',
            color: '#854d0e',
            border: '1px solid #fde047',
        },
        low: {
            background: '#dcfce7',
            color: '#166534',
            border: '1px solid #86efac',
        },
    };

    const labels = {
        high: 'High Risk',
        medium: 'Medium Risk',
        low: 'Low Risk',
    };

    const style = styles[currentRisk] || styles.low;
    const label = labels[currentRisk] || 'Low Risk';

    return (
        <span style={{
            ...style,
            padding: '2px 10px',
            borderRadius: '12px',
            fontSize: '12px',
            fontWeight: '600',
            display: 'inline-block',
        }}>
            {label} {score !== undefined ? `(${(score * 100).toFixed(0)}%)` : ''}
        </span>
    );
};

export default RiskBadge;