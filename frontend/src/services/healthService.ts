/**
 * Health Service for MAGPIE Platform
 * 
 * This service provides functionality for checking system health and status.
 */

import { api } from './api';

// Health check interval (5 minutes)
const HEALTH_CHECK_INTERVAL = 5 * 60 * 1000;

// Health check listeners
type HealthListener = (status: HealthStatus) => void;
const listeners: HealthListener[] = [];

// Health status
export interface HealthStatus {
  status: 'healthy' | 'degraded' | 'unhealthy';
  timestamp: number;
  services: {
    api: boolean;
    database: boolean;
    llm: boolean;
    documentation: boolean;
    troubleshooting: boolean;
    maintenance: boolean;
    orchestrator: boolean;
  };
  message?: string;
}

// Current health status
let currentStatus: HealthStatus = {
  status: 'healthy',
  timestamp: Date.now(),
  services: {
    api: true,
    database: true,
    llm: true,
    documentation: true,
    troubleshooting: true,
    maintenance: true,
    orchestrator: true
  }
};

// Health check interval ID
let healthCheckIntervalId: NodeJS.Timeout | null = null;

/**
 * Start health check
 */
export function startHealthCheck(): void {
  if (healthCheckIntervalId) {
    return;
  }

  // Perform initial health check
  checkHealth();

  // Start interval
  healthCheckIntervalId = setInterval(checkHealth, HEALTH_CHECK_INTERVAL);
}

/**
 * Stop health check
 */
export function stopHealthCheck(): void {
  if (healthCheckIntervalId) {
    clearInterval(healthCheckIntervalId);
    healthCheckIntervalId = null;
  }
}

/**
 * Check health
 */
export async function checkHealth(): Promise<HealthStatus> {
  try {
    // Get health status from API
    const response = await api.health.check();

    // Update current status
    currentStatus = {
      status: response.status,
      timestamp: Date.now(),
      services: response.services,
      message: response.message
    };

    // Notify listeners
    notifyListeners();

    return currentStatus;
  } catch (error) {
    console.error('Error checking health:', error);

    // Update current status to unhealthy
    currentStatus = {
      status: 'unhealthy',
      timestamp: Date.now(),
      services: {
        api: false,
        database: false,
        llm: false,
        documentation: false,
        troubleshooting: false,
        maintenance: false,
        orchestrator: false
      },
      message: 'Failed to connect to health check endpoint'
    };

    // Notify listeners
    notifyListeners();

    return currentStatus;
  }
}

/**
 * Get detailed health status
 * @returns Detailed health status
 */
export async function getDetailedHealth(): Promise<any> {
  try {
    return await api.health.detailed();
  } catch (error) {
    console.error('Error getting detailed health:', error);
    throw error;
  }
}

/**
 * Get current health status
 * @returns Current health status
 */
export function getCurrentHealth(): HealthStatus {
  return { ...currentStatus };
}

/**
 * Add health listener
 * @param listener Health listener
 * @returns Function to remove listener
 */
export function addHealthListener(listener: HealthListener): () => void {
  listeners.push(listener);

  // Notify listener of current status
  listener(currentStatus);

  return () => {
    const index = listeners.indexOf(listener);
    if (index !== -1) {
      listeners.splice(index, 1);
    }
  };
}

/**
 * Notify all listeners of health status change
 */
function notifyListeners(): void {
  listeners.forEach(listener => {
    try {
      listener(currentStatus);
    } catch (error) {
      console.error('Error in health listener:', error);
    }
  });
}

// Export health service
const healthService = {
  startCheck: startHealthCheck,
  stopCheck: stopHealthCheck,
  check: checkHealth,
  getDetailed: getDetailedHealth,
  getCurrent: getCurrentHealth,
  addListener: addHealthListener
};

export default healthService;
