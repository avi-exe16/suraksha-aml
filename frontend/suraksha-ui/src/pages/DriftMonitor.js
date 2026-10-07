import React, { useState, useEffect } from 'react';
import { fetchDriftReport } from '../utils/api';

const DriftMonitor = () => {
    const [report, setReport] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    useEffect(() => {
        loadReport();
    }, []); // eslint-disable-line react-hooks/exhaustive-deps

    const loadReport = async () => {
        try {
            setLoading(true);
            const data = await fetchDriftReport();
            setReport(data);
            setError(null);
        } catch (err) {
            setError('Failed to load drift report. Ensure the backend is running.');
        } finally {
            setLoading(false);
        }
    };

    if (loading) {
        return (
            <div style={{ padding: '40px', textAlign: 'center', color: '#6b7280' }}>
                Computing drift report...
            </div>
        );
    }

    if (error) {
        return (
            <div style={{ padding: '40px', textAlign: 'center', color: '#ef4444' }}>
                {error}
            </div>
        );
    }

    return (
        <div style={{ padding: '32px', background: '#f8fafc', minHeight: '100vh' }}>
            <div style={{ marginBottom: '28px' }}>
                <h1 style={{ fontSize: '24px', fontWeight: '700', color: '#0f172a', margin: '0 0 4px 0' }}>
                    Model Drift Monitor
                </h1>
                <p style={{ color: '#64748b', fontSize: '14px', margin: 0 }}>
                    Monitors whether incoming transaction patterns have shifted from training distribution
                </p>
            </div>

            <div style={{
                background: report.drift_detected ? '#fee2e2' : '#dcfce7',
                border: `1px solid ${report.drift_detected ? '#fca5a5' : '#86efac'}`,
                borderRadius: '10px',
                padding: '20px 24px',
                marginBottom: '24px',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
            }}>
                <div>
                    <p style={{
                        fontSize: '16px',
                        fontWeight: '700',
                        color: report.drift_detected ? '#991b1b' : '#166534',
                        margin: '0 0 4px 0',
                    }}>
                        {report.drift_detected ? 'Drift Detected' : 'Model Stable'}
                    </p>
                    <p style={{
                        fontSize: '13px',
                        color: report.drift_detected ? '#b91c1c' : '#15803d',
                        margin: 0,
                    }}>
                        {report.recommendation}
                    </p>
                </div>
                <button
                    onClick={loadReport}
                    style={{
                        padding: '8px 20px',
                        background: '#0f172a',
                        color: '#ffffff',
                        border: 'none',
                        borderRadius: '6px',
                        fontSize: '13px',
                        fontWeight: '600',
                        cursor: 'pointer',
                    }}
                >
                    Refresh
                </button>
            </div>

            <div style={{ display: 'flex', gap: '16px', marginBottom: '24px', flexWrap: 'wrap' }}>
                {[
                    { label: 'Reference Period', value: report.reference_period_size.toLocaleString('en-IN'), color: '#3b82f6' },
                    { label: 'Current Period', value: report.current_period_size.toLocaleString('en-IN'), color: '#8b5cf6' },
                    { label: 'Reference Fraud Rate', value: `${report.reference_fraud_rate}%`, color: '#f59e0b' },
                    { label: 'Current Fraud Rate', value: `${report.current_fraud_rate}%`, color: '#ef4444' },
                ].map((card) => (
                    <div key={card.label} style={{
                        background: '#ffffff',
                        border: '1px solid #e2e8f0',
                        borderLeft: `4px solid ${card.color}`,
                        borderRadius: '8px',
                        padding: '16px 20px',
                        flex: 1,
                        minWidth: '160px',
                    }}>
                        <p style={{ fontSize: '12px', color: '#6b7280', margin: '0 0 6px 0', textTransform: 'uppercase', fontWeight: '500' }}>
                            {card.label}
                        </p>
                        <p style={{ fontSize: '24px', fontWeight: '700', color: '#0f172a', margin: 0 }}>
                            {card.value}
                        </p>
                    </div>
                ))}
            </div>

            <div style={{
                background: '#ffffff',
                border: '1px solid #e2e8f0',
                borderRadius: '10px',
                overflow: 'hidden',
            }}>
                <div style={{ padding: '16px 20px', borderBottom: '1px solid #e2e8f0' }}>
                    <h2 style={{ fontSize: '15px', fontWeight: '600', color: '#0f172a', margin: 0 }}>
                        Feature Drift Analysis
                    </h2>
                </div>
                <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '14px' }}>
                    <thead>
                        <tr style={{ background: '#f9fafb', borderBottom: '2px solid #e5e7eb' }}>
                            {['Feature', 'Reference Mean', 'Current Mean', 'Change %', 'Status'].map((h) => (
                                <th key={h} style={{
                                    padding: '12px 16px',
                                    textAlign: 'left',
                                    fontWeight: '600',
                                    color: '#374151',
                                    fontSize: '13px',
                                    textTransform: 'uppercase',
                                }}>
                                    {h}
                                </th>
                            ))}
                        </tr>
                    </thead>
                    <tbody>
                        {report.features.map((feature, index) => (
                            <tr key={feature.feature} style={{
                                borderBottom: '1px solid #f3f4f6',
                                background: index % 2 === 0 ? '#ffffff' : '#fafafa',
                            }}>
                                <td style={{ padding: '12px 16px', fontWeight: '600', color: '#0f172a', textTransform: 'capitalize' }}>
                                    {feature.feature.replace(/_/g, ' ')}
                                </td>
                                <td style={{ padding: '12px 16px', color: '#374151' }}>
                                    {feature.reference_mean}
                                </td>
                                <td style={{ padding: '12px 16px', color: '#374151' }}>
                                    {feature.current_mean}
                                </td>
                                <td style={{ padding: '12px 16px', fontWeight: '600', color: feature.drift_detected ? '#ef4444' : '#22c55e' }}>
                                    {feature.pct_change}%
                                </td>
                                <td style={{ padding: '12px 16px' }}>
                                    <span style={{
                                        padding: '2px 10px',
                                        borderRadius: '12px',
                                        fontSize: '12px',
                                        fontWeight: '600',
                                        background: feature.drift_detected ? '#fee2e2' : '#dcfce7',
                                        color: feature.drift_detected ? '#991b1b' : '#166534',
                                        border: `1px solid ${feature.drift_detected ? '#fca5a5' : '#86efac'}`,
                                    }}>
                                        {feature.drift_detected ? 'Drift' : 'Stable'}
                                    </span>
                                </td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>
        </div>
    );
};

export default DriftMonitor;