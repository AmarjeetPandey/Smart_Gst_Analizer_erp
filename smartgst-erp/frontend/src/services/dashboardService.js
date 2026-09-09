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

  createInvoice: async (payload) => {
    const response = await apiClient.post('/invoices', payload);
    return response.data;
  },
};
