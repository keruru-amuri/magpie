/**
 * Custom hook for analytics tracking
 */

import { useCallback, useEffect } from 'react';
import { usePathname, useSearchParams } from 'next/navigation';
import analyticsService, { EventType } from '../services/analyticsService';
import { AgentType } from '../types/api';

interface UseAnalyticsOptions {
  userId?: string;
  conversationId?: string;
}

export function useAnalytics(options: UseAnalyticsOptions = {}) {
  const pathname = usePathname();
  const searchParams = useSearchParams();
  const { userId, conversationId } = options;

  // Track page views
  useEffect(() => {
    // Track initial page view
    analyticsService.trackPageView(
      pathname,
      document.title
    );

    // Note: In App Router, we don't have router.events
    // Instead, we track page views whenever pathname or searchParams change
  }, [pathname, searchParams]);

  // Track conversation start
  const trackConversationStart = useCallback((
    convId: string,
    uid: string = userId || 'anonymous'
  ) => {
    analyticsService.trackConversationStart(convId, uid);
  }, [userId]);

  // Track message sent
  const trackMessageSent = useCallback((
    messageId: string,
    messageContent: string,
    convId: string = conversationId || 'unknown',
    uid: string = userId || 'anonymous'
  ) => {
    analyticsService.trackMessageSent(
      convId,
      uid,
      messageId,
      messageContent.length
    );
  }, [userId, conversationId]);

  // Track message received
  const trackMessageReceived = useCallback((
    messageId: string,
    messageContent: string,
    agentType: AgentType,
    responseTime: number,
    convId: string = conversationId || 'unknown',
    uid: string = userId || 'anonymous'
  ) => {
    analyticsService.trackMessageReceived(
      convId,
      uid,
      messageId,
      agentType,
      messageContent.length,
      responseTime
    );
  }, [userId, conversationId]);

  // Track agent switch
  const trackAgentSwitch = useCallback((
    fromAgent: AgentType,
    toAgent: AgentType,
    reason: string,
    convId: string = conversationId || 'unknown',
    uid: string = userId || 'anonymous'
  ) => {
    analyticsService.trackAgentSwitch(
      convId,
      uid,
      fromAgent,
      toAgent,
      reason
    );
  }, [userId, conversationId]);

  // Track feedback
  const trackFeedback = useCallback((
    messageId: string,
    agentType: AgentType,
    feedback: 'positive' | 'negative',
    comments?: string,
    convId: string = conversationId || 'unknown',
    uid: string = userId || 'anonymous'
  ) => {
    analyticsService.trackFeedback(
      convId,
      uid,
      messageId,
      agentType,
      feedback,
      comments
    );
  }, [userId, conversationId]);

  // Track error
  const trackError = useCallback((
    errorType: string,
    errorMessage: string,
    errorStack?: string,
    metadata?: Record<string, any>
  ) => {
    analyticsService.trackError(
      errorType,
      errorMessage,
      errorStack,
      {
        userId,
        conversationId,
        ...metadata
      }
    );
  }, [userId, conversationId]);

  // Track custom event
  const trackEvent = useCallback((
    eventType: EventType,
    metadata: Record<string, any> = {}
  ) => {
    analyticsService.trackEvent(
      eventType,
      {
        userId,
        conversationId,
        ...metadata
      }
    );
  }, [userId, conversationId]);

  return {
    trackConversationStart,
    trackMessageSent,
    trackMessageReceived,
    trackAgentSwitch,
    trackFeedback,
    trackError,
    trackEvent
  };
}
