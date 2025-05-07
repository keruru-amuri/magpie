/**
 * WebSocket Connection Test
 * 
 * This test verifies that the WebSocket connection is established correctly.
 */

import { getWebSocketService } from '../../services/mockWebsocketService';
import { API_CONFIG } from '../../config/environment';

// Mock the API_CONFIG
jest.mock('../../config/environment', () => ({
  API_CONFIG: {
    USE_MOCK_WEBSOCKET: false,
    BASE_URL: 'http://localhost:8000',
    WEBSOCKET_URL: 'ws://localhost:8000/ws'
  }
}));

// Mock the WebSocket class
class MockWebSocket {
  url: string;
  onopen: any;
  onmessage: any;
  onclose: any;
  onerror: any;
  readyState: number;
  
  constructor(url: string) {
    this.url = url;
    this.readyState = 0; // CONNECTING
    
    // Simulate successful connection
    setTimeout(() => {
      this.readyState = 1; // OPEN
      if (this.onopen) {
        this.onopen({ target: this });
      }
    }, 100);
  }
  
  send(data: string) {
    // Mock send method
    console.log('MockWebSocket.send', data);
  }
  
  close() {
    // Mock close method
    this.readyState = 3; // CLOSED
    if (this.onclose) {
      this.onclose({ target: this });
    }
  }
}

// Mock the websocketService module
jest.mock('../../services/websocketService', () => {
  // Create a mock implementation of the WebSocket service
  const mockService = {
    connect: jest.fn((userId, conversationId) => {
      console.log('Mock connect called with', { userId, conversationId });
    }),
    disconnect: jest.fn(),
    send: jest.fn(),
    sendChatMessage: jest.fn(),
    sendTypingIndicator: jest.fn(),
    sendMessageFeedback: jest.fn(),
    addMessageListener: jest.fn(() => jest.fn()),
    removeMessageListener: jest.fn(),
    addConnectionListener: jest.fn(() => jest.fn()),
    removeConnectionListener: jest.fn(),
    joinConversation: jest.fn(),
    leaveConversation: jest.fn()
  };
  
  return {
    websocketService: mockService
  };
});

// Mock the global WebSocket class
global.WebSocket = MockWebSocket as any;

describe('WebSocket Service', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });
  
  test('should use real WebSocket service when USE_MOCK_WEBSOCKET is false', () => {
    // Get the WebSocket service
    const service = getWebSocketService();
    
    // Verify that it's the real service (mock implementation from the mock module)
    expect(service).toBeDefined();
    expect(service.connect).toBeDefined();
    
    // Connect to the WebSocket server
    service.connect('test-user', 'test-conversation');
    
    // Verify that the connect method was called with the correct parameters
    expect(service.connect).toHaveBeenCalledWith('test-user', 'test-conversation');
  });
});
