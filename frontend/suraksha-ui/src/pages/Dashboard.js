import React, { useState, useEffect } from 'react';
import StatsCard from '../components/StatsCard';
import TransactionTable from '../components/TransactionTable';
import { fetchDashboardStats, fetchTransactions } from '../utils/api';

const Dashboard = () => {
    const [stats, setStats] = useState(null);
    const [transactions, setTransactions] = useState([]);
    const [loading, setLoading] = useState(true);
    const [filter, setFilter] = useState(null);
    const [error, setError] = useState(null);

    useEffect(() => {
        loadData(true); // initial load shows loading spinner

        const interval = setInterval(() => {
            loadData(false); // background polling runs silently
        }, 4000);

        return () => clearInterval(interval);
    }, [filter]); // eslint-disable-line react-hooks/exhaustive-deps

    const loadData = async (isInitial = false) => {
        try {
            if (isInitial) setLoading(true);
            const [statsData, txnData] = await Promise.all([
                fetchDashboardStats(),
                fetchTransactions(100, filter),
            ]);
            setStats(statsData?.data || statsData);
            
            const txns = Array.isArray(txnData) 
                ? txnData 
                : (txnData?.transactions || txnData?.data || []);
            setTransactions(txns);
            setError(null);
        } catch (err) {
            console.error("Dashboard Load Error:", err);
            setError('Failed to load data. Ensure the backend is running.');
        } finally {
            if (isInitial) setLoading(false);
        }
    };

    const formatCurrency = (amount) => {
        return new Intl.NumberFormat('en-IN', {
            style: 'currency',
            currency: 'INR',
            maximumFractionDigits: 0,
        }).format(amount);
    };

    const filterButtons = [
        { label: 'All', value: null },
        { label: 'High Risk', value: 'high' },
        { label: 'Medium Risk', value: 'medium' },
        { label: 'Low Risk', value: 'low' },
    ];

    return (
        <div style={{ padding: '32px', background: '#f8fafc', minHeight: '100vh' }}>
           <div style={{ marginBottom: '28px', display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                <div>
                    <h1 style={{ fontSize: '24px', fontWeight: '700', color: '#0f172a', margin: '0 0 4px 0' }}>
                        Command Center
                    </h1>
                    <p style={{ color: '#64748b', fontSize: '14px', margin: 0 }}>
                        Real-time transaction monitoring and fraud detection
                    </p>
                </div>
                
            </div>

            {error && (
                <div style={{
                    background: '#fee2e2',
                    border: '1px solid #fca5a5',
                    borderRadius: '8px',
                    padding: '12px 16px',
                    marginBottom: '24px',
                    color: '#991b1b',
                    fontSize: '14px',
                }}>
                    {error}
                </div>
            )}

            <div style={{ display: 'flex', gap: '16px', marginBottom: '28px', flexWrap: 'wrap' }}>
    <StatsCard
        title="Total Transactions"
        value={stats ? (stats.total_transactions?.toLocaleString('en-IN') ?? '0') : '...'}
        subtitle="Last 90 days"
        color="blue"
    />
    <StatsCard
        title="High Risk Blocked"
        value={stats ? (stats.high_risk?.toLocaleString('en-IN') ?? '0') : '...'}
        subtitle={stats ? `${stats.fraud_rate ?? 0}% fraud rate` : '...'}
        color="red"
    />
    <StatsCard
        title="Under Review"
        value={stats ? (stats.medium_risk?.toLocaleString('en-IN') ?? '0') : '...'}
        subtitle="Step-up auth triggered"
        color="yellow"
    />
    <StatsCard
        title="Amount Protected"
        value={stats ? formatCurrency(stats.amount_saved ?? 0) : '...'}
        subtitle="Fraud value intercepted"
        color="green"
    />
</div>

            <div style={{
                background: '#ffffff',
                borderRadius: '10px',
                border: '1px solid #e2e8f0',
                overflow: 'hidden',
            }}>
                <div style={{
                    padding: '16px 20px',
                    borderBottom: '1px solid #e2e8f0',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    flexWrap: 'wrap',
                    gap: '12px',
                }}>
                    <h2 style={{ fontSize: '16px', fontWeight: '600', color: '#0f172a', margin: 0 }}>
                        Live Transaction Feed
                    </h2>
                    <div style={{ display: 'flex', gap: '8px' }}>
                        {filterButtons.map((btn) => (
                            <button
                                key={btn.label}
                                onClick={() => setFilter(btn.value)}
                                style={{
                                    padding: '6px 14px',
                                    borderRadius: '6px',
                                    border: '1px solid',
                                    borderColor: filter === btn.value ? '#2563eb' : '#e2e8f0',
                                    background: filter === btn.value ? '#2563eb' : '#ffffff',
                                    color: filter === btn.value ? '#ffffff' : '#374151',
                                    fontSize: '13px',
                                    fontWeight: '500',
                                    cursor: 'pointer',
                                }}
                            >
                                {btn.label}
                            </button>
                        ))}
                        <button
                            onClick={loadData}
                            style={{
                                padding: '6px 14px',
                                borderRadius: '6px',
                                border: '1px solid #e2e8f0',
                                background: '#f8fafc',
                                color: '#374151',
                                fontSize: '13px',
                                fontWeight: '500',
                                cursor: 'pointer',
                            }}
                        >
                            Refresh
                        </button>
                    </div>
                </div>
                <TransactionTable transactions={transactions} loading={loading} />
            </div>
        </div>
    );
};

export default Dashboard;