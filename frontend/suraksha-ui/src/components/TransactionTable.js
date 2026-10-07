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
        if (!timestamp) return '-';
        return new Date(timestamp).toLocaleString('en-IN', {
            day: '2-digit',
            month: 'short',
            year: 'numeric',
            hour: '2-digit',
            minute: '2-digit',
        });
    };

    const handleDownloadStr = (e, txnId) => {
        e.stopPropagation(); // Prevents triggering the row click navigation
        window.open(`https://suraksha-aml.onrender.com/transactions/${txnId}/report`, '_blank');
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
                        {['Transaction ID', 'User ID', 'Amount', 'Channel', 'Risk Level', 'Score', 'Time', 'Compliance Action'].map((header) => (
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
                        const score = txn.anomaly_score ?? 0;
                        const riskLevel = txn.risk_level || getRiskLevel(score);
                        const isFlagged = riskLevel === 'high' || riskLevel === 'medium';

                        return (
                            <tr
                                key={txn.txn_id || index}
                                onClick={() => navigate(`/transaction/${txn.txn_id}`)}
                                style={{
                                    borderBottom: '1px solid #f3f4f6',
                                    cursor: 'pointer',
                                    transition: 'background-color 0.15s ease',
                                    backgroundColor: index % 2 === 0 ? '#ffffff' : '#fafafa',
                                }}
                                onMouseEnter={(e) => (e.currentTarget.style.backgroundColor = '#f0fdf4')}
                                onMouseLeave={(e) => (e.currentTarget.style.backgroundColor = index % 2 === 0 ? '#ffffff' : '#fafafa')}
                            >
                                <td style={{ padding: '12px 16px', fontWeight: '600', color: '#111827' }}>
                                    {txn.txn_id}
                                </td>
                                <td style={{ padding: '12px 16px', color: '#4b5563' }}>
                                    {txn.user_id}
                                </td>
                                <td style={{ padding: '12px 16px', fontWeight: '500', color: '#111827' }}>
                                    {formatAmount(txn.amount)}
                                </td>
                                <td style={{ padding: '12px 16px', color: '#4b5563' }}>
                                    {txn.channel || 'UPI'}
                                </td>
                                <td style={{ padding: '12px 16px' }}>
                                    <RiskBadge riskLevel={riskLevel} score={score} />
                                </td>
                                <td style={{ padding: '12px 16px', color: '#374151', fontWeight: '500' }}>
                                    {(score * 100).toFixed(1)}%
                                </td>
                                <td style={{ padding: '12px 16px', color: '#6b7280', fontSize: '13px' }}>
                                    {formatTime(txn.created_at || txn.timestamp)}
                                </td>
                                <td style={{ padding: '12px 16px' }}>
                                    {isFlagged ? (
                                        <button
                                            onClick={(e) => handleDownloadStr(e, txn.txn_id)}
                                            style={{
                                                backgroundColor: riskLevel === 'high' ? '#fee2e2' : '#fef3c7',
                                                color: riskLevel === 'high' ? '#991b1b' : '#92400e',
                                                border: `1px solid ${riskLevel === 'high' ? '#f87171' : '#fcd34d'}`,
                                                padding: '5px 10px',
                                                borderRadius: '6px',
                                                fontSize: '12px',
                                                fontWeight: '600',
                                                cursor: 'pointer',
                                                display: 'inline-flex',
                                                alignItems: 'center',
                                                gap: '4px',
                                            }}
                                            title="Generate official FIU-IND report"
                                        >
                                            📄 Download STR
                                        </button>
                                    ) : (
                                        <span style={{ color: '#9ca3af', fontSize: '12px' }}>Pass</span>
                                    )}
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