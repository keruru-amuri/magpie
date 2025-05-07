/**
 * User Service for MAGPIE Platform
 * 
 * This service provides functionality for managing user profiles, preferences,
 * and history.
 */

import { api } from './api';
import analyticsService from './analyticsService';

/**
 * Get user profile
 * @returns User profile
 */
export async function getUserProfile(): Promise<any> {
  try {
    return await api.user.getProfile();
  } catch (error) {
    console.error('Error getting user profile:', error);
    throw error;
  }
}

/**
 * Update user profile
 * @param profileData Profile data
 * @returns Updated profile
 */
export async function updateUserProfile(profileData: any): Promise<any> {
  try {
    analyticsService.trackEvent('profile_update', {
      fields: Object.keys(profileData)
    });
    return await api.user.updateProfile(profileData);
  } catch (error) {
    console.error('Error updating user profile:', error);
    throw error;
  }
}

/**
 * Get user preferences
 * @returns User preferences
 */
export async function getUserPreferences(): Promise<any> {
  try {
    return await api.user.getPreferences();
  } catch (error) {
    console.error('Error getting user preferences:', error);
    throw error;
  }
}

/**
 * Update user preferences
 * @param preferences User preferences
 * @returns Updated preferences
 */
export async function updateUserPreferences(preferences: any): Promise<any> {
  try {
    analyticsService.trackEvent('preferences_update', {
      fields: Object.keys(preferences)
    });
    return await api.user.updatePreferences(preferences);
  } catch (error) {
    console.error('Error updating user preferences:', error);
    throw error;
  }
}

/**
 * Get user history
 * @returns User history
 */
export async function getUserHistory(): Promise<any[]> {
  try {
    return await api.user.getHistory();
  } catch (error) {
    console.error('Error getting user history:', error);
    throw error;
  }
}

/**
 * Clear user history
 */
export async function clearUserHistory(): Promise<void> {
  try {
    analyticsService.trackEvent('history_clear', {});
    await api.user.clearHistory();
  } catch (error) {
    console.error('Error clearing user history:', error);
    throw error;
  }
}

/**
 * Get default preferences
 * @returns Default preferences
 */
export function getDefaultPreferences(): Record<string, any> {
  return {
    theme: 'system', // 'light', 'dark', or 'system'
    fontSize: 'medium', // 'small', 'medium', or 'large'
    notifications: {
      email: true,
      inApp: true
    },
    accessibility: {
      highContrast: false,
      reducedMotion: false
    },
    agents: {
      documentation: {
        enabled: true,
        showSuggestions: true
      },
      troubleshooting: {
        enabled: true,
        showSuggestions: true
      },
      maintenance: {
        enabled: true,
        showSuggestions: true
      }
    },
    display: {
      showConfidence: true,
      showAgentType: true,
      compactView: false
    }
  };
}

// Export user service
const userService = {
  getProfile: getUserProfile,
  updateProfile: updateUserProfile,
  getPreferences: getUserPreferences,
  updatePreferences: updateUserPreferences,
  getHistory: getUserHistory,
  clearHistory: clearUserHistory,
  getDefaultPreferences
};

export default userService;
