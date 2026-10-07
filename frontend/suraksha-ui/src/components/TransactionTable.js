import React from 'react';
import { useNavigate } from 'react-router-dom';
import RiskBadge from './RiskBadge';

const TransactionTable = ({ transactions, loading }) => {
    const navigate = useNavigate();

    if (loading) {
        return (
            <div style={{ padding: '40px', textAlign: 'center', color: '#6b7280' }}>
                Loading transactions...
            </div>
        );
    }

    if (!transactions || transactions.length === 0) {
        return (
            <div style={{ padding: '40px', textAlign: 'center', color: '#6b7280' }}>
                No transactions found.
            </div>
        );
    }

    const getRiskLevel = (score) => {
        if (score >= 0.8) return 'high';
        if (score >= 0.5) return 'medium';
        return 'low';
    };

    const formatAmount = (amount) => {
        return new Intl.NumberFormat('en-IN', {
            style: 'currency',
            currency: 'INR',
            maximumFractionDigits: 0,
        }).format(amount);
    };

    const formatTime = (timestamp) => {
        return new Date(timestamp).toLocaleString('en-IN', {
            day: '2-digit',
            month: 'short',
            year: 'numeric',
            hour: '2-digit',
            minute: '2-digit',
        });
    };

    return (
        <div style={{ overflowX: 'auto' }}>
            <table style={{
                width: '100%',
                borderCollapse: 'collapse',
                fontSize: '14px',
            }}>
                <thead>
                    <tr style={{ background: '#f9fafb', borderBottom: '2px solid #e5e7eb' }}>
                        {['Transaction ID', 'User ID', 'Amount', 'City', 'Category', 'Risk Level', 'Score', 'Time'].map((header) => (
                            <th key={header} style={{
                                padding: '12px 16px',
                                textAlign: 'left',
                                fontWeight: '600',
                                color: '#374151',
                                fontSize: '13px',
                                textTransform: 'uppercase',
                                letterSpacing: '0.05em',
                            }}>
                                {header}
                            </th>
                        ))}
                    </tr>
                </thead>
                <tbody>
                    {transactions.map((txn, index) => {
                        const riskLevel = getRiskLevel(txn.anomaly_score);
                        return (
                            <tr
                                key={txn.txn_id}
                                onClick={() => navigate(`/transaction/${txn.txn_id}`)}
                                style={{
                                    borderBottom: '1px solid #f3f4f6',
                                    cursor: 'pointer',
                                    background: index % 2 === 0 ? '#ffffff' : '#fafafa',
                                    transition: 'background 0.15s',
                                }}
                                onMouseEnter={(e) => e.currentTarget.style.background = '#f0f9ff'}
                                onMouseLeave={(e) => e.currentTarget.style.background = index % 2 === 0 ? '#ffffff' : '#fafafa'}
                            >
                                <td style={{ padding: '12px 16px', color: '#2563eb', fontWeight: '500' }}>
                                    {txn.txn_id}
                                </td>
                                <td style={{ padding: '12px 16px', color: '#374151' }}>
                                    {txn.user_id}
                                </td>
                                <td style={{ padding: '12px 16px', fontWeight: '600', color: '#111827' }}>
                                    {formatAmount(txn.amount)}
                                </td>
                                <td style={{ padding: '12px 16px', color: '#374151' }}>
                                    {txn.city}
                                </td>
                                <td style={{ padding: '12px 16px', color: '#374151', textTransform: 'capitalize' }}>
                                    {txn.merchant_category}
                                </td>
                                <td style={{ padding: '12px 16px' }}>
                                    <RiskBadge riskLevel={riskLevel} score={txn.anomaly_score} />
                                </td>
                                <td style={{ padding: '12px 16px', fontWeight: '600', color: riskLevel === 'high' ? '#ef4444' : riskLevel === 'medium' ? '#f59e0b' : '#22c55e' }}>
                                    {(txn.anomaly_score * 100).toFixed(1)}%
                                </td>
                                <td style={{ padding: '12px 16px', color: '#6b7280', fontSize: '13px' }}>
                                    {formatTime(txn.timestamp)}
                                </td>
                            </tr>
                        );
                    })}
                </tbody>
            </table>
        </div>
    );
};

export default TransactionTable;