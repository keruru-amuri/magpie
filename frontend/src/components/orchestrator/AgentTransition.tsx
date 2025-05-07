'use client';

import React, { useEffect, useState } from 'react';
import { ArrowRightIcon, InformationCircleIcon, KeyIcon } from '@heroicons/react/24/outline';
import AgentIndicator from './AgentIndicator';
import ConfidenceIndicator from './ConfidenceIndicator';

interface AgentTransitionProps {
  fromAgent: 'documentation' | 'troubleshooting' | 'maintenance';
  toAgent: 'documentation' | 'troubleshooting' | 'maintenance';
  reason?: string;
  contextSummary?: string;
  preservedContext?: string[];
  confidenceScore?: number;
  isVisible?: boolean;
  onClose?: () => void;
  className?: string;
}

export default function AgentTransition({
  fromAgent,
  toAgent,
  reason = 'Your query requires specialized knowledge from a different agent.',
  contextSummary,
  preservedContext = [],
  confidenceScore = 0.8,
  isVisible = true,
  onClose,
  className = '',
}: AgentTransitionProps) {
  const [isShowing, setIsShowing] = useState(false);

  useEffect(() => {
    if (isVisible) {
      setIsShowing(true);
    } else {
      const timer = setTimeout(() => {
        setIsShowing(false);
      }, 200);
      return () => clearTimeout(timer);
    }
  }, [isVisible]);

  if (!isVisible && !isShowing) {
    return null;
  }

  return (
    <div
      className={`bg-gray-50 dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-4 ${className} transition-opacity duration-300 ${isVisible ? 'opacity-100' : 'opacity-0'}`}
    >
        <div className="flex items-center justify-between mb-3">
          <h3 className="text-sm font-medium text-gray-900 dark:text-white flex items-center">
            <InformationCircleIcon className="h-5 w-5 mr-1.5 text-primary-500" />
            Agent Transition
          </h3>
          {onClose && (
            <button
              onClick={onClose}
              className="text-gray-400 hover:text-gray-500 dark:hover:text-gray-300"
              aria-label="Close transition notification"
            >
              <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          )}
        </div>

        <div className="flex items-center justify-center space-x-3 mb-3">
          <div className="flex flex-col items-center">
            <AgentIndicator agentType={fromAgent} showLabel={true} size="md" />
          </div>
          <div className="flex flex-col items-center">
            <ArrowRightIcon className="h-5 w-5 text-gray-400" />
            <div className="mt-1">
              <ConfidenceIndicator
                confidence={confidenceScore}
                size="sm"
                showPercentage={true}
                label="Transition Confidence"
              />
            </div>
          </div>
          <div className="flex flex-col items-center">
            <AgentIndicator agentType={toAgent} showLabel={true} size="md" />
          </div>
        </div>

        <p className="text-sm text-gray-600 dark:text-gray-400 mb-3">
          {reason}
        </p>

        {(contextSummary || preservedContext.length > 0) && (
          <div className="mt-3 bg-gray-100 dark:bg-gray-700 p-3 rounded-md">
            <h4 className="text-xs font-medium text-gray-700 dark:text-gray-300 uppercase tracking-wider mb-1 flex items-center">
              <KeyIcon className="h-3 w-3 mr-1" />
              Context Preserved
            </h4>

            {contextSummary && (
              <p className="text-xs text-gray-600 dark:text-gray-400 mb-2">
                {contextSummary}
              </p>
            )}

            {preservedContext.length > 0 && (
              <div className="mt-2">
                <div className="flex flex-wrap gap-1">
                  {preservedContext.map((key, index) => (
                    <span
                      key={index}
                      className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-300"
                    >
                      {key}
                    </span>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}
      </div>
  );
}
