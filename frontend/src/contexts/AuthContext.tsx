'use client';

import React, { createContext, useState, useEffect, useContext } from 'react';
import { useRouter } from 'next/navigation';
import { signIn, signOut } from '@/auth';
import { useNotifications } from '../hooks/useNotifications';
import { useAnalytics } from '../hooks/useAnalytics';

interface User {
  id: string;
  name: string;
  email: string;
  role: string;
  image?: string;
  firstName?: string;
  lastName?: string;
  createdAt?: string;
  updatedAt?: string;
  preferences?: Record<string, any>;
}

interface AuthContextType {
  user: User | null;
  isLoading: boolean;
  isAuthenticated: boolean;
  login: (email: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
  register: (userData: any) => Promise<void>;
  requestPasswordReset: (email: string) => Promise<void>;
  confirmPasswordReset: (token: string, newPassword: string) => Promise<void>;
  updateUser: (userData: Partial<User>) => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const router = useRouter();

  // Get notifications and analytics hooks
  const notifications = useNotifications();
  const analytics = useAnalytics();

  // Initialize with mock user for development/testing
  useEffect(() => {
    // For testing purposes, provide a mock user in development
    const isDevelopment = process.env.NODE_ENV === 'development';

    if (isDevelopment) {
      // Provide a mock user for development/testing
      const mockUser: User = {
        id: '1',
        name: 'Test User',
        email: 'test@example.com',
        role: 'admin',
        firstName: 'Test',
        lastName: 'User',
      };

      setUser(mockUser);
      setIsAuthenticated(true);
      console.log('Using mock user for development:', mockUser);

      // Track user session
      analytics.trackEvent('session_start', { userId: mockUser.id });
    } else {
      setUser(null);
      setIsAuthenticated(false);
    }

    setIsLoading(false);
  }, [analytics]);

  // Login user (mock implementation for testing)
  const login = async (email: string, password: string) => {
    setIsLoading(true);
    try {
      // For development, just simulate a successful login
      if (process.env.NODE_ENV === 'development') {
        const mockUser: User = {
          id: '1',
          name: 'Test User',
          email: email || 'test@example.com',
          role: 'admin',
          firstName: 'Test',
          lastName: 'User',
        };

        setUser(mockUser);
        setIsAuthenticated(true);

        // Show success notification
        notifications.showSuccess(
          'Login Successful',
          `Welcome back, ${mockUser.firstName}!`
        );

        // Track login event
        analytics.trackEvent('login', { userId: mockUser.id });

        return { ok: true };
      }

      throw new Error('Login not implemented in test mode');
    } catch (error) {
      console.error('Login failed:', error);

      // Show error notification
      notifications.showError(
        'Login Failed',
        error instanceof Error ? error.message : 'Invalid email or password'
      );

      throw error;
    } finally {
      setIsLoading(false);
    }
  };

  // Logout user (mock implementation for testing)
  const logout = async () => {
    setIsLoading(true);
    try {
      // Track logout event before clearing user
      if (user) {
        analytics.trackEvent('logout', { userId: user.id });
      }

      // Clear user state
      setUser(null);
      setIsAuthenticated(false);

      // Show success notification
      notifications.showSuccess(
        'Logout Successful',
        'You have been logged out successfully'
      );

      // Redirect to login page
      router.push('/login');
    } catch (error) {
      console.error('Logout failed:', error);

      // Show error notification
      notifications.showError(
        'Logout Failed',
        error instanceof Error ? error.message : 'Failed to logout'
      );

      throw error;
    } finally {
      setIsLoading(false);
    }
  };

  // Register user (mock implementation for testing)
  const register = async (userData: any) => {
    setIsLoading(true);
    try {
      // For development, just simulate a successful registration
      if (process.env.NODE_ENV === 'development') {
        // Show success notification
        notifications.showSuccess(
          'Registration Successful',
          'Your account has been created successfully. Please login.'
        );

        return { success: true, user: { ...userData, id: '2' } };
      }

      throw new Error('Registration not implemented in test mode');
    } catch (error) {
      console.error('Registration failed:', error);

      // Show error notification
      notifications.showError(
        'Registration Failed',
        error instanceof Error ? error.message : 'Failed to create account'
      );

      throw error;
    } finally {
      setIsLoading(false);
    }
  };

  // Request password reset (mock implementation for testing)
  const requestPasswordReset = async (email: string) => {
    setIsLoading(true);
    try {
      // For development, just simulate a successful password reset request
      // Show success notification regardless of response for security
      notifications.showSuccess(
        'Password Reset Requested',
        'If an account with that email exists, you will receive a password reset link'
      );
    } catch (error) {
      console.error('Password reset request failed:', error);

      // Show success notification anyway for security
      notifications.showSuccess(
        'Password Reset Requested',
        'If an account with that email exists, you will receive a password reset link'
      );
    } finally {
      setIsLoading(false);
    }
  };

  // Confirm password reset (mock implementation for testing)
  const confirmPasswordReset = async (token: string, newPassword: string) => {
    setIsLoading(true);
    try {
      // For development, just simulate a successful password reset
      if (process.env.NODE_ENV === 'development') {
        // Show success notification
        notifications.showSuccess(
          'Password Reset Successful',
          'Your password has been reset successfully. Please login with your new password.'
        );

        return { success: true };
      }

      throw new Error('Password reset not implemented in test mode');
    } catch (error) {
      console.error('Password reset confirmation failed:', error);

      // Show error notification
      notifications.showError(
        'Password Reset Failed',
        error instanceof Error ? error.message : 'Failed to reset password'
      );

      throw error;
    } finally {
      setIsLoading(false);
    }
  };

  // Update user data
  const updateUser = (userData: Partial<User>) => {
    if (!user) return;

    setUser({
      ...user,
      ...userData
    });
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        isLoading,
        isAuthenticated,
        login,
        logout,
        register,
        requestPasswordReset,
        confirmPasswordReset,
        updateUser
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}
