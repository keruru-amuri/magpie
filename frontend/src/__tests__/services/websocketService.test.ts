/**
 * WebSocket Service Tests
 *
 * This file contains tests for the WebSocket service.
 */

import { mockWebsocketService } from '../../services/mockWebsocketService';

// Mock WebSocket
class MockWebSocket {
  url: string;
  onopen: ((this: WebSocket, ev: Event) => any) | null = null;
  onmessage: ((this: WebSocket, ev: MessageEvent) => any) | null = null;
  onclose: ((this: WebSocket, ev: CloseEvent) => any) | null = null;
  onerror: ((this: WebSocket, ev: Event) => any) | null = null;
  readyState: number = WebSocket.CONNECTING;

  constructor(url: string) {
    this.url = url;
    setTimeout(() => {
      this.readyState = WebSocket.OPEN;
      if (this.onopen) {
        this.onopen(new Event('open'));
      }
    }, 0);
  }

  send(data: string): void {
    // Mock send
  }

  close(): void {
    this.readyState = WebSocket.CLOSED;
    if (this.onclose) {
      this.onclose(new CloseEvent('close'));
    }
  }
}

// Mock global WebSocket
global.WebSocket = MockWebSocket as any;

describe('WebSocket Service', () => {
  // Reset mocks before each test
  beforeEach(() => {
    jest.clearAllMocks();
    localStorage.clear();
  });

  describe('Connection', () => {
    test('connect should set up WebSocket connection', () => {
      // Set up spy
      const connectSpy = jest.spyOn(mockWebsocketService, 'connect');

      // Connect
      mockWebsocketService.connect('user123');

      // Check connect was called with user123
      expect(connectSpy).toHaveBeenCalled();
      expect(connectSpy.mock.calls[0][0]).toBe('user123');
    });

    test('disconnect should close WebSocket connection', () => {
      // Set up spy
      const disconnectSpy = jest.spyOn(mockWebsocketService, 'disconnect');

      // Connect and disconnect
      mockWebsocketService.connect('user123');
      mockWebsocketService.disconnect();

      // Check disconnect was called
      expect(disconnectSpy).toHaveBeenCalled();
    });
  });

  describe('Message Handling', () => {
    test('should handle incoming messages', () => {
      // Set up listener
      const listener = jest.fn();
      mockWebsocketService.addMessageListener(listener);

      // Connect
      mockWebsocketService.connect('user123');

      // Simulate incoming message
      const message = {
        type: 'message',
        payload: {
          message: {
            id: '123',
            content: 'Test message',
            role: 'assistant',
            timestamp: new Date().toISOString()
          },
          conversationId: '456'
        }
      };

      // Manually trigger message handling
      (mockWebsocketService as any).simulateIncomingMessage(message);

      // Check listener was called with message
      expect(listener).toHaveBeenCalledWith(message);
    });

    test('should send messages', () => {
      // Set up spy
      const sendSpy = jest.spyOn(mockWebsocketService, 'send');

      // Connect
      mockWebsocketService.connect('user123');

      // Send message
      mockWebsocketService.sendChatMessage('Test message', '456');

      // Check send was called with correct arguments
      expect(sendSpy).toHaveBeenCalledWith('message', {
        message: 'Test message',
        conversation_id: '456',
        force_agent_type: undefined
      });
    });
  });

  describe('Conversation Management', () => {
    test('should join conversation', () => {
      // Set up spy
      const sendSpy = jest.spyOn(mockWebsocketService, 'send');

      // Connect
      mockWebsocketService.connect('user123');

      // Join conversation
      mockWebsocketService.joinConversation('456');

      // Check send was called with correct arguments
      expect(sendSpy).toHaveBeenCalledWith('join_conversation', {
        conversation_id: '456'
      });
    });

    test('should leave conversation', () => {
      // Set up spy
      const sendSpy = jest.spyOn(mockWebsocketService, 'send');

      // Connect and join conversation
      mockWebsocketService.connect('user123');
      mockWebsocketService.joinConversation('456');

      // Leave conversation
      mockWebsocketService.leaveConversation();

      // Check send was called with correct arguments
      expect(sendSpy).toHaveBeenCalledWith('leave_conversation', {
        conversation_id: '456'
      });
    });
  });

  describe('Listeners', () => {
    test('should add and remove message listeners', () => {
      // Set up listener
      const listener = jest.fn();

      // Add listener
      mockWebsocketService.addMessageListener(listener);

      // Connect
      mockWebsocketService.connect('user123');

      // Simulate incoming message
      const message = {
        type: 'message',
        payload: {
          message: {
            id: '123',
            content: 'Test message',
            role: 'assistant',
            timestamp: new Date().toISOString()
          },
          conversationId: '456'
        }
      };

      // Manually trigger message handling
      (mockWebsocketService as any).simulateIncomingMessage(message);

      // Check listener was called
      expect(listener).toHaveBeenCalledWith(message);

      // Reset mock
      listener.mockReset();

      // Remove listener
      mockWebsocketService.removeMessageListener(listener);

      // Simulate another message
      (mockWebsocketService as any).simulateIncomingMessage(message);

      // Check listener was not called
      expect(listener).not.toHaveBeenCalled();
    });
  });
});
