/**
 * Analytics Service for MAGPIE Platform
 *
 * This service provides analytics and telemetry functionality for tracking
 * usage, performance, and errors.
 */

import { AgentType } from '../types/api';
import { ANALYTICS_CONFIG } from '../config/environment';

// Check if we're in a browser environment
const isBrowser = typeof window !== 'undefined';

// Analytics configuration
const ANALYTICS_ENABLED = ANALYTICS_CONFIG.ENABLED;
const ANALYTICS_ENDPOINT = ANALYTICS_CONFIG.ENDPOINT;

// Event types
export type EventType =
  | 'page_view'
  | 'conversation_start'
  | 'message_sent'
  | 'message_received'
  | 'agent_switch'
  | 'feedback_given'
  | 'error'
  | 'search'
  | 'document_view'
  | 'login'
  | 'logout'
  | 'performance';

// Event data interface
interface EventData {
  eventType: EventType;
  timestamp: number;
  userId?: string;
  conversationId?: string;
  agentType?: AgentType;
  duration?: number;
  metadata?: Record<string, any>;
}

// Queue for batching events
let eventQueue: EventData[] = [];
let isFlushPending = false;
const FLUSH_INTERVAL = 10000; // 10 seconds
const MAX_QUEUE_SIZE = 50;

/**
 * Track an event
 * @param eventType Event type
 * @param metadata Event metadata
 */
export function trackEvent(
  eventType: EventType,
  metadata: Record<string, any> = {}
): void {
  // In development, just log to console instead of sending to server
  if (process.env.NODE_ENV === 'development') {
    console.log('[Analytics]', eventType, metadata);
    return;
  }

  if (!ANALYTICS_ENABLED) {
    return;
  }

  // Create event data
  const eventData: EventData = {
    eventType,
    timestamp: Date.now(),
    userId: metadata.userId,
    conversationId: metadata.conversationId,
    agentType: metadata.agentType,
    duration: metadata.duration,
    metadata: { ...metadata }
  };

  // Add to queue
  eventQueue.push(eventData);

  // Flush queue if it's full
  if (eventQueue.length >= MAX_QUEUE_SIZE) {
    flushEvents();
  } else if (!isFlushPending) {
    // Schedule flush
    isFlushPending = true;
    setTimeout(flushEvents, FLUSH_INTERVAL);
  }
}

/**
 * Flush events to the server
 */
export async function flushEvents(): Promise<void> {
  // In development, don't try to send events
  if (process.env.NODE_ENV === 'development') {
    isFlushPending = false;
    eventQueue = []; // Clear the queue
    return;
  }

  if (!ANALYTICS_ENABLED || eventQueue.length === 0) {
    isFlushPending = false;
    return;
  }

  // Copy queue and clear it
  const events = [...eventQueue];
  eventQueue = [];
  isFlushPending = false;

  try {
    // Send events to server
    await fetch(ANALYTICS_ENDPOINT, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ events }),
      keepalive: true // Ensure request completes even if page is closed
    });
  } catch (error) {
    console.error('Error sending analytics events:', error);

    // Add events back to queue
    eventQueue = [...events, ...eventQueue];

    // Limit queue size
    if (eventQueue.length > MAX_QUEUE_SIZE * 2) {
      eventQueue = eventQueue.slice(-MAX_QUEUE_SIZE);
    }
  }
}

/**
 * Track page view
 * @param path Page path
 * @param title Page title
 */
export function trackPageView(path: string, title: string): void {
  if (!isBrowser) return;

  trackEvent('page_view', {
    path,
    title: title || (isBrowser ? document.title : 'Unknown')
  });
}

/**
 * Track conversation start
 * @param conversationId Conversation ID
 * @param userId User ID
 */
export function trackConversationStart(conversationId: string, userId: string): void {
  trackEvent('conversation_start', { conversationId, userId });
}

/**
 * Track message sent
 * @param conversationId Conversation ID
 * @param userId User ID
 * @param messageId Message ID
 * @param messageLength Message length
 */
export function trackMessageSent(
  conversationId: string,
  userId: string,
  messageId: string,
  messageLength: number
): void {
  trackEvent('message_sent', {
    conversationId,
    userId,
    messageId,
    messageLength
  });
}

/**
 * Track message received
 * @param conversationId Conversation ID
 * @param userId User ID
 * @param messageId Message ID
 * @param agentType Agent type
 * @param messageLength Message length
 * @param responseTime Response time in milliseconds
 */
export function trackMessageReceived(
  conversationId: string,
  userId: string,
  messageId: string,
  agentType: AgentType,
  messageLength: number,
  responseTime: number
): void {
  trackEvent('message_received', {
    conversationId,
    userId,
    messageId,
    agentType,
    messageLength,
    responseTime
  });
}

/**
 * Track agent switch
 * @param conversationId Conversation ID
 * @param userId User ID
 * @param fromAgent Previous agent type
 * @param toAgent New agent type
 * @param reason Reason for switch
 */
export function trackAgentSwitch(
  conversationId: string,
  userId: string,
  fromAgent: AgentType,
  toAgent: AgentType,
  reason: string
): void {
  trackEvent('agent_switch', {
    conversationId,
    userId,
    fromAgent,
    toAgent,
    reason
  });
}

/**
 * Track feedback given
 * @param conversationId Conversation ID
 * @param userId User ID
 * @param messageId Message ID
 * @param agentType Agent type
 * @param feedback Feedback (positive or negative)
 * @param comments Optional comments
 */
export function trackFeedback(
  conversationId: string,
  userId: string,
  messageId: string,
  agentType: AgentType,
  feedback: 'positive' | 'negative',
  comments?: string
): void {
  trackEvent('feedback_given', {
    conversationId,
    userId,
    messageId,
    agentType,
    feedback,
    comments
  });
}

/**
 * Track error
 * @param errorType Error type
 * @param errorMessage Error message
 * @param errorStack Error stack
 * @param metadata Additional metadata
 */
export function trackError(
  errorType: string,
  errorMessage: string,
  errorStack?: string,
  metadata?: Record<string, any>
): void {
  trackEvent('error', {
    errorType,
    errorMessage,
    errorStack,
    ...metadata
  });
}

// Ensure events are flushed before page unload
if (isBrowser) {
  window.addEventListener('beforeunload', () => {
    flushEvents();
  });
}

// Export analytics service
const analyticsService = {
  trackEvent,
  flushEvents,
  trackPageView,
  trackConversationStart,
  trackMessageSent,
  trackMessageReceived,
  trackAgentSwitch,
  trackFeedback,
  trackError
};

export default analyticsService;
