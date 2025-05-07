'use client';

import React, { useState, useRef, useEffect } from 'react';
import { PaperAirplaneIcon, PaperClipIcon, XMarkIcon } from '@heroicons/react/24/outline';
import MessageBubble from './MessageBubble';
import TypingIndicator from './TypingIndicator';
import AgentIndicator from '../orchestrator/AgentIndicator';
import Button from '../common/Button';
import ContextPanel from '../content-panels/ContextPanel';
import KeyboardShortcutsHelp from '../common/KeyboardShortcutsHelp';
import { useOrchestrator } from '../orchestrator/OrchestratorContext';
import AgentTransition from '../orchestrator/AgentTransition';
import OrchestratorPanel from '../orchestrator/OrchestratorPanel';
import { useConversation } from '../../hooks/useConversation';
import { useApiError } from '../../hooks/useApiError';
import { Message as ApiMessage, AgentType, ApiError } from '../../types/api';

interface Message {
  id: string;
  content: string;
  role: 'user' | 'assistant' | 'system';
  timestamp: Date;
  agentType?: AgentType;
  confidence?: number;
}

interface ChatInterfaceProps {
  initialMessages?: Message[];
  initialConversationId?: string;
  userId?: string;
}

export default function ChatInterface({
  initialMessages = [],
  initialConversationId,
  userId = 'default-user'
}: ChatInterfaceProps) {
  const [inputValue, setInputValue] = useState('');
  const [showContextPanel, setShowContextPanel] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  // Use the orchestrator context
  const {
    currentAgent,
    previousAgent,
    setAgent,
    clearAgent,
    showTransition,
    dismissTransition,
    preserveContext,
    getPreservedContext,
    transitions
  } = useOrchestrator();

  // Use the error handling hook
  const {
    error: apiError,
    handleError,
    getErrorMessage
  } = useApiError({
    onError: (err) => {
      setErrorMessage(err.message);
    }
  });

  // Use the conversation hook
  const {
    messages,
    isTyping,
    isLoadingQuery,
    sendMessage,
    createConversation,
    sendMessageFeedback
  } = useConversation({
    initialConversationId,
    userId,
    onError: (err: ApiError) => {
      console.error('Conversation error:', err);
      handleError(err);
    }
  });

  // Ref to track if we've already tried to create a conversation
  const hasTriedToCreateConversation = useRef(false);

  // Initialize conversation if needed
  useEffect(() => {
    if (!initialConversationId && messages.length === 0 && !hasTriedToCreateConversation.current) {
      // Mark that we've tried to create a conversation
      hasTriedToCreateConversation.current = true;

      // Create a new conversation
      createConversation('New Conversation').catch((err: ApiError) => {
        console.error('Error creating conversation:', err);
        handleError(err);
      });
    }
  }, [initialConversationId, messages.length, createConversation, handleError]);

  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);

  // Track if this is the initial render
  const isInitialRender = useRef(true);

  // Track if the user has scrolled away from the chat
  const userHasScrolled = useRef(false);

  // Track the main page scroll position
  const mainScrollPosition = useRef(0);

  // Auto-scroll to bottom when messages change, but only if not initial render
  useEffect(() => {
    // Skip scrolling on initial render
    if (isInitialRender.current) {
      isInitialRender.current = false;
      return;
    }

    // Store current main page scroll position
    mainScrollPosition.current = window.scrollY;

    // Only scroll the messages container if there are messages
    if (messages.length > 0) {
      // Get the messages container
      const messagesContainer = document.querySelector('.messages-container');

      if (messagesContainer) {
        // Only auto-scroll the messages container, not the whole page
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth', block: 'end' });

        // Restore the main page scroll position
        setTimeout(() => {
          window.scrollTo(0, mainScrollPosition.current);
        }, 0);
      }
    }
  }, [messages]);

  // Disable auto-focus and prevent scrolling on load
  useEffect(() => {
    // Intentionally not focusing the input on load
    // This prevents the page from scrolling to the input

    // Prevent any scrolling in the messages container on initial load
    const messagesContainer = document.querySelector('.messages-container');
    if (messagesContainer) {
      messagesContainer.scrollTop = 0;
    }

    // Also prevent the main window from scrolling
    const preventScroll = () => {
      window.scrollTo(0, 0);
    };

    // Apply multiple times to catch any layout shifts
    const intervals = [10, 50, 100, 200, 500];
    const timers = intervals.map(delay => setTimeout(preventScroll, delay));

    return () => {
      // Clean up all timers
      timers.forEach(timer => clearTimeout(timer));
    };
  }, []);

  // Add keyboard shortcuts
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      // Ctrl+/ or Cmd+/ to focus the chat input
      if ((e.ctrlKey || e.metaKey) && e.key === '/') {
        e.preventDefault();
        inputRef.current?.focus();
      }

      // Escape to close context panel
      if (e.key === 'Escape' && showContextPanel) {
        e.preventDefault();
        setShowContextPanel(false);
      }

      // Ctrl+. or Cmd+. to toggle context panel
      if ((e.ctrlKey || e.metaKey) && e.key === '.' && currentAgent) {
        e.preventDefault();
        setShowContextPanel(!showContextPanel);
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [showContextPanel, currentAgent]);

  // Auto-resize textarea without causing page scroll
  const handleTextareaChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    // Store current scroll position
    const scrollPosition = window.scrollY;

    // Update input value and resize
    setInputValue(e.target.value);
    e.target.style.height = 'auto';
    e.target.style.height = `${Math.min(e.target.scrollHeight, 200)}px`;

    // Restore scroll position after the browser might have scrolled
    window.scrollTo(0, scrollPosition);
  };

  const handleSendMessage = async () => {
    if (!inputValue.trim()) return;

    // Store current scroll position
    const scrollPosition = window.scrollY;

    // Reset textarea height
    if (inputRef.current) {
      inputRef.current.style.height = 'auto';
    }

    // Clear error message
    setErrorMessage(null);

    // Store the message text and clear input
    const messageText = inputValue;
    setInputValue('');

    // Restore scroll position after UI updates
    setTimeout(() => {
      window.scrollTo(0, scrollPosition);
    }, 0);

    try {
      // Preserve the user's query in context
      preserveContext('lastUserQuery', messageText, true);

      // Send message using the conversation hook
      const response = await sendMessage(messageText);

      // If we got a response with agent type, preserve it in context
      if (response && response.agentType) {
        // Preserve the agent type and confidence
        preserveContext('lastAgentType', response.agentType, true);
        if (response.confidence) {
          preserveContext('lastAgentConfidence', response.confidence, true);
        }

        // Preserve any metadata from the response
        if (response.metadata) {
          preserveContext('lastResponseMetadata', response.metadata, true);
        }
      }

      // Show context panel if not already visible
      if (currentAgent && !showContextPanel) {
        setShowContextPanel(true);
      }

      // Restore scroll position again after async operations
      window.scrollTo(0, scrollPosition);
    } catch (error) {
      console.error('Error sending message:', error);

      // Set error message
      if (error instanceof Error) {
        setErrorMessage(error.message);
      } else {
        setErrorMessage('An unknown error occurred. Please try again.');
      }

      // Restore scroll position after error handling
      window.scrollTo(0, scrollPosition);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();

      // Store current scroll position
      const scrollPosition = window.scrollY;

      // Send message
      handleSendMessage();

      // Restore scroll position after a short delay
      // This ensures the browser doesn't scroll after the message is sent
      setTimeout(() => {
        window.scrollTo(0, scrollPosition);
      }, 0);
    }
  };

  // Toggle context panel
  const toggleContextPanel = () => {
    setShowContextPanel(!showContextPanel);
  };

  return (
    <div className="flex h-full" role="main" aria-label="Chat with MAGPIE Assistant">
      {/* Main Chat Interface */}
      <div className={`flex flex-col ${showContextPanel ? 'lg:w-2/3' : 'w-full'} h-full bg-white dark:bg-gray-800 rounded-lg shadow-md border border-gray-200 dark:border-gray-700 overflow-hidden transition-all duration-300`}>
        {/* Chat Header */}
        <div className="p-4 border-b border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-900">
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-semibold text-gray-900 dark:text-white" id="chat-heading">MAGPIE Assistant</h2>
            <div className="flex items-center space-x-2">
              {currentAgent && currentAgent.type && (
                <button
                  onClick={toggleContextPanel}
                  className="text-xs px-2 py-1 rounded-md bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-300 hover:bg-gray-300 dark:hover:bg-gray-600"
                  aria-expanded={showContextPanel}
                  aria-controls="context-panel"
                  aria-label={showContextPanel ? 'Hide context panel' : 'Show context panel'}
                >
                  {showContextPanel ? 'Hide Context' : 'Show Context'}
                </button>
              )}
              {currentAgent && currentAgent.type && <AgentIndicator agentType={currentAgent.type} showLabel={true} />}
            </div>
          </div>
        </div>

        {/* Agent Transition Notification */}
        {showTransition && currentAgent?.type && previousAgent?.type && (
          <div className="px-4 pt-2">
            <AgentTransition
              fromAgent={previousAgent.type}
              toAgent={currentAgent.type}
              isVisible={showTransition}
              onClose={dismissTransition}
              confidenceScore={currentAgent.confidence}
              preservedContext={transitions.length > 0
                ? transitions[transitions.length - 1].preservedContext || []
                : []}
            />
          </div>
        )}

        {/* Messages Container */}
        <div
          className="flex-grow overflow-y-auto p-4 space-y-4 messages-container"
          role="log"
          aria-live="polite"
          aria-label="Conversation messages"
        >
          {/* Error Message */}
          {errorMessage && (
            <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded relative" role="alert">
              <strong className="font-bold">Error: </strong>
              <span className="block sm:inline">{errorMessage}</span>
            </div>
          )}

          {/* Conversation Messages */}
          {messages.map((apiMessage) => {
            // Convert API message to local format
            const message: Message = {
              id: apiMessage.id,
              content: apiMessage.content,
              role: apiMessage.role,
              timestamp: new Date(apiMessage.timestamp),
              agentType: apiMessage.agentType,
              confidence: apiMessage.confidence
            };

            return (
              <MessageBubble
                key={message.id}
                message={message}
                showAgentIndicator={message.role === 'assistant' && !!message.agentType}
                onFeedback={sendMessageFeedback}
              />
            );
          })}

          {/* Typing Indicator */}
          {isTyping && <TypingIndicator />}

          {/* Auto-scroll anchor */}
          <div ref={messagesEndRef} />
        </div>

        {/* Input Area */}
        <div className="border-t border-gray-200 dark:border-gray-700 p-4 bg-gray-50 dark:bg-gray-900">
          <div className="flex items-end space-x-2">
            <button className="p-2 rounded-full text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-800">
              <PaperClipIcon className="h-5 w-5" />
            </button>
            <KeyboardShortcutsHelp />
            <div className="flex-grow relative">
              <textarea
                ref={inputRef}
                value={inputValue}
                onChange={handleTextareaChange}
                onKeyDown={handleKeyDown}
                placeholder="Ask me anything about aircraft maintenance... (Ctrl+/ to focus)"
                className="w-full border border-gray-300 dark:border-gray-600 rounded-lg py-2 px-3 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent dark:bg-gray-800 dark:text-white resize-none min-h-[40px] max-h-[200px]"
                rows={1}
              />
            </div>
            <Button
              onClick={handleSendMessage}
              disabled={!inputValue.trim() || isTyping}
              className="rounded-full p-2 h-10 w-10 flex items-center justify-center"
              aria-label="Send message"
            >
              <PaperAirplaneIcon className="h-5 w-5" />
            </Button>
          </div>
          <div className="mt-2 text-xs text-gray-500 dark:text-gray-400 text-right">
            Press <kbd className="px-1 py-0.5 text-xs font-semibold text-gray-800 bg-gray-100 border border-gray-200 rounded dark:bg-gray-700 dark:text-gray-200 dark:border-gray-600">Enter</kbd> to send, <kbd className="px-1 py-0.5 text-xs font-semibold text-gray-800 bg-gray-100 border border-gray-200 rounded dark:bg-gray-700 dark:text-gray-200 dark:border-gray-600">Shift+Enter</kbd> for new line
          </div>
        </div>
      </div>

      {/* Context Panel (conditionally rendered) */}
      {showContextPanel && (
        <div
          className="hidden lg:flex lg:flex-col lg:w-1/3 ml-4 h-full relative"
          id="context-panel"
          role="complementary"
          aria-label={`${currentAgent?.type || 'context'} panel`}
        >
          <button
            onClick={toggleContextPanel}
            className="absolute top-2 right-2 z-10 p-1 rounded-full bg-gray-200 dark:bg-gray-700 text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-300"
            aria-label="Close context panel"
          >
            <XMarkIcon className="h-5 w-5" />
          </button>

          {/* Orchestrator Panel */}
          <div className="mb-4">
            <OrchestratorPanel />
          </div>

          {/* Agent-specific Context Panel */}
          <div className="flex-grow">
            <ContextPanel
              agentType={currentAgent?.type || null}
              isVisible={showContextPanel}
              className="h-full"
            />
          </div>
        </div>
      )}
    </div>
  );
}
