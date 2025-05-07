/**
 * Authentication Service for MAGPIE Platform
 * 
 * This service provides authentication functionality for user login, registration,
 * and token management.
 */

import { api } from './api';
import { LoginRequest, LoginResponse } from '../types/api';

// Token storage keys
const ACCESS_TOKEN_KEY = 'magpie_access_token';
const REFRESH_TOKEN_KEY = 'magpie_refresh_token';
const USER_DATA_KEY = 'magpie_user_data';

// Token expiration buffer (5 minutes in milliseconds)
const TOKEN_EXPIRATION_BUFFER = 5 * 60 * 1000;

// Authentication service
class AuthService {
  private accessToken: string | null = null;
  private refreshToken: string | null = null;
  private tokenExpiration: number | null = null;
  private refreshPromise: Promise<string> | null = null;

  constructor() {
    // Initialize tokens from storage
    this.loadTokensFromStorage();
  }

  /**
   * Load tokens from storage
   */
  private loadTokensFromStorage(): void {
    if (typeof window === 'undefined') {
      return;
    }

    try {
      this.accessToken = localStorage.getItem(ACCESS_TOKEN_KEY);
      this.refreshToken = localStorage.getItem(REFRESH_TOKEN_KEY);
      
      const expirationStr = localStorage.getItem('magpie_token_expiration');
      this.tokenExpiration = expirationStr ? parseInt(expirationStr, 10) : null;
    } catch (error) {
      console.error('Error loading tokens from storage:', error);
      this.clearTokens();
    }
  }

  /**
   * Save tokens to storage
   * @param accessToken Access token
   * @param refreshToken Refresh token
   * @param expiresIn Expiration time in seconds
   */
  private saveTokensToStorage(
    accessToken: string,
    refreshToken: string,
    expiresIn: number
  ): void {
    try {
      localStorage.setItem(ACCESS_TOKEN_KEY, accessToken);
      localStorage.setItem(REFRESH_TOKEN_KEY, refreshToken);
      
      const expirationTime = Date.now() + expiresIn * 1000;
      localStorage.setItem('magpie_token_expiration', expirationTime.toString());
      
      this.accessToken = accessToken;
      this.refreshToken = refreshToken;
      this.tokenExpiration = expirationTime;
    } catch (error) {
      console.error('Error saving tokens to storage:', error);
    }
  }

  /**
   * Clear tokens from storage
   */
  private clearTokens(): void {
    try {
      localStorage.removeItem(ACCESS_TOKEN_KEY);
      localStorage.removeItem(REFRESH_TOKEN_KEY);
      localStorage.removeItem('magpie_token_expiration');
      localStorage.removeItem(USER_DATA_KEY);
      
      this.accessToken = null;
      this.refreshToken = null;
      this.tokenExpiration = null;
    } catch (error) {
      console.error('Error clearing tokens from storage:', error);
    }
  }

  /**
   * Check if token is expired or about to expire
   * @returns True if token is expired or about to expire
   */
  private isTokenExpiredOrExpiring(): boolean {
    if (!this.tokenExpiration) {
      return true;
    }
    
    return Date.now() + TOKEN_EXPIRATION_BUFFER > this.tokenExpiration;
  }

  /**
   * Get access token (refreshing if needed)
   * @returns Access token
   */
  async getAccessToken(): Promise<string | null> {
    // If no token, return null
    if (!this.accessToken || !this.refreshToken) {
      return null;
    }
    
    // If token is not expired, return it
    if (!this.isTokenExpiredOrExpiring()) {
      return this.accessToken;
    }
    
    // If token is expired, refresh it
    try {
      // If already refreshing, wait for that promise
      if (this.refreshPromise) {
        return await this.refreshPromise;
      }
      
      // Start refreshing
      this.refreshPromise = this.refreshAccessToken();
      const newToken = await this.refreshPromise;
      this.refreshPromise = null;
      
      return newToken;
    } catch (error) {
      console.error('Error refreshing token:', error);
      this.clearTokens();
      return null;
    }
  }

  /**
   * Refresh access token
   * @returns New access token
   */
  private async refreshAccessToken(): Promise<string> {
    if (!this.refreshToken) {
      throw new Error('No refresh token available');
    }
    
    try {
      const response = await api.auth.refreshToken(this.refreshToken);
      
      this.saveTokensToStorage(
        response.access_token,
        response.refresh_token,
        response.expires_in
      );
      
      return response.access_token;
    } catch (error) {
      console.error('Error refreshing token:', error);
      this.clearTokens();
      throw error;
    }
  }

  /**
   * Login user
   * @param credentials Login credentials
   * @returns Login response
   */
  async login(credentials: LoginRequest): Promise<LoginResponse> {
    try {
      const response = await api.auth.login(credentials);
      
      this.saveTokensToStorage(
        response.access_token,
        response.refresh_token,
        response.expires_in
      );
      
      // Save user data
      localStorage.setItem(USER_DATA_KEY, JSON.stringify(response.user));
      
      return response;
    } catch (error) {
      console.error('Error logging in:', error);
      throw error;
    }
  }

  /**
   * Logout user
   */
  async logout(): Promise<void> {
    try {
      // Call logout API if token is available
      if (this.accessToken) {
        await api.auth.logout();
      }
    } catch (error) {
      console.error('Error logging out:', error);
    } finally {
      // Clear tokens regardless of API call success
      this.clearTokens();
    }
  }

  /**
   * Check if user is authenticated
   * @returns True if user is authenticated
   */
  async isAuthenticated(): Promise<boolean> {
    try {
      const token = await this.getAccessToken();
      return !!token;
    } catch (error) {
      return false;
    }
  }

  /**
   * Get current user data
   * @returns User data or null if not authenticated
   */
  async getCurrentUser(): Promise<any | null> {
    try {
      // Try to get user data from storage
      const userDataStr = localStorage.getItem(USER_DATA_KEY);
      if (userDataStr) {
        return JSON.parse(userDataStr);
      }
      
      // If not in storage but authenticated, fetch from API
      if (await this.isAuthenticated()) {
        const userData = await api.auth.getUser();
        localStorage.setItem(USER_DATA_KEY, JSON.stringify(userData));
        return userData;
      }
      
      return null;
    } catch (error) {
      console.error('Error getting current user:', error);
      return null;
    }
  }

  /**
   * Register a new user
   * @param userData User registration data
   * @returns Registration response
   */
  async register(userData: any): Promise<any> {
    try {
      return await api.auth.register(userData);
    } catch (error) {
      console.error('Error registering user:', error);
      throw error;
    }
  }

  /**
   * Request password reset
   * @param email User email
   * @returns Password reset response
   */
  async requestPasswordReset(email: string): Promise<any> {
    try {
      return await api.auth.resetPassword(email);
    } catch (error) {
      console.error('Error requesting password reset:', error);
      throw error;
    }
  }

  /**
   * Confirm password reset
   * @param token Reset token
   * @param newPassword New password
   * @returns Password reset confirmation response
   */
  async confirmPasswordReset(token: string, newPassword: string): Promise<any> {
    try {
      return await api.auth.confirmResetPassword(token, newPassword);
    } catch (error) {
      console.error('Error confirming password reset:', error);
      throw error;
    }
  }
}

// Create singleton instance
const authService = new AuthService();

export default authService;
