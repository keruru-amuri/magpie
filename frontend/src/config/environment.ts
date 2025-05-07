/**
 * Environment Configuration
 *
 * This file contains environment-specific configuration for the MAGPIE platform.
 * Values are loaded from environment variables with sensible defaults.
 */

// API Configuration
export const API_CONFIG = {
  // Base URL for API requests
  BASE_URL: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000',

  // API version prefix
  VERSION_PREFIX: process.env.NEXT_PUBLIC_API_VERSION || '/api/v1',

  // Whether to use mock data instead of real API
  USE_MOCK_DATA: process.env.NEXT_PUBLIC_USE_MOCK_DATA === 'true',

  // Whether to use mock WebSocket instead of real WebSocket
  USE_MOCK_WEBSOCKET: process.env.NEXT_PUBLIC_USE_MOCK_WEBSOCKET === 'true',

  // WebSocket URL
  WEBSOCKET_URL: process.env.NEXT_PUBLIC_WEBSOCKET_URL || 'ws://localhost:8000/ws',

  // Request timeout in milliseconds
  TIMEOUT: parseInt(process.env.NEXT_PUBLIC_API_TIMEOUT || '30000', 10),

  // Maximum number of retries for failed requests
  MAX_RETRIES: parseInt(process.env.NEXT_PUBLIC_API_MAX_RETRIES || '3', 10),
};

// Cache Configuration
export const CACHE_CONFIG = {
  // Whether to enable caching
  ENABLED: process.env.NEXT_PUBLIC_ENABLE_CACHE === 'true',

  // Cache expiration time in milliseconds (default: 24 hours)
  EXPIRATION: parseInt(process.env.NEXT_PUBLIC_CACHE_EXPIRATION || '86400000', 10),
};

// Analytics Configuration
export const ANALYTICS_CONFIG = {
  // Whether to enable analytics
  ENABLED: process.env.NEXT_PUBLIC_ENABLE_ANALYTICS === 'true',

  // Analytics endpoint
  ENDPOINT: process.env.NEXT_PUBLIC_ANALYTICS_ENDPOINT || '/api/v1/analytics',
};

// Feature Flags
export const FEATURE_FLAGS = {
  // Whether to enable the documentation agent
  ENABLE_DOCUMENTATION_AGENT: process.env.NEXT_PUBLIC_ENABLE_DOCUMENTATION_AGENT !== 'false',

  // Whether to enable the troubleshooting agent
  ENABLE_TROUBLESHOOTING_AGENT: process.env.NEXT_PUBLIC_ENABLE_TROUBLESHOOTING_AGENT !== 'false',

  // Whether to enable the maintenance agent
  ENABLE_MAINTENANCE_AGENT: process.env.NEXT_PUBLIC_ENABLE_MAINTENANCE_AGENT !== 'false',

  // Whether to enable the orchestrator
  ENABLE_ORCHESTRATOR: process.env.NEXT_PUBLIC_ENABLE_ORCHESTRATOR !== 'false',

  // Whether to enable authentication
  ENABLE_AUTH: process.env.NEXT_PUBLIC_ENABLE_AUTH !== 'false',

  // Whether to enable feedback
  ENABLE_FEEDBACK: process.env.NEXT_PUBLIC_ENABLE_FEEDBACK !== 'false',
};

// Default configuration for development
if (process.env.NODE_ENV === 'development' && typeof window !== 'undefined') {
  // In development, use mock data by default unless explicitly set
  if (process.env.NEXT_PUBLIC_USE_MOCK_DATA === undefined) {
    (API_CONFIG as any).USE_MOCK_DATA = true;
  }

  // In development, use mock WebSocket by default unless explicitly set
  if (process.env.NEXT_PUBLIC_USE_MOCK_WEBSOCKET === undefined) {
    (API_CONFIG as any).USE_MOCK_WEBSOCKET = true;
  }

  // Enable caching in development by default
  if (process.env.NEXT_PUBLIC_ENABLE_CACHE === undefined) {
    (CACHE_CONFIG as any).ENABLED = true;
  }

  // Disable analytics in development by default
  if (process.env.NEXT_PUBLIC_ENABLE_ANALYTICS === undefined) {
    (ANALYTICS_CONFIG as any).ENABLED = false;
  }
}

// Export all configuration
export default {
  API: API_CONFIG,
  CACHE: CACHE_CONFIG,
  ANALYTICS: ANALYTICS_CONFIG,
  FEATURES: FEATURE_FLAGS,
};
