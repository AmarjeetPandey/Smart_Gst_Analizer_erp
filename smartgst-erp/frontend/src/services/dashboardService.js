import apiClient from './api';

export const dashboardService = {
  getSummary: async () => {
    const response = await apiClient.get('/dashboard/summary');
    return response.data;
  },

  getCustomers: async () => {
    const response = await apiClient.get('/customers');
    return response.data;
  },

  createCustomer: async (payload) => {
    const response = await apiClient.post('/customers', payload);
    return response.data;
  },

  getProducts: async () => {
    const response = await apiClient.get('/products');
    return response.data;
  },

  createProduct: async (payload) => {
    const response = await apiClient.post('/products', payload);
    return response.data;
  },

  getInvoices: async () => {
    const response = await apiClient.get('/invoices');
    return response.data;
  },

  getCompanyProfile: async () => {
    const response = await apiClient.get('/company-profile');
    return response.data;
  },

  createInvoice: async (payload) => {
    const response = await apiClient.post('/invoices', payload);
    return response.data;
  },

  downloadInvoicePdf: async (invoiceId) => {
    const response = await apiClient.get(`/invoices/${invoiceId}/pdf`, { responseType: 'blob' });
    return response.data;
  },

  downloadInvoiceExcel: async (invoiceId) => {
    const response = await apiClient.get(`/invoices/${invoiceId}/excel`, { responseType: 'blob' });
    return response.data;
  },

  sendInvoiceEmail: async (invoiceId, recipientEmail, paymentProofExpected = false) => {
    const response = await apiClient.post(`/invoices/${invoiceId}/send`, {
      recipient_email: recipientEmail || null,
      payment_proof_expected: paymentProofExpected,
    });
    return response.data;
  },

  getVendors: async () => {
    const response = await apiClient.get('/vendors');
    return response.data;
  },

  createVendor: async (payload) => {
    const response = await apiClient.post('/vendors', payload);
    return response.data;
  },

  getPurchases: async () => {
    const response = await apiClient.get('/purchases');
    return response.data;
  },

  createPurchase: async (payload) => {
    const response = await apiClient.post('/purchases', payload);
    return response.data;
  },

  clearBusinessHistory: async (confirmation) => {
    const response = await apiClient.post('/history/clear', { confirmation });
    return response.data;
  },

  getReportSummary: async () => {
    const response = await apiClient.get('/reports/summary');
    return response.data;
  },

  getAnalyzerInsights: async () => {
    const response = await apiClient.get('/analyzer/insights');
    return response.data;
  },
};
