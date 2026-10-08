import React, { useState } from 'react';
import { scoreTransaction } from '../utils/api';
import RiskBadge from '../components/RiskBadge';
import ShapChart from '../components/ShapChart';

const AdminPanel = () => {
    const [form, setForm] = useState({
        txn_id: 'TXN_TEST_001',
        user_id: 'USR00001',
        amount: 5000,
        city: 'Mumbai',
        lat: 19.076,
        lon: 72.8777,
        device_id: 'device-test-001',
        merchant_category: 'grocery',
        km_from_last_txn: 2,
        minutes_from_last_txn: 120,
        impossible_speed: 0,
        hour: 14,
        is_weekend: 0,
        is_night: 0,
        txn_count_1hr: 0,
        txn_count_24hr: 2,
        amount_sum_1hr: 0,
        amount_sum_24hr: 8000,
        amount_vs_user_avg: 1.0,
        is_new_device: 0,
        device_count_7d: 1,
        is_new_merchant_category: 0,
    });

    const [result, setResult] = useState(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);
    const [shadowMode, setShadowMode] = useState(false);
    const [shadowMessage, setShadowMessage] = useState(null);

    const fraudPreset = {
        txn_id: 'TXN_FRAUD_TEST',
        user_id: 'USR00001',
        amount: 95000,
        city: 'Delhi',
        lat: 28.6139,
        lon: 77.209,
        device_id: 'device-unknown-xyz',
        merchant_category: 'crypto',
        km_from_last_txn: 1400,
        minutes_from_last_txn: 45,
        impossible_speed: 1,
        hour: 3,
        is_weekend: 0,
        is_night: 1,
        txn_count_1hr: 3,
        txn_count_24hr: 8,
        amount_sum_1hr: 180000,
        amount_sum_24hr: 320000,
        amount_vs_user_avg: 8.5,
        is_new_device: 1,
        device_count_7d: 4,
        is_new_merchant_category: 1,
    };

    const normalPreset = {
        txn_id: 'TXN_NORMAL_TEST',
        user_id: 'USR00002',
        amount: 3500,
        city: 'Bangalore',
        lat: 12.9716,
        lon: 77.5946,
        device_id: 'device-regular-001',
        merchant_category: 'grocery',
        km_from_last_txn: 1.2,
        minutes_from_last_txn: 480,
        impossible_speed: 0,
        hour: 11,
        is_weekend: 0,
        is_night: 0,
        txn_count_1hr: 0,
        txn_count_24hr: 1,
        amount_sum_1hr: 0,
        amount_sum_24hr: 3500,
        amount_vs_user_avg: 0.9,
        is_new_device: 0,
        device_count_7d: 1,
        is_new_merchant_category: 0,
    };

    const handleChange = (key, value) => {
        setForm((prev) => ({ ...prev, [key]: value }));
    };

    const handleSubmit = async () => {
        try {
            setLoading(true);
            setError(null);
            const parsedForm = {
                ...form,
                amount: parseFloat(form.amount),
                lat: parseFloat(form.lat),
                lon: parseFloat(form.lon),
                km_from_last_txn: parseFloat(form.km_from_last_txn),
                minutes_from_last_txn: parseFloat(form.minutes_from_last_txn),
                impossible_speed: parseInt(form.impossible_speed),
                hour: parseInt(form.hour),
                is_weekend: parseInt(form.is_weekend),
                is_night: parseInt(form.is_night),
                txn_count_1hr: parseInt(form.txn_count_1hr),
                txn_count_24hr: parseInt(form.txn_count_24hr),
                amount_sum_1hr: parseFloat(form.amount_sum_1hr),
                amount_sum_24hr: parseFloat(form.amount_sum_24hr),
                amount_vs_user_avg: parseFloat(form.amount_vs_user_avg),
                is_new_device: parseInt(form.is_new_device),
                device_count_7d: parseInt(form.device_count_7d),
                is_new_merchant_category: parseInt(form.is_new_merchant_category),
            };
            const response = await scoreTransaction(parsedForm);
            setResult(response);
        } catch (err) {
            setError('Scoring failed. Ensure the backend is running.');
        } finally {
            setLoading(false);
        }
    };

    const handleShadowToggle = async () => {
        const res = await fetch('https://suraksha-aml.onrender.com/shadow-mode/toggle', { method: 'POST' });
        const data = await res.json();
        setShadowMode(data.shadow_mode);
        setShadowMessage(data.message);
        setTimeout(() => setShadowMessage(null), 3000);
    };

    const getRiskLevel = (score) => {
        if (score >= 0.8) return 'high';
        if (score >= 0.5) return 'medium';
        return 'low';
    };

    const inputStyle = {
        width: '100%',
        padding: '7px 10px',
        border: '1px solid #e2e8f0',
        borderRadius: '6px',
        fontSize: '13px',
        color: '#0f172a',
        background: '#ffffff',
        boxSizing: 'border-box',
    };

    const labelStyle = {
        fontSize: '12px',
        fontWeight: '500',
        color: '#64748b',
        marginBottom: '4px',
        display: 'block',
        textTransform: 'uppercase',
        letterSpacing: '0.04em',
    };

    return (
        <div style={{ padding: '32px', background: '#f8fafc', minHeight: '100vh' }}>
            <div style={{ marginBottom: '28px' }}>
                <h1 style={{ fontSize: '24px', fontWeight: '700', color: '#0f172a', margin: '0 0 4px 0' }}>
                    Admin Panel
                </h1>
                <p style={{ color: '#64748b', fontSize: '14px', margin: 0 }}>
                    Simulate and score transactions in real time
                </p>
            </div>

            <div style={{ display: 'flex', gap: '12px', marginBottom: '8px', flexWrap: 'wrap', alignItems: 'center' }}>
                <button
                    onClick={() => setForm(fraudPreset)}
                    style={{
                        padding: '8px 20px',
                        background: '#fee2e2',
                        color: '#991b1b',
                        border: '1px solid #fca5a5',
                        borderRadius: '6px',
                        cursor: 'pointer',
                        fontSize: '13px',
                        fontWeight: '600',
                    }}
                >
                    Load Fraud Scenario
                </button>
                <button
                    onClick={() => setForm(normalPreset)}
                    style={{
                        padding: '8px 20px',
                        background: '#dcfce7',
                        color: '#166534',
                        border: '1px solid #86efac',
                        borderRadius: '6px',
                        cursor: 'pointer',
                        fontSize: '13px',
                        fontWeight: '600',
                    }}
                >
                    Load Normal Scenario
                </button>
                <button
                    onClick={handleShadowToggle}
                    style={{
                        padding: '8px 20px',
                        background: shadowMode ? '#1e3a5f' : '#f1f5f9',
                        color: shadowMode ? '#60a5fa' : '#374151',
                        border: '1px solid',
                        borderColor: shadowMode ? '#2563eb' : '#e2e8f0',
                        borderRadius: '6px',
                        cursor: 'pointer',
                        fontSize: '13px',
                        fontWeight: '600',
                    }}
                >
                    {shadowMode ? 'Shadow Mode: ON' : 'Shadow Mode: OFF'}
                </button>
            </div>

            {shadowMessage && (
                <p style={{ color: '#2563eb', fontSize: '13px', marginBottom: '16px', fontWeight: '500' }}>
                    {shadowMessage}
                </p>
            )}

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '24px' }}>
                <div style={{
                    background: '#ffffff',
                    border: '1px solid #e2e8f0',
                    borderRadius: '10px',
                    padding: '24px',
                }}>
                    <h2 style={{ fontSize: '15px', fontWeight: '600', color: '#0f172a', margin: '0 0 20px 0' }}>
                        Transaction Input
                    </h2>
                    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '14px' }}>
                        {Object.entries(form).map(([key, value]) => (
                            <div key={key}>
                                <label style={labelStyle}>{key.replace(/_/g, ' ')}</label>
                                <input
                                    style={inputStyle}
                                    value={value}
                                    onChange={(e) => handleChange(key, e.target.value)}
                                />
                            </div>
                        ))}
                    </div>
                    <button
                        onClick={handleSubmit}
                        disabled={loading}
                        style={{
                            marginTop: '20px',
                            width: '100%',
                            padding: '10px',
                            background: loading ? '#94a3b8' : '#2563eb',
                            color: '#ffffff',
                            border: 'none',
                            borderRadius: '6px',
                            fontSize: '14px',
                            fontWeight: '600',
                            cursor: loading ? 'not-allowed' : 'pointer',
                        }}
                    >
                        {loading ? 'Scoring...' : 'Score Transaction'}
                    </button>
                    {error && (
                        <p style={{ color: '#ef4444', fontSize: '13px', marginTop: '10px' }}>{error}</p>
                    )}
                </div>

                <div style={{
                    background: '#ffffff',
                    border: '1px solid #e2e8f0',
                    borderRadius: '10px',
                    padding: '24px',
                }}>
                    <h2 style={{ fontSize: '15px', fontWeight: '600', color: '#0f172a', margin: '0 0 20px 0' }}>
                        Scoring Result
                    </h2>
                    {!result ? (
                        <div style={{ color: '#94a3b8', fontSize: '14px', padding: '40px 0', textAlign: 'center' }}>
                            Submit a transaction to see the result.
                        </div>
                    ) : (
                        <div>
                            <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '20px' }}>
                                <span style={{ fontSize: '36px', fontWeight: '700', color: '#0f172a' }}>
                                    {(result.anomaly_score * 100).toFixed(1)}%
                                </span>
                                <RiskBadge riskLevel={getRiskLevel(result.anomaly_score)} score={result.anomaly_score} />
                            </div>
                            <div style={{
                                padding: '12px 16px',
                                borderRadius: '8px',
                                background: result.action === 'blocked' ? '#fee2e2' : result.action === 'step_up_auth' ? '#fef9c3' : '#dcfce7',
                                color: result.action === 'blocked' ? '#991b1b' : result.action === 'step_up_auth' ? '#854d0e' : '#166534',
                                fontWeight: '600',
                                fontSize: '14px',
                                marginBottom: '20px',
                            }}>
                                Action: {result.action === 'blocked' ? 'Transaction Blocked' : result.action === 'step_up_auth' ? 'Step-up Authentication Triggered' : 'Transaction Approved'}
                            </div>
                            <h3 style={{ fontSize: '14px', fontWeight: '600', color: '#0f172a', margin: '0 0 12px 0' }}>
                                Feature Importance
                            </h3>
                            <ShapChart explanation={result.explanation} />
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
};

export default AdminPanel;