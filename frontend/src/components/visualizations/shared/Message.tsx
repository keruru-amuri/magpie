'use client';

import React, { useState } from 'react';
import { format } from 'date-fns';
import CodeSnippet from './CodeSnippet';
import AgentIndicator from '../../orchestrator/AgentIndicator';

// Define message content types
export type MessageContentType = 'text' | 'code' | 'image' | 'file' | 'chart';

// Define message source
export type MessageSource = 'user' | 'agent';

// Define message content
export interface MessageContent {
  type: MessageContentType;
  content: string;
  language?: string;
  fileName?: string;
  highlightedLines?: number[];
  altText?: string;
  chartData?: any;
}

// Define message props
export interface MessageProps {
  id: string;
  source: MessageSource;
  agentType?: 'documentation' | 'troubleshooting' | 'maintenance' | null;
  timestamp: Date;
  contents: MessageContent[];
  metadata?: Record<string, any>;
  isNew?: boolean;
  className?: string;
}

/**
 * A versatile message component that can display different types of content
 */
export default function Message({
  id,
  source,
  agentType,
  timestamp,
  contents,
  metadata,
  isNew = false,
  className = '',
}: MessageProps) {
  const [expanded, setExpanded] = useState(true);
  const [showMetadata, setShowMetadata] = useState(false);

  // Format timestamp
  const formattedTime = format(timestamp, 'h:mm a');
  const formattedDate = format(timestamp, 'MMM d, yyyy');

  // Determine message style based on source
  const messageStyle = source === 'user'
    ? 'bg-blue-50 dark:bg-blue-900/30 border-blue-200 dark:border-blue-800'
    : 'bg-gray-50 dark:bg-gray-800 border-gray-200 dark:border-gray-700';

  // Render content based on type
  const renderContent = (content: MessageContent, index: number) => {
    switch (content.type) {
      case 'code':
        return (
          <CodeSnippet
            key={`${id}-code-${index}`}
            code={content.content}
            language={content.language}
            fileName={content.fileName}
            highlightedLines={content.highlightedLines}
            className="mt-2"
          />
        );
      case 'image':
        return (
          <div key={`${id}-image-${index}`} className="mt-2">
            <img
              src={content.content}
              alt={content.altText || 'Image'}
              className="max-w-full rounded-md"
            />
            {content.altText && (
              <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                {content.altText}
              </p>
            )}
          </div>
        );
      case 'file':
        return (
          <div key={`${id}-file-${index}`} className="mt-2 p-3 border rounded-md border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-800 flex items-center">
            <svg className="h-6 w-6 text-gray-500 dark:text-gray-400 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
            <a
              href={content.content}
              download={content.fileName}
              className="text-blue-600 dark:text-blue-400 hover:underline"
            >
              {content.fileName || 'Download file'}
            </a>
          </div>
        );
      case 'chart':
        // Chart rendering would be implemented here
        return (
          <div key={`${id}-chart-${index}`} className="mt-2 p-2 border rounded-md border-gray-200 dark:border-gray-700">
            <p className="text-sm text-gray-500 dark:text-gray-400">
              [Chart visualization would be rendered here]
            </p>
          </div>
        );
      case 'text':
      default:
        return (
          <div 
            key={`${id}-text-${index}`} 
            className="prose dark:prose-invert max-w-none"
            dangerouslySetInnerHTML={{ __html: content.content }}
          />
        );
    }
  };

  return (
    <div 
      className={`relative border rounded-lg p-4 mb-4 ${messageStyle} ${isNew ? 'animate-fadeIn' : ''} ${className}`}
      id={`message-${id}`}
    >
      {/* Message header */}
      <div className="flex items-center justify-between mb-2">
        <div className="flex items-center">
          {source === 'agent' && agentType && (
            <AgentIndicator 
              agentType={agentType} 
              showLabel={true} 
              size="sm" 
              className="mr-2"
            />
          )}
          {source === 'user' && (
            <div className="flex items-center text-sm font-medium text-gray-700 dark:text-gray-300">
              <svg className="h-5 w-5 mr-1 text-blue-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
              </svg>
              You
            </div>
          )}
        </div>
        <div className="flex items-center text-xs text-gray-500 dark:text-gray-400">
          <span title={formattedDate}>{formattedTime}</span>
          <button
            onClick={() => setShowMetadata(!showMetadata)}
            className="ml-2 p-1 rounded-full hover:bg-gray-200 dark:hover:bg-gray-700"
            title="Show metadata"
          >
            <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          </button>
          <button
            onClick={() => setExpanded(!expanded)}
            className="ml-1 p-1 rounded-full hover:bg-gray-200 dark:hover:bg-gray-700"
            title={expanded ? 'Collapse' : 'Expand'}
          >
            <svg className={`h-4 w-4 transform ${expanded ? 'rotate-0' : 'rotate-180'}`} fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
            </svg>
          </button>
        </div>
      </div>

      {/* Message content */}
      {expanded && (
        <div className="space-y-2">
          {contents.map((content, index) => renderContent(content, index))}
        </div>
      )}

      {/* Message metadata */}
      {showMetadata && metadata && (
        <div className="mt-3 pt-2 border-t border-gray-200 dark:border-gray-700">
          <h4 className="text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider mb-1">
            Metadata
          </h4>
          <pre className="text-xs bg-gray-100 dark:bg-gray-900 p-2 rounded overflow-x-auto">
            {JSON.stringify(metadata, null, 2)}
          </pre>
        </div>
      )}
    </div>
  );
}
