/**
 * Custom hook for managing user data
 */

import { useState, useCallback, useEffect } from 'react';
import { api } from '../services/api';
import { User, ApiError, LoginRequest, LoginResponse } from '../types/api';

interface UseUserOptions {
  onError?: (error: ApiError) => void;
}

export function useUser(options: UseUserOptions = {}) {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [error, setError] = useState<ApiError | null>(null);
  const [preferences, setPreferences] = useState<Record<string, any> | null>(null);

  // Check if user is authenticated on mount
  useEffect(() => {
    const token = localStorage.getItem('authToken');
    if (token) {
      fetchUser();
    }
  }, []);

  // Fetch user data
  const fetchUser = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    
    try {
      const userData = await api.auth.getUser();
      setUser(userData);
      setIsAuthenticated(true);
      return userData;
    } catch (err) {
      const apiError = err as ApiError;
      setError(apiError);
      setIsAuthenticated(false);
      if (options.onError) {
        options.onError(apiError);
      }
      // Clear token if unauthorized
      if (apiError.status === 401) {
        localStorage.removeItem('authToken');
      }
      throw apiError;
    } finally {
      setIsLoading(false);
    }
  }, [options]);

  // Login
  const login = useCallback(async (credentials: LoginRequest): Promise<LoginResponse> => {
    setIsLoading(true);
    setError(null);
    
    try {
      const response = await api.auth.login(credentials);
      
      // Store token
      localStorage.setItem('authToken', response.access_token);
      
      // Set user data
      setUser(response.user);
      setIsAuthenticated(true);
      
      return response;
    } catch (err) {
      const apiError = err as ApiError;
      setError(apiError);
      if (options.onError) {
        options.onError(apiError);
      }
      throw apiError;
    } finally {
      setIsLoading(false);
    }
  }, [options]);

  // Logout
  const logout = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    
    try {
      await api.auth.logout();
      
      // Clear token
      localStorage.removeItem('authToken');
      
      // Clear user data
      setUser(null);
      setIsAuthenticated(false);
      setPreferences(null);
    } catch (err) {
      const apiError = err as ApiError;
      setError(apiError);
      if (options.onError) {
        options.onError(apiError);
      }
      
      // Clear token anyway
      localStorage.removeItem('authToken');
      setUser(null);
      setIsAuthenticated(false);
      setPreferences(null);
      
      throw apiError;
    } finally {
      setIsLoading(false);
    }
  }, [options]);

  // Register
  const register = useCallback(async (userData: any) => {
    setIsLoading(true);
    setError(null);
    
    try {
      const response = await api.auth.register(userData);
      return response;
    } catch (err) {
      const apiError = err as ApiError;
      setError(apiError);
      if (options.onError) {
        options.onError(apiError);
      }
      throw apiError;
    } finally {
      setIsLoading(false);
    }
  }, [options]);

  // Update user profile
  const updateProfile = useCallback(async (profileData: any) => {
    setIsLoading(true);
    setError(null);
    
    try {
      const updatedUser = await api.user.updateProfile(profileData);
      setUser(updatedUser);
      return updatedUser;
    } catch (err) {
      const apiError = err as ApiError;
      setError(apiError);
      if (options.onError) {
        options.onError(apiError);
      }
      throw apiError;
    } finally {
      setIsLoading(false);
    }
  }, [options]);

  // Get user preferences
  const fetchPreferences = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    
    try {
      const userPreferences = await api.user.getPreferences();
      setPreferences(userPreferences);
      return userPreferences;
    } catch (err) {
      const apiError = err as ApiError;
      setError(apiError);
      if (options.onError) {
        options.onError(apiError);
      }
      throw apiError;
    } finally {
      setIsLoading(false);
    }
  }, [options]);

  // Update user preferences
  const updatePreferences = useCallback(async (newPreferences: Record<string, any>) => {
    setIsLoading(true);
    setError(null);
    
    try {
      const updatedPreferences = await api.user.updatePreferences(newPreferences);
      setPreferences(updatedPreferences);
      return updatedPreferences;
    } catch (err) {
      const apiError = err as ApiError;
      setError(apiError);
      if (options.onError) {
        options.onError(apiError);
      }
      throw apiError;
    } finally {
      setIsLoading(false);
    }
  }, [options]);

  // Reset password
  const resetPassword = useCallback(async (email: string) => {
    setIsLoading(true);
    setError(null);
    
    try {
      const response = await api.auth.resetPassword(email);
      return response;
    } catch (err) {
      const apiError = err as ApiError;
      setError(apiError);
      if (options.onError) {
        options.onError(apiError);
      }
      throw apiError;
    } finally {
      setIsLoading(false);
    }
  }, [options]);

  // Confirm password reset
  const confirmResetPassword = useCallback(async (token: string, newPassword: string) => {
    setIsLoading(true);
    setError(null);
    
    try {
      const response = await api.auth.confirmResetPassword(token, newPassword);
      return response;
    } catch (err) {
      const apiError = err as ApiError;
      setError(apiError);
      if (options.onError) {
        options.onError(apiError);
      }
      throw apiError;
    } finally {
      setIsLoading(false);
    }
  }, [options]);

  return {
    user,
    isLoading,
    isAuthenticated,
    error,
    preferences,
    fetchUser,
    login,
    logout,
    register,
    updateProfile,
    fetchPreferences,
    updatePreferences,
    resetPassword,
    confirmResetPassword
  };
}
