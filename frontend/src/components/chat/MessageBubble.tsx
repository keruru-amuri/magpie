'use client';

import React, { useState } from 'react';
import { HandThumbUpIcon as ThumbUpIcon, HandThumbDownIcon as ThumbDownIcon, CheckCircleIcon } from '@heroicons/react/24/outline';
import AgentIndicator from '../orchestrator/AgentIndicator';
import { AgentType } from '../../types/api';

interface Message {
  id: string;
  content: string;
  role: 'user' | 'assistant' | 'system';
  timestamp: Date;
  agentType?: AgentType;
  confidence?: number;
}

interface MessageBubbleProps {
  message: Message;
  showAgentIndicator?: boolean;
  onFeedback?: (messageId: string, feedback: 'positive' | 'negative', comments?: string) => void;
}

export default function MessageBubble({ message, showAgentIndicator = false, onFeedback }: MessageBubbleProps) {
  const [feedbackGiven, setFeedbackGiven] = useState<'positive' | 'negative' | null>(null);
  const [showFeedbackForm, setShowFeedbackForm] = useState(false);
  const [feedbackComment, setFeedbackComment] = useState('');

  const isUser = message.role === 'user';
  const isSystem = message.role === 'system';

  // Format timestamp
  const formattedTime = new Intl.DateTimeFormat('en-US', {
    hour: 'numeric',
    minute: 'numeric',
    hour12: true
  }).format(message.timestamp);

  // Handle feedback
  const handleFeedback = (feedback: 'positive' | 'negative') => {
    if (!onFeedback) return;

    setFeedbackGiven(feedback);

    if (feedback === 'negative') {
      // Show feedback form for negative feedback
      setShowFeedbackForm(true);
    } else {
      // Send positive feedback immediately
      onFeedback(message.id, feedback);
    }
  };

  // Submit feedback with comments
  const submitFeedback = () => {
    if (!onFeedback || !feedbackGiven) return;

    onFeedback(message.id, feedbackGiven, feedbackComment);
    setShowFeedbackForm(false);
  };

  return (
    <div className={`flex ${isUser ? 'justify-end' : 'justify-start'} ${isSystem ? 'justify-center' : ''}`}>
      {/* Avatar for assistant */}
      {!isUser && !isSystem && (
        <div className="h-10 w-10 rounded-full bg-gradient-to-br from-primary-500 to-primary-700 flex items-center justify-center text-white mr-3 flex-shrink-0 shadow-sm">
          <svg
            xmlns="http://www.w3.org/2000/svg"
            className="h-6 w-6"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
          >
            <path d="M22 12H8l4-4H8l-6 6 6 6h4l-4-4h14z" />
          </svg>
        </div>
      )}

      <div className={`flex flex-col max-w-[80%] ${isUser ? 'items-end' : 'items-start'} ${isSystem ? 'items-center max-w-2xl' : ''}`}>
        {/* Agent indicator */}
        {showAgentIndicator && message.agentType && (
          <div className="mb-1">
            <AgentIndicator agentType={message.agentType} showLabel={true} />
          </div>
        )}

        {/* Message bubble */}
        <div
          className={`rounded-lg px-4 py-2 ${
            isUser
              ? 'bg-primary-600 text-white'
              : isSystem
              ? 'bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-300 text-center'
              : 'bg-gray-200 dark:bg-gray-800 text-gray-800 dark:text-gray-200'
          }`}
        >
          <p className="whitespace-pre-wrap">{message.content}</p>
        </div>

        {/* Timestamp and confidence */}
        <div className="flex items-center mt-1 text-xs text-gray-500 dark:text-gray-400 space-x-2">
          <span>{formattedTime}</span>

          {/* Confidence indicator for assistant messages */}
          {!isUser && !isSystem && message.confidence !== undefined && (
            <span className="flex items-center">
              <span className="mr-1">Confidence:</span>
              <span
                className={`px-1.5 py-0.5 rounded-full text-xs ${
                  message.confidence > 0.9
                    ? 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200'
                    : message.confidence > 0.7
                    ? 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200'
                    : 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200'
                }`}
              >
                {Math.round(message.confidence * 100)}%
              </span>
            </span>
          )}
        </div>

        {/* Feedback buttons for assistant messages */}
        {!isUser && !isSystem && (
          <div className="mt-1">
            {feedbackGiven ? (
              <div className="flex items-center text-xs text-green-600 dark:text-green-400">
                <CheckCircleIcon className="h-4 w-4 mr-1" />
                <span>Feedback submitted</span>
              </div>
            ) : (
              <div className="flex space-x-2">
                <button
                  onClick={() => handleFeedback('positive')}
                  className="text-gray-400 hover:text-green-600 dark:hover:text-green-400 transition-colors"
                  aria-label="Helpful"
                  title="Helpful"
                >
                  <ThumbUpIcon className="h-4 w-4" />
                </button>
                <button
                  onClick={() => handleFeedback('negative')}
                  className="text-gray-400 hover:text-red-600 dark:hover:text-red-400 transition-colors"
                  aria-label="Not helpful"
                  title="Not helpful"
                >
                  <ThumbDownIcon className="h-4 w-4" />
                </button>
              </div>
            )}

            {/* Feedback form for negative feedback */}
            {showFeedbackForm && (
              <div className="mt-2 p-2 bg-gray-100 dark:bg-gray-700 rounded-md">
                <textarea
                  value={feedbackComment}
                  onChange={(e) => setFeedbackComment(e.target.value)}
                  placeholder="What could be improved? (optional)"
                  className="w-full p-2 text-sm bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded-md"
                  rows={2}
                />
                <div className="flex justify-end mt-2 space-x-2">
                  <button
                    onClick={() => setShowFeedbackForm(false)}
                    className="px-2 py-1 text-xs text-gray-600 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-600 rounded-md"
                  >
                    Cancel
                  </button>
                  <button
                    onClick={submitFeedback}
                    className="px-2 py-1 text-xs text-white bg-primary-600 hover:bg-primary-700 rounded-md"
                  >
                    Submit
                  </button>
                </div>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Avatar for user */}
      {isUser && (
        <div className="h-10 w-10 rounded-full bg-gray-300 dark:bg-gray-600 flex items-center justify-center text-gray-700 dark:text-gray-300 ml-3 flex-shrink-0">
          <svg
            xmlns="http://www.w3.org/2000/svg"
            className="h-6 w-6"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
          >
            <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2" />
            <circle cx="12" cy="7" r="4" />
          </svg>
        </div>
      )}
    </div>
  );
}
