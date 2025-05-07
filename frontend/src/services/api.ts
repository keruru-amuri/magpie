import {
  ApiError,
  LoginRequest,
  LoginResponse,
  OrchestratorRequest,
  OrchestratorResponse,
  RoutingInfo,
  DocumentSearchRequest,
  TroubleshootingRequest,
  MaintenanceProcedureRequest
} from '../types/api';
import cacheService from './cacheService';
import { API_CONFIG, CACHE_CONFIG } from '../config/environment';

// API base URL and prefix
const API_BASE_URL = API_CONFIG.BASE_URL;
const API_V1_PREFIX = API_CONFIG.VERSION_PREFIX;

// Cache configuration
const CACHE_ENABLED = CACHE_CONFIG.ENABLED;
const CACHE_EXPIRATION = CACHE_CONFIG.EXPIRATION;

// Endpoints that should be cached
const CACHEABLE_ENDPOINTS = [
  '/documentation/search',
  '/documentation/documents/',
  '/documentation/recent',
  '/documentation/popular',
  '/agents',
  '/agents/',
  '/troubleshooting/solutions/',
  '/maintenance/procedures/',
];

// Check if an endpoint is cacheable
const isCacheableEndpoint = (endpoint: string): boolean => {
  return CACHEABLE_ENDPOINTS.some(cacheable => endpoint.includes(cacheable));
};

// Generate cache key for an endpoint
const generateCacheKey = (endpoint: string, method: string, data?: any): string => {
  const dataString = data ? JSON.stringify(data) : '';
  return `${method}_${endpoint}_${dataString}`;
};

// Helper function for handling API responses
async function handleResponse(response: Response) {
  if (!response.ok) {
    // Try to get error message from response
    let errorMessage;
    let errorDetails: Record<string, any> = {};

    try {
      const errorData = await response.json();
      errorMessage = errorData.detail || errorData.message || `API error: ${response.status}`;
      errorDetails = errorData;
    } catch (e) {
      errorMessage = `API error: ${response.status}`;
    }

    const apiError: ApiError = {
      status: response.status,
      message: errorMessage,
      details: errorDetails
    };

    throw apiError;
  }

  // Check if response is empty
  const contentType = response.headers.get('content-type');
  if (contentType && contentType.includes('application/json')) {
    return await response.json();
  }

  return await response.text();
}

// Import mock data service
import { getMockResponse } from './mockData';

// Helper function for making API requests
async function apiRequest<T = any>(
  endpoint: string,
  method: string = 'GET',
  data?: any,
  customHeaders: Record<string, string> = {},
  options: {
    useCache?: boolean;
    cacheExpiration?: number;
    forceRefresh?: boolean;
    useMockData?: boolean;
  } = {}
): Promise<T> {
  // Default options
  const {
    useCache = CACHE_ENABLED,
    cacheExpiration = CACHE_EXPIRATION,
    forceRefresh = false,
    useMockData = API_CONFIG.USE_MOCK_DATA
  } = options;

  // Add API version prefix if not already included
  const fullEndpoint = endpoint.startsWith('/api')
    ? endpoint
    : `${API_V1_PREFIX}${endpoint}`;

  const url = `${API_BASE_URL}${fullEndpoint}`;

  // Check if endpoint is cacheable and method is GET
  const shouldUseCache = useCache &&
    method === 'GET' &&
    isCacheableEndpoint(fullEndpoint) &&
    !forceRefresh;

  // Generate cache key
  const cacheKey = generateCacheKey(fullEndpoint, method, data);

  // Try to get from cache first
  if (shouldUseCache) {
    const cachedData = cacheService.get<T>(cacheKey);
    if (cachedData) {
      console.log(`Using cached data for ${fullEndpoint}`);
      return cachedData;
    }
  }

  // Use mock data if configured
  if (useMockData) {
    console.log(`Using mock data for ${fullEndpoint}`);
    const mockResponse = getMockResponse(fullEndpoint, method, data);

    // Cache the mock response if it's cacheable
    if (shouldUseCache) {
      cacheService.set(cacheKey, mockResponse, cacheExpiration);
    }

    return mockResponse as T;
  }

  // Default headers
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...customHeaders,
  };

  // Add auth token if available
  const token = localStorage.getItem('authToken');
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  // Request options
  const requestOptions: RequestInit = {
    method,
    headers,
    credentials: 'include', // Include cookies for cross-origin requests
  };

  // Add body if data is provided
  if (data && ['POST', 'PUT', 'PATCH'].includes(method)) {
    requestOptions.body = JSON.stringify(data);
  }

  // Add retry logic
  const maxRetries = API_CONFIG.MAX_RETRIES;
  let retries = 0;
  let lastError: any;

  while (retries < maxRetries) {
    try {
      const response = await fetch(url, requestOptions);
      const responseData = await handleResponse(response);

      // Cache the response if it's cacheable
      if (shouldUseCache) {
        cacheService.set(cacheKey, responseData, cacheExpiration);
      }

      return responseData;
    } catch (error) {
      lastError = error;

      // Check if we have cached data to return in case of error
      if (shouldUseCache && retries === maxRetries - 1) {
        const cachedData = cacheService.get<T>(cacheKey);
        if (cachedData) {
          console.log(`Using cached data after error for ${fullEndpoint}`);
          return cachedData;
        }
      }

      // Check if we should fall back to mock data
      if (retries === maxRetries - 1 && API_CONFIG.USE_MOCK_DATA) {
        console.log(`Falling back to mock data after error for ${fullEndpoint}`);
        return getMockResponse(fullEndpoint, method, data) as T;
      }

      // Only retry on network errors or 5xx server errors
      if (error instanceof Error && !(error as ApiError).status) {
        // Network error
        retries++;
        if (retries < maxRetries) {
          // Exponential backoff
          const delay = Math.min(1000 * Math.pow(2, retries), 10000);
          await new Promise(resolve => setTimeout(resolve, delay));
          continue;
        }
      } else if ((error as ApiError).status >= 500) {
        // Server error
        retries++;
        if (retries < maxRetries) {
          // Exponential backoff
          const delay = Math.min(1000 * Math.pow(2, retries), 10000);
          await new Promise(resolve => setTimeout(resolve, delay));
          continue;
        }
      }

      // Client error or max retries reached
      throw error;
    }
  }

  throw lastError;
}

// API endpoints
export const api = {
  // Auth endpoints
  auth: {
    login: (credentials: LoginRequest): Promise<LoginResponse> =>
      apiRequest('/auth/login', 'POST', credentials),
    logout: (): Promise<void> =>
      apiRequest('/auth/logout', 'POST'),
    getUser: (): Promise<any> =>
      apiRequest('/auth/user'),
    register: (userData: any): Promise<any> =>
      apiRequest('/auth/register', 'POST', userData),
    refreshToken: (refreshToken: string): Promise<any> =>
      apiRequest('/auth/refresh', 'POST', { refresh_token: refreshToken }),
    resetPassword: (email: string): Promise<any> =>
      apiRequest('/auth/password-reset', 'POST', { email }),
    confirmResetPassword: (token: string, newPassword: string): Promise<any> =>
      apiRequest('/auth/password-reset/confirm', 'POST', { token, new_password: newPassword }),
  },

  // Orchestrator endpoints
  orchestrator: {
    query: (request: OrchestratorRequest): Promise<OrchestratorResponse> =>
      apiRequest('/orchestrator/query', 'POST', request),
    getRoutingInfo: (query: string, conversationId?: string): Promise<RoutingInfo> =>
      apiRequest(`/orchestrator/routing-info?query=${encodeURIComponent(query)}${conversationId ? `&conversation_id=${conversationId}` : ''}`),
    getConversationHistory: (conversationId: string): Promise<any> =>
      apiRequest(`/orchestrator/conversation/${conversationId}`),
    deleteConversation: (conversationId: string): Promise<void> =>
      apiRequest(`/orchestrator/conversation/${conversationId}`, 'DELETE'),
  },

  // Agents endpoints
  agents: {
    getAll: (): Promise<any[]> =>
      apiRequest('/agents'),
    getById: (id: string): Promise<any> =>
      apiRequest(`/agents/${id}`),
    getCapabilities: (agentType: string): Promise<any> =>
      apiRequest(`/agents/${agentType}/capabilities`),
  },

  // Documentation agent endpoints
  documentation: {
    search: (query: string): Promise<any> =>
      apiRequest(`/documentation/search?q=${encodeURIComponent(query)}`),
    advancedSearch: (request: DocumentSearchRequest): Promise<any> =>
      apiRequest('/documentation/search', 'POST', request),
    getDocument: (id: string): Promise<any> =>
      apiRequest(`/documentation/documents/${id}`),
    getRecentDocuments: (): Promise<any[]> =>
      apiRequest('/documentation/recent'),
    getPopularDocuments: (): Promise<any[]> =>
      apiRequest('/documentation/popular'),
    getCrossReferences: (documentId: string): Promise<any[]> =>
      apiRequest(`/documentation/cross-references/${documentId}`),
  },

  // Troubleshooting agent endpoints
  troubleshooting: {
    analyze: (problem: TroubleshootingRequest): Promise<any> =>
      apiRequest('/troubleshooting/analyze', 'POST', problem),
    getSolutions: (problemId: string): Promise<any> =>
      apiRequest(`/troubleshooting/solutions/${problemId}`),
    getStepDetails: (problemId: string, stepId: string): Promise<any> =>
      apiRequest(`/troubleshooting/solutions/${problemId}/steps/${stepId}`),
    updateStepStatus: (problemId: string, stepId: string, status: string): Promise<any> =>
      apiRequest(`/troubleshooting/solutions/${problemId}/steps/${stepId}/status`, 'PUT', { status }),
    getSimilarProblems: (problemId: string): Promise<any[]> =>
      apiRequest(`/troubleshooting/similar/${problemId}`),
  },

  // Maintenance agent endpoints
  maintenance: {
    generateProcedure: (params: MaintenanceProcedureRequest): Promise<any> =>
      apiRequest('/maintenance/generate', 'POST', params),
    getProcedure: (id: string): Promise<any> =>
      apiRequest(`/maintenance/procedures/${id}`),
    updateStepStatus: (procedureId: string, stepId: string, completed: boolean): Promise<any> =>
      apiRequest(`/maintenance/procedures/${procedureId}/steps/${stepId}`, 'PUT', { completed }),
    getToolsAndParts: (procedureId: string): Promise<any> =>
      apiRequest(`/maintenance/procedures/${procedureId}/resources`),
    getSafetyPrecautions: (procedureId: string): Promise<any[]> =>
      apiRequest(`/maintenance/procedures/${procedureId}/safety`),
  },

  // Chat endpoints
  chat: {
    sendMessage: (message: string, conversationId?: string): Promise<any> =>
      apiRequest('/chat/message', 'POST', {
        message,
        conversation_id: conversationId
      }),
    getConversations: (): Promise<any[]> =>
      apiRequest('/chat/conversations'),
    getConversation: (id: string): Promise<any> =>
      apiRequest(`/chat/conversations/${id}`),
    createConversation: (title?: string): Promise<any> =>
      apiRequest('/chat/conversations', 'POST', { title }),
    updateConversation: (id: string, title: string): Promise<any> =>
      apiRequest(`/chat/conversations/${id}`, 'PUT', { title }),
    deleteConversation: (id: string): Promise<void> =>
      apiRequest(`/chat/conversations/${id}`, 'DELETE'),
  },

  // User endpoints
  user: {
    getProfile: (): Promise<any> =>
      apiRequest('/users/me'),
    updateProfile: (profileData: any): Promise<any> =>
      apiRequest('/users/me', 'PUT', profileData),
    getPreferences: (): Promise<any> =>
      apiRequest('/users/me/preferences'),
    updatePreferences: (preferences: any): Promise<any> =>
      apiRequest('/users/me/preferences', 'PUT', preferences),
    getHistory: (): Promise<any[]> =>
      apiRequest('/users/me/history'),
    clearHistory: (): Promise<void> =>
      apiRequest('/users/me/history', 'DELETE'),
  },

  // Health and monitoring endpoints
  health: {
    check: (): Promise<any> =>
      apiRequest('/health'),
    detailed: (): Promise<any> =>
      apiRequest('/health/detailed'),
  }
};

export default api;
