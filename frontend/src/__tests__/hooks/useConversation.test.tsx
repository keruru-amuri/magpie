/**
 * useConversation Hook Tests
 * 
 * This file contains tests for the useConversation hook.
 */

import { renderHook, act } from '@testing-library/react-hooks';
import { useConversation } from '../../hooks/useConversation';
import { conversationService, orchestratorService } from '../../services';

// Mock services
jest.mock('../../services', () => ({
  conversationService: {
    getAll: jest.fn(),
    get: jest.fn(),
    create: jest.fn(),
    update: jest.fn(),
    delete: jest.fn(),
    sendMessage: jest.fn(),
    generateTitle: jest.fn()
  },
  orchestratorService: {
    connectWebSocket: jest.fn(),
    joinConversation: jest.fn(),
    leaveConversation: jest.fn(),
    sendChatMessage: jest.fn(),
    sendTypingIndicator: jest.fn(),
    sendMessageFeedback: jest.fn(),
    addMessageListener: jest.fn(() => jest.fn()),
    addConnectionListener: jest.fn(() => jest.fn())
  },
  analyticsService: {
    trackEvent: jest.fn()
  }
}));

// Mock useNotifications hook
jest.mock('../../hooks/useNotifications', () => ({
  useNotifications: () => ({
    showSuccess: jest.fn(),
    showError: jest.fn(),
    showInfo: jest.fn(),
    showWarning: jest.fn()
  })
}));

describe('useConversation Hook', () => {
  // Reset mocks before each test
  beforeEach(() => {
    jest.clearAllMocks();
  });

  test('should connect to WebSocket on mount', () => {
    // Render hook
    const { result } = renderHook(() => useConversation({ userId: 'user123' }));

    // Check WebSocket connection was established
    expect(orchestratorService.connectWebSocket).toHaveBeenCalledWith('user123', undefined);
    expect(orchestratorService.addMessageListener).toHaveBeenCalled();
    expect(orchestratorService.addConnectionListener).toHaveBeenCalled();
  });

  test('should fetch conversations', async () => {
    // Mock getAll to return conversations
    const mockConversations = [
      {
        id: 'conv1',
        title: 'Conversation 1',
        messages: [],
        createdAt: new Date().toISOString(),
        updatedAt: new Date().toISOString()
      },
      {
        id: 'conv2',
        title: 'Conversation 2',
        messages: [],
        createdAt: new Date().toISOString(),
        updatedAt: new Date().toISOString()
      }
    ];
    (conversationService.getAll as jest.Mock).mockResolvedValue(mockConversations);

    // Render hook
    const { result, waitForNextUpdate } = renderHook(() => useConversation({ userId: 'user123' }));

    // Fetch conversations
    let fetchPromise;
    act(() => {
      fetchPromise = result.current.fetchConversations();
    });

    // Wait for update
    await waitForNextUpdate();

    // Check conversations were fetched
    await expect(fetchPromise).resolves.toEqual(mockConversations);
    expect(result.current.conversations).toEqual(mockConversations);
    expect(conversationService.getAll).toHaveBeenCalled();
  });

  test('should load conversation', async () => {
    // Mock get to return conversation
    const mockConversation = {
      id: 'conv1',
      title: 'Conversation 1',
      messages: [
        {
          id: 'msg1',
          content: 'Hello',
          role: 'user',
          timestamp: new Date().toISOString()
        }
      ],
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString()
    };
    (conversationService.get as jest.Mock).mockResolvedValue(mockConversation);

    // Render hook
    const { result, waitForNextUpdate } = renderHook(() => useConversation({ userId: 'user123' }));

    // Load conversation
    let loadPromise;
    act(() => {
      loadPromise = result.current.loadConversation('conv1');
    });

    // Wait for update
    await waitForNextUpdate();

    // Check conversation was loaded
    await expect(loadPromise).resolves.toEqual(mockConversation);
    expect(result.current.currentConversation).toEqual(mockConversation);
    expect(result.current.messages).toEqual(mockConversation.messages);
    expect(result.current.conversationId).toBe('conv1');
    expect(conversationService.get).toHaveBeenCalledWith('conv1');
    expect(orchestratorService.joinConversation).toHaveBeenCalledWith('conv1');
  });

  test('should create conversation', async () => {
    // Mock create to return conversation
    const mockConversation = {
      id: 'new-conv',
      title: 'New Conversation',
      messages: [],
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString()
    };
    (conversationService.create as jest.Mock).mockResolvedValue(mockConversation);

    // Render hook
    const { result, waitForNextUpdate } = renderHook(() => useConversation({ userId: 'user123' }));

    // Create conversation
    let createPromise;
    act(() => {
      createPromise = result.current.createConversation('New Conversation');
    });

    // Wait for update
    await waitForNextUpdate();

    // Check conversation was created
    await expect(createPromise).resolves.toEqual(mockConversation);
    expect(result.current.currentConversation).toEqual(mockConversation);
    expect(result.current.conversationId).toBe('new-conv');
    expect(conversationService.create).toHaveBeenCalledWith('New Conversation');
    expect(orchestratorService.joinConversation).toHaveBeenCalledWith('new-conv');
  });

  test('should send message', async () => {
    // Mock services
    (conversationService.generateTitle as jest.Mock).mockReturnValue('Generated Title');
    (conversationService.create as jest.Mock).mockResolvedValue({
      id: 'new-conv',
      title: 'Generated Title',
      messages: [],
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString()
    });

    // Render hook
    const { result, waitForNextUpdate } = renderHook(() => useConversation({ userId: 'user123' }));

    // Send message
    let sendPromise;
    act(() => {
      sendPromise = result.current.sendMessage('Hello');
    });

    // Wait for update
    await waitForNextUpdate();

    // Check message was sent
    const userMessage = await sendPromise;
    expect(userMessage).toEqual({
      id: expect.any(String),
      content: 'Hello',
      role: 'user',
      timestamp: expect.any(String)
    });
    expect(result.current.messages).toContainEqual(userMessage);
    expect(orchestratorService.sendTypingIndicator).toHaveBeenCalledWith(true);
    expect(orchestratorService.sendTypingIndicator).toHaveBeenCalledWith(false);
  });

  test('should delete conversation', async () => {
    // Mock delete to resolve
    (conversationService.delete as jest.Mock).mockResolvedValue(undefined);

    // Mock current conversation
    const mockConversation = {
      id: 'conv1',
      title: 'Conversation 1',
      messages: [],
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString()
    };

    // Render hook with initial conversation
    const { result } = renderHook(() => useConversation({ userId: 'user123' }));

    // Set current conversation
    act(() => {
      (result.current as any).setCurrentConversation(mockConversation);
      (result.current as any).setConversationId('conv1');
      (result.current as any).setConversations([mockConversation]);
    });

    // Delete conversation
    await act(async () => {
      await result.current.deleteConversation('conv1');
    });

    // Check conversation was deleted
    expect(conversationService.delete).toHaveBeenCalledWith('conv1');
    expect(result.current.currentConversation).toBeNull();
    expect(result.current.messages).toEqual([]);
    expect(result.current.conversationId).toBeNull();
    expect(result.current.conversations).toEqual([]);
  });
});
