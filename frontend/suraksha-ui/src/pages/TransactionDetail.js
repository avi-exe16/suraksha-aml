import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import RiskBadge from '../components/RiskBadge';
import ShapChart from '../components/ShapChart';
import { fetchTransactionById, fetchUserTransactions } from '../utils/api';

const TransactionDetail = () => {
    const { txnId } = useParams();
    const navigate = useNavigate();
    const [transaction, setTransaction] = useState(null);
    const [userHistory, setUserHistory] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    useEffect(() => {
        loadTransaction();
    }, [txnId]); // eslint-disable-line react-hooks/exhaustive-deps

    const loadTransaction = async () => {
        try {
            setLoading(true);
            const txn = await fetchTransactionById(txnId);
            setTransaction(txn);
            const history = await fetchUserTransactions(txn.user_id);
            setUserHistory(history.transactions.slice(0, 10));
            setError(null);
        } catch (err) {
            setError('Transaction not found.');
        } finally {
            setLoading(false);
        }
    };

    const formatCurrency = (amount) => {
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
const handleDownloadReport = () => {
        window.open(`https://suraksha-aml.onrender.com/transactions/${txnId}/report`, '_blank');
    };
    const getRiskLevel = (score) => {
        if (score >= 0.8) return 'high';
        if (score >= 0.5) return 'medium';
        return 'low';
    };

    const getActionLabel = (score) => {
        if (score >= 0.8) return 'Transaction Blocked';
        if (score >= 0.5) return 'Step-up Authentication Triggered';
        return 'Transaction Approved';
    };

    const getActionColor = (score) => {
        if (score >= 0.8) return { background: '#fee2e2', color: '#991b1b', border: '1px solid #fca5a5' };
        if (score >= 0.5) return { background: '#fef9c3', color: '#854d0e', border: '1px solid #fde047' };
        return { background: '#dcfce7', color: '#166534', border: '1px solid #86efac' };
    };

    if (loading) {
        return (
            <div style={{ padding: '40px', textAlign: 'center', color: '#6b7280' }}>
                Loading transaction details...
            </div>
        );
    }

    if (error || !transaction) {
        return (
            <div style={{ padding: '40px', textAlign: 'center', color: '#ef4444' }}>
                {error || 'Transaction not found.'}
            </div>
        );
    }

    const riskLevel = getRiskLevel(transaction.anomaly_score);
    const actionStyle = getActionColor(transaction.anomaly_score);

    const shapImportance = [
        { feature: 'amount_vs_user_avg', value: transaction.amount_vs_user_avg, importance: 0.226 },
        { feature: 'km_from_last_txn', value: transaction.km_from_last_txn, importance: 0.212 },
        { feature: 'is_new_device', value: transaction.is_new_device, importance: 0.082 },
        { feature: 'is_night', value: transaction.is_night, importance: 0.490 },
        { feature: 'txn_count_24hr', value: transaction.txn_count_24hr, importance: 0.305 },
    ];

    return (
        <div style={{ padding: '32px', background: '#f8fafc', minHeight: '100vh' }}>
            <button
                onClick={() => navigate(-1)}
                style={{
                    background: 'none',
                    border: 'none',
                    color: '#2563eb',
                    fontSize: '14px',
                    cursor: 'pointer',
                    marginBottom: '20px',
                    padding: 0,
                    fontWeight: '500',
                }}
            >
                Back
            </button>

            <div style={{ display: 'flex', alignItems: 'center', gap: '16px', marginBottom: '28px' }}>
                <div>
                    <h1 style={{ fontSize: '22px', fontWeight: '700', color: '#0f172a', margin: '0 0 4px 0' }}>
                        {transaction.txn_id}
                    </h1>
                    <p style={{ color: '#64748b', fontSize: '14px', margin: 0 }}>
                        {formatTime(transaction.timestamp)}
                    </p>
                </div>
                <RiskBadge riskLevel={riskLevel} score={transaction.anomaly_score} />
            </div>

            <div style={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                ...actionStyle,
                borderRadius: '8px',
                padding: '14px 20px',
                marginBottom: '24px',
                fontSize: '14px',
                fontWeight: '600',
            }}>
                <span>{getActionLabel(transaction.anomaly_score)}</span>
                <button
                    onClick={handleDownloadReport}
                    style={{
                        padding: '6px 16px',
                        background: '#0f172a',
                        color: '#ffffff',
                        border: 'none',
                        borderRadius: '6px',
                        fontSize: '13px',
                        fontWeight: '600',
                        cursor: 'pointer',
                    }}
                >
                    Download STR Report
                </button>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '20px', marginBottom: '24px' }}>
                <div style={{
                    background: '#ffffff',
                    border: '1px solid #e2e8f0',
                    borderRadius: '10px',
                    padding: '20px 24px',
                }}>
                    <h2 style={{ fontSize: '15px', fontWeight: '600', color: '#0f172a', margin: '0 0 16px 0' }}>
                        Transaction Details
                    </h2>
                    {[
                        { label: 'User ID', value: transaction.user_id },
                        { label: 'Amount', value: formatCurrency(transaction.amount) },
                        { label: 'City', value: transaction.city },
                        { label: 'Merchant Category', value: transaction.merchant_category },
                        { label: 'Device', value: transaction.device_id ? transaction.device_id.slice(0, 16) + '...' : 'N/A' },
                        { label: 'Anomaly Score', value: `${(transaction.anomaly_score * 100).toFixed(1)}%` },
                    ].map((item) => (
                        <div key={item.label} style={{
                            display: 'flex',
                            justifyContent: 'space-between',
                            padding: '8px 0',
                            borderBottom: '1px solid #f1f5f9',
                            fontSize: '14px',
                        }}>
                            <span style={{ color: '#64748b' }}>{item.label}</span>
                            <span style={{ color: '#0f172a', fontWeight: '500' }}>{item.value}</span>
                        </div>
                    ))}
                </div>

                <div style={{
                    background: '#ffffff',
                    border: '1px solid #e2e8f0',
                    borderRadius: '10px',
                    padding: '20px 24px',
                }}>
                    <h2 style={{ fontSize: '15px', fontWeight: '600', color: '#0f172a', margin: '0 0 16px 0' }}>
                        Behavioral Signals
                    </h2>
                    {[
                        { label: 'Distance from Last Transaction', value: `${transaction.km_from_last_txn} km` },
                        { label: 'Time Since Last Transaction', value: `${transaction.minutes_from_last_txn} min` },
                        { label: 'Impossible Speed Detected', value: transaction.impossible_speed ? 'Yes' : 'No' },
                        { label: 'New Device', value: transaction.is_new_device ? 'Yes' : 'No' },
                        { label: 'Night Transaction', value: transaction.is_night ? 'Yes' : 'No' },
                        { label: 'Amount vs User Average', value: `${(transaction.amount_vs_user_avg * 100).toFixed(0)}%` },
                    ].map((item) => (
                        <div key={item.label} style={{
                            display: 'flex',
                            justifyContent: 'space-between',
                            padding: '8px 0',
                            borderBottom: '1px solid #f1f5f9',
                            fontSize: '14px',
                        }}>
                            <span style={{ color: '#64748b' }}>{item.label}</span>
                            <span style={{ color: '#0f172a', fontWeight: '500' }}>{item.value}</span>
                        </div>
                    ))}
                </div>
            </div>

            <div style={{
                background: '#ffffff',
                border: '1px solid #e2e8f0',
                borderRadius: '10px',
                padding: '20px 24px',
                marginBottom: '24px',
            }}>
                <h2 style={{ fontSize: '15px', fontWeight: '600', color: '#0f172a', margin: '0 0 4px 0' }}>
                    Explainability — Feature Importance
                </h2>
                <p style={{ color: '#64748b', fontSize: '13px', margin: '0 0 16px 0' }}>
                    Features that contributed most to this anomaly score
                </p>
                <ShapChart explanation={shapImportance} />
            </div>

            <div style={{
                background: '#ffffff',
                border: '1px solid #e2e8f0',
                borderRadius: '10px',
                padding: '20px 24px',
            }}>
                <h2 style={{ fontSize: '15px', fontWeight: '600', color: '#0f172a', margin: '0 0 16px 0' }}>
                    Recent Transaction History — {transaction.user_id}
                </h2>
                <div style={{ overflowX: 'auto' }}>
                    <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '13px' }}>
                        <thead>
                            <tr style={{ background: '#f9fafb', borderBottom: '2px solid #e5e7eb' }}>
                                {['Transaction ID', 'Amount', 'City', 'Category', 'Score', 'Time'].map((h) => (
                                    <th key={h} style={{
                                        padding: '10px 14px',
                                        textAlign: 'left',
                                        fontWeight: '600',
                                        color: '#374151',
                                        fontSize: '12px',
                                        textTransform: 'uppercase',
                                    }}>
                                        {h}
                                    </th>
                                ))}
                            </tr>
                        </thead>
                        <tbody>
                            {userHistory.map((txn, index) => (
                                <tr
                                    key={txn.txn_id}
                                    style={{
                                        borderBottom: '1px solid #f3f4f6',
                                        background: txn.txn_id === transaction.txn_id ? '#eff6ff' : index % 2 === 0 ? '#ffffff' : '#fafafa',
                                    }}
                                >
                                    <td style={{ padding: '10px 14px', color: '#2563eb', fontWeight: '500' }}>{txn.txn_id}</td>
                                    <td style={{ padding: '10px 14px', fontWeight: '600' }}>{formatCurrency(txn.amount)}</td>
                                    <td style={{ padding: '10px 14px', color: '#374151' }}>{txn.city}</td>
                                    <td style={{ padding: '10px 14px', color: '#374151' }}>{txn.merchant_category}</td>
                                    <td style={{ padding: '10px 14px', fontWeight: '600', color: txn.anomaly_score >= 0.8 ? '#ef4444' : txn.anomaly_score >= 0.5 ? '#f59e0b' : '#22c55e' }}>
                                        {(txn.anomaly_score * 100).toFixed(1)}%
                                    </td>
                                    <td style={{ padding: '10px 14px', color: '#6b7280' }}>{formatTime(txn.timestamp)}</td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    );
};

export default TransactionDetail;