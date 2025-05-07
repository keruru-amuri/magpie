/**
 * Services index file
 * 
 * This file exports all services for the MAGPIE platform.
 */

// API and authentication
export { api } from './api';
export { default as authService } from './authService';

// Agent services
export { default as agentService } from './agentService';
export { default as orchestratorService } from './orchestratorService';
export { default as conversationService } from './conversationService';

// User services
export { default as userService } from './userService';

// Utility services
export { default as analyticsService } from './analyticsService';
export { default as cacheService } from './cacheService';
export { default as healthService } from './healthService';
export { default as notificationService } from './notificationService';

// WebSocket services
export { default as websocketService, mockWebsocketService, getWebSocketService } from './mockWebsocketService';
