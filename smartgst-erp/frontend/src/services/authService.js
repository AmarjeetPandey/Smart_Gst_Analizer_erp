import apiClient from './api';
import Cookie from 'js-cookie';

export const authService = {
  sendOTP: async (email) => {
    const response = await apiClient.post('/auth/send-otp', { email });
    return response.data;
  },

  verifyOTP: async (email, code) => {
    const response = await apiClient.post('/auth/verify-otp', { email, code });
    
    // Store tokens
    Cookie.set('access_token', response.data.access_token);
    Cookie.set('refresh_token', response.data.refresh_token);
    
    return response.data;
  },

  refreshToken: async (refreshToken) => {
    const response = await apiClient.post('/auth/refresh-token', {
      refresh_token: refreshToken,
    });
    
    Cookie.set('access_token', response.data.access_token);
    return response.data;
  },

  logout: () => {
    Cookie.remove('access_token');
    Cookie.remove('refresh_token');
    Cookie.remove('user');
    window.location.href = '/login';
  },

  getCurrentUser: () => {
    const userStr = Cookie.get('user');
    return userStr ? JSON.parse(userStr) : null;
  },

  saveUser: (user) => {
    Cookie.set('user', JSON.stringify(user));
  },

  isAuthenticated: () => {
    return !!Cookie.get('access_token');
  },
};
