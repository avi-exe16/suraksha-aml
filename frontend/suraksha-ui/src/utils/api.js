import axios from 'axios';
const BASE_URL = process.env.REACT_APP_API_URL || 'https://suraksha-aml.onrender.com';

const api = axios.create({
    baseURL: BASE_URL,
    timeout: 10000,
});

export const fetchDashboardStats = async () => {
    const response = await api.get('/dashboard/stats');
    return response.data;
};

export const fetchTransactions = async (limit = 100, riskLevel = null) => {
    const params = { limit };
    if (riskLevel) params.risk_level = riskLevel;
    const response = await api.get('/transactions', { params });
    return response.data;
};

export const fetchTransactionById = async (txnId) => {
    const response = await api.get(`/transactions/${txnId}`);
    return response.data;
};

export const fetchFlaggedTransactions = async (limit = 50) => {
    const response = await api.get('/transactions/flagged', { params: { limit } });
    return response.data;
};

export const fetchUserTransactions = async (userId) => {
    const response = await api.get(`/users/${userId}/transactions`);
    return response.data;
};

export const fetchUserProfile = async (userId) => {
    const response = await api.get(`/users/${userId}`);
    return response.data;
};

export const fetchAuditLog = async (userId) => {
    const response = await api.get(`/audit/${userId}`);
    return response.data;
};

export const revokeConsent = async (userId, accessor) => {
    const response = await api.post('/consent/revoke', {
        user_id: userId,
        accessor: accessor,
    });
    return response.data;
};

export const fetchConsentStatus = async (userId) => {
    const response = await api.get(`/consent/${userId}`);
    return response.data;
};

export const scoreTransaction = async (transactionData) => {
    const response = await api.post('/transaction/score', transactionData);
    return response.data;
};

export const fetchDriftReport = async () => {
    const response = await api.get('/drift/report');
    return response.data;
};