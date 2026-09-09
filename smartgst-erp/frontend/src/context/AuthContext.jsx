import React, { createContext, useCallback, useEffect, useState } from 'react';
import { authService } from '../services/authService';

export const AuthContext = createContext(null);

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isAuthenticated, setIsAuthenticated] = useState(false);

  // Initialize auth state
  useEffect(() => {
    const storedUser = authService.getCurrentUser();
    const isAuth = authService.isAuthenticated();
    
    if (isAuth && storedUser) {
      setUser(storedUser);
      setIsAuthenticated(true);
    }
    
    setIsLoading(false);
  }, []);

  const login = useCallback(async (email, otp) => {
    try {
      const response = await authService.verifyOTP(email, otp);
      setUser(response.user);
      authService.saveUser(response.user);
      setIsAuthenticated(true);
      return response;
    } catch (error) {
      console.error('Login failed:', error);
      throw error;
    }
  }, []);

  const logout = useCallback(() => {
    authService.logout();
    setUser(null);
    setIsAuthenticated(false);
  }, []);

  const sendOTP = useCallback(async (email) => {
    return authService.sendOTP(email);
  }, []);

  const value = {
    user,
    isLoading,
    isAuthenticated,
    login,
    logout,
    sendOTP,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};

export const useAuth = () => {
  const context = React.useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
