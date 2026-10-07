import React, { useState } from 'react';
import { fetchAuditLog, revokeConsent, fetchConsentStatus } from '../utils/api';

const ConsentPortal = () => {
    const [userId, setUserId] = useState('');
    const [auditLog, setAuditLog] = useState([]);
    const [consentStatus, setConsentStatus] = useState([]);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);
    const [searched, setSearched] = useState(false);
    const [revokeSuccess, setRevokeSuccess] = useState(null);

    const handleSearch = async () => {
        if (!userId.trim()) return;
        try {
            setLoading(true);
            setError(null);
            const [auditData, consentData] = await Promise.all([
                fetchAuditLog(userId.trim()),
                fetchConsentStatus(userId.trim()),
            ]);
            setAuditLog(auditData.entries);
            setConsentStatus(consentData.consents);
            setSearched(true);
        } catch (err) {
            setError('Failed to load data for this user ID.');
        } finally {
            setLoading(false);
        }
    };

    const handleRevoke = async (accessor) => {
        try {
            await revokeConsent(userId.trim(), accessor);
            setRevokeSuccess(`Access revoked for ${accessor}`);
            await handleSearch();
            setTimeout(() => setRevokeSuccess(null), 3000);
        } catch (err) {
            setError('Failed to revoke consent.');
        }
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

    const accessors = [
        'fraud_detection_engine',
        'bank_officer',
        'compliance_team',
        'third_party_analytics',
    ];

    return (
        <div style={{ padding: '32px', background: '#f8fafc', minHeight: '100vh' }}>
            <div style={{ marginBottom: '28px' }}>
                <h1 style={{ fontSize: '24px', fontWeight: '700', color: '#0f172a', margin: '0 0 4px 0' }}>
                    Customer Consent Portal
                </h1>
                <p style={{ color: '#64748b', fontSize: '14px', margin: 0 }}>
                    View and manage who has access to your personal data — DPDP Act 2023 Compliant
                </p>
            </div>

            <div style={{
                background: '#ffffff',
                border: '1px solid #e2e8f0',
                borderRadius: '10px',
                padding: '24px',
                marginBottom: '24px',
            }}>
                <h2 style={{ fontSize: '15px', fontWeight: '600', color: '#0f172a', margin: '0 0 16px 0' }}>
                    Enter Customer ID
                </h2>
                <div style={{ display: 'flex', gap: '12px' }}>
                    <input
                        value={userId}
                        onChange={(e) => setUserId(e.target.value)}
                        onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
                        placeholder="e.g. USR00001"
                        style={{
                            flex: 1,
                            padding: '10px 14px',
                            border: '1px solid #e2e8f0',
                            borderRadius: '6px',
                            fontSize: '14px',
                            color: '#0f172a',
                        }}
                    />
                    <button
                        onClick={handleSearch}
                        disabled={loading}
                        style={{
                            padding: '10px 24px',
                            background: '#2563eb',
                            color: '#ffffff',
                            border: 'none',
                            borderRadius: '6px',
                            fontSize: '14px',
                            fontWeight: '600',
                            cursor: loading ? 'not-allowed' : 'pointer',
                        }}
                    >
                        {loading ? 'Loading...' : 'Search'}
                    </button>
                </div>
                {error && (
                    <p style={{ color: '#ef4444', fontSize: '13px', marginTop: '10px' }}>{error}</p>
                )}
                {revokeSuccess && (
                    <p style={{ color: '#166534', fontSize: '13px', marginTop: '10px', fontWeight: '600' }}>
                        {revokeSuccess}
                    </p>
                )}
            </div>

            {searched && (
                <>
                    <div style={{
                        background: '#ffffff',
                        border: '1px solid #e2e8f0',
                        borderRadius: '10px',
                        padding: '24px',
                        marginBottom: '24px',
                    }}>
                        <h2 style={{ fontSize: '15px', fontWeight: '600', color: '#0f172a', margin: '0 0 16px 0' }}>
                            Data Access Control
                        </h2>
                        <p style={{ color: '#64748b', fontSize: '13px', margin: '0 0 16px 0' }}>
                            The following entities have access to your data. You can revoke access at any time.
                        </p>
                        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(260px, 1fr))', gap: '12px' }}>
                            {accessors.map((accessor) => {
                                const isRevoked = consentStatus.some(
                                    (c) => c.accessor === accessor && c.status === 'revoked'
                                );
                                return (
                                    <div key={accessor} style={{
                                        border: '1px solid #e2e8f0',
                                        borderRadius: '8px',
                                        padding: '16px',
                                        display: 'flex',
                                        justifyContent: 'space-between',
                                        alignItems: 'center',
                                    }}>
                                        <div>
                                            <p style={{
                                                fontSize: '13px',
                                                fontWeight: '600',
                                                color: '#0f172a',
                                                margin: '0 0 4px 0',
                                                textTransform: 'capitalize',
                                            }}>
                                                {accessor.replace(/_/g, ' ')}
                                            </p>
                                            <p style={{
                                                fontSize: '12px',
                                                color: isRevoked ? '#ef4444' : '#22c55e',
                                                margin: 0,
                                                fontWeight: '500',
                                            }}>
                                                {isRevoked ? 'Access Revoked' : 'Access Active'}
                                            </p>
                                        </div>
                                        {!isRevoked && (
                                            <button
                                                onClick={() => handleRevoke(accessor)}
                                                style={{
                                                    padding: '6px 12px',
                                                    background: '#fee2e2',
                                                    color: '#991b1b',
                                                    border: '1px solid #fca5a5',
                                                    borderRadius: '6px',
                                                    fontSize: '12px',
                                                    fontWeight: '600',
                                                    cursor: 'pointer',
                                                }}
                                            >
                                                Revoke
                                            </button>
                                        )}
                                    </div>
                                );
                            })}
                        </div>
                    </div>

                    <div style={{
                        background: '#ffffff',
                        border: '1px solid #e2e8f0',
                        borderRadius: '10px',
                        padding: '24px',
                    }}>
                        <h2 style={{ fontSize: '15px', fontWeight: '600', color: '#0f172a', margin: '0 0 16px 0' }}>
                            Data Access Audit Log
                        </h2>
                        {auditLog.length === 0 ? (
                            <p style={{ color: '#94a3b8', fontSize: '14px' }}>
                                No audit log entries found for this user.
                            </p>
                        ) : (
                            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '13px' }}>
                                <thead>
                                    <tr style={{ background: '#f9fafb', borderBottom: '2px solid #e5e7eb' }}>
                                        {['Accessor', 'Access Type', 'Purpose', 'Timestamp'].map((h) => (
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
                                    {auditLog.map((entry, index) => (
                                        <tr key={index} style={{
                                            borderBottom: '1px solid #f3f4f6',
                                            background: index % 2 === 0 ? '#ffffff' : '#fafafa',
                                        }}>
                                            <td style={{ padding: '10px 14px', color: '#374151', fontWeight: '500', textTransform: 'capitalize' }}>
                                                {entry.accessor.replace(/_/g, ' ')}
                                            </td>
                                            <td style={{ padding: '10px 14px', color: '#374151', textTransform: 'capitalize' }}>
                                                {entry.access_type.replace(/_/g, ' ')}
                                            </td>
                                            <td style={{ padding: '10px 14px', color: '#64748b' }}>
                                                {entry.purpose}
                                            </td>
                                            <td style={{ padding: '10px 14px', color: '#6b7280' }}>
                                                {formatTime(entry.timestamp)}
                                            </td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        )}
                    </div>
                </>
            )}
        </div>
    );
};

export default ConsentPortal;