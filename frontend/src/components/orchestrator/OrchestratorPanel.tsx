'use client';

import React, { useState } from 'react';
import {
  ChevronUpIcon,
  CpuChipIcon,
  ClockIcon,
  AdjustmentsHorizontalIcon,
  ArrowPathIcon,
  DocumentTextIcon,
  KeyIcon
} from '@heroicons/react/24/outline';
import { useOrchestrator } from './OrchestratorContext';
import EnhancedAgentIndicator from './EnhancedAgentIndicator';
import AgentTransition from './AgentTransition';
import MultiAgentCollaboration from './MultiAgentCollaboration';
import ConfidenceIndicator from './ConfidenceIndicator';

interface OrchestratorPanelProps {
  className?: string;
  showSettings?: boolean;
  showContextPreservation?: boolean;
}

export default function OrchestratorPanel({
  className = '',
  showSettings = true,
  showContextPreservation = true
}: OrchestratorPanelProps) {
  const {
    currentAgent,
    previousAgent,
    agentHistory,
    transitions,
    multiAgentState,
    showTransition,
    dismissTransition,
    preservedContext,
    confidenceThresholds,
    setConfidenceThresholds,
    getAgentConfidence
  } = useOrchestrator();

  const [showAgentDetails, setShowAgentDetails] = useState<string | null>(null);
  const [showConfidenceSettings, setShowConfidenceSettings] = useState(false);
  const [showPreservedContext, setShowPreservedContext] = useState(false);

  // Toggle agent details
  const toggleAgentDetails = (agentType: string) => {
    if (showAgentDetails === agentType) {
      setShowAgentDetails(null);
    } else {
      setShowAgentDetails(agentType);
    }
  };

  // Format timestamp
  const formatTimestamp = (date: Date) => {
    return new Intl.DateTimeFormat('en-US', {
      hour: 'numeric',
      minute: 'numeric',
      second: 'numeric',
      hour12: true,
    }).format(date);
  };

  // Format date for context items
  const formatContextDate = (date: Date) => {
    return new Intl.DateTimeFormat('en-US', {
      month: 'short',
      day: 'numeric',
      hour: 'numeric',
      minute: 'numeric',
      hour12: true,
    }).format(date);
  };

  // Get the latest transition
  const latestTransition = transitions.length > 0 ? transitions[transitions.length - 1] : null;

  // Get agent confidence scores
  const documentationConfidence = getAgentConfidence('documentation');
  const troubleshootingConfidence = getAgentConfidence('troubleshooting');
  const maintenanceConfidence = getAgentConfidence('maintenance');

  return (
    <div className={`bg-white dark:bg-gray-900 rounded-lg shadow-md border border-gray-200 dark:border-gray-700 overflow-hidden ${className}`}>
      <div className="p-4 border-b border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-800">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white flex items-center">
          <CpuChipIcon className="h-5 w-5 mr-2 text-primary-500" />
          Orchestrator Status
        </h3>
      </div>

      <div className="p-4">
        {/* Current Agent */}
        {currentAgent && currentAgent.type && (
          <div className="mb-6">
            <h4 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              Current Agent
            </h4>
            <EnhancedAgentIndicator
              agentType={currentAgent.type}
              confidence={currentAgent.confidence}
              isActive={true}
              showDetails={showAgentDetails === currentAgent.type}
              onToggleDetails={() => toggleAgentDetails(currentAgent.type!)}
            />
            <div className="mt-1 text-xs text-gray-500 dark:text-gray-400 flex items-center">
              <ClockIcon className="h-3 w-3 mr-1" />
              Active since {formatTimestamp(currentAgent.timestamp)}
            </div>
          </div>
        )}

        {/* Agent Transition */}
        {showTransition && latestTransition && latestTransition.fromAgent && latestTransition.toAgent && (
          <div className="mb-6">
            <AgentTransition
              fromAgent={latestTransition.fromAgent as any}
              toAgent={latestTransition.toAgent as any}
              reason={latestTransition.reason}
              contextSummary={latestTransition.contextSummary}
              isVisible={showTransition}
              onClose={dismissTransition}
            />
          </div>
        )}

        {/* Agent Confidence Overview */}
        <div className="mb-6">
          <h4 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2 flex items-center">
            <AdjustmentsHorizontalIcon className="h-4 w-4 mr-1" />
            Agent Confidence
          </h4>
          <div className="space-y-3 bg-gray-50 dark:bg-gray-800 p-3 rounded-md">
            <div className="flex items-center justify-between">
              <span className="text-xs text-gray-600 dark:text-gray-400">Documentation</span>
              <ConfidenceIndicator
                confidence={documentationConfidence}
                size="sm"
                label="Documentation Confidence"
              />
            </div>
            <div className="flex items-center justify-between">
              <span className="text-xs text-gray-600 dark:text-gray-400">Troubleshooting</span>
              <ConfidenceIndicator
                confidence={troubleshootingConfidence}
                size="sm"
                label="Troubleshooting Confidence"
              />
            </div>
            <div className="flex items-center justify-between">
              <span className="text-xs text-gray-600 dark:text-gray-400">Maintenance</span>
              <ConfidenceIndicator
                confidence={maintenanceConfidence}
                size="sm"
                label="Maintenance Confidence"
              />
            </div>
          </div>
        </div>

        {/* Multi-Agent Collaboration */}
        {multiAgentState && multiAgentState.isCollaborating && (
          <div className="mb-6">
            <h4 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2 flex items-center">
              <ArrowPathIcon className="h-4 w-4 mr-1" />
              Collaboration
            </h4>
            <MultiAgentCollaboration
              agents={multiAgentState.agents as any[]}
              primaryAgent={multiAgentState.primaryAgent as any}
            />
            {multiAgentState.startTime && (
              <div className="mt-1 text-xs text-gray-500 dark:text-gray-400 flex items-center">
                <ClockIcon className="h-3 w-3 mr-1" />
                Started at {formatTimestamp(multiAgentState.startTime)}
              </div>
            )}
          </div>
        )}

        {/* Preserved Context */}
        {showContextPreservation && preservedContext.length > 0 && (
          <div className="mb-6">
            <div className="border border-gray-200 dark:border-gray-700 rounded-lg overflow-hidden">
              <button
                onClick={() => setShowPreservedContext(!showPreservedContext)}
                className="flex justify-between w-full px-4 py-2 text-sm font-medium text-left text-gray-700 dark:text-gray-300 bg-gray-100 dark:bg-gray-800 hover:bg-gray-200 dark:hover:bg-gray-700 focus:outline-none focus-visible:ring focus-visible:ring-primary-500 focus-visible:ring-opacity-75"
                aria-expanded={showPreservedContext}
              >
                <span className="flex items-center">
                  <KeyIcon className="h-4 w-4 mr-1" />
                  Preserved Context ({preservedContext.length})
                </span>
                <ChevronUpIcon
                  className={`${
                    showPreservedContext ? 'transform rotate-180' : ''
                  } w-5 h-5 text-gray-500`}
                />
              </button>

              {showPreservedContext && (
                <div className="px-4 pt-4 pb-2 text-sm text-gray-500 dark:text-gray-400">
                  <div className="space-y-2 max-h-48 overflow-y-auto">
                    {preservedContext.map((item, index) => (
                      <div key={index} className="p-2 bg-gray-50 dark:bg-gray-800 rounded-md border border-gray-200 dark:border-gray-700">
                        <div className="flex justify-between items-start">
                          <div className="font-medium text-gray-700 dark:text-gray-300 text-xs">{item.key}</div>
                          {item.agentType && (
                            <EnhancedAgentIndicator
                              agentType={item.agentType}
                              isActive={false}
                              className="scale-75"
                            />
                          )}
                        </div>
                        <div className="mt-1 text-xs truncate max-w-xs">
                          {typeof item.value === 'string'
                            ? item.value.length > 50
                              ? `${item.value.substring(0, 50)}...`
                              : item.value
                            : '[Complex data]'}
                        </div>
                        <div className="mt-1 flex justify-between items-center">
                          <span className="text-xs text-gray-500">{formatContextDate(item.timestamp)}</span>
                          <span className={`text-xs px-1.5 py-0.5 rounded-full ${item.isShared ? 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-300' : 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-300'}`}>
                            {item.isShared ? 'Shared' : 'Private'}
                          </span>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </div>
        )}

        {/* Confidence Settings */}
        {showSettings && (
          <div className="mb-6">
            <div className="border border-gray-200 dark:border-gray-700 rounded-lg overflow-hidden">
              <button
                onClick={() => setShowConfidenceSettings(!showConfidenceSettings)}
                className="flex justify-between w-full px-4 py-2 text-sm font-medium text-left text-gray-700 dark:text-gray-300 bg-gray-100 dark:bg-gray-800 hover:bg-gray-200 dark:hover:bg-gray-700 focus:outline-none focus-visible:ring focus-visible:ring-primary-500 focus-visible:ring-opacity-75"
                aria-expanded={showConfidenceSettings}
              >
                <span className="flex items-center">
                  <AdjustmentsHorizontalIcon className="h-4 w-4 mr-1" />
                  Confidence Settings
                </span>
                <ChevronUpIcon
                  className={`${
                    showConfidenceSettings ? 'transform rotate-180' : ''
                  } w-5 h-5 text-gray-500`}
                />
              </button>

              {showConfidenceSettings && (
                <div className="px-4 pt-4 pb-2 text-sm text-gray-500 dark:text-gray-400">
                  <div className="space-y-4">
                    <div>
                      <label className="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1">
                        Minimum Confidence ({Math.round(confidenceThresholds.minimum * 100)}%)
                      </label>
                      <input
                        type="range"
                        min="0"
                        max="1"
                        step="0.05"
                        value={confidenceThresholds.minimum}
                        onChange={(e) => setConfidenceThresholds({ minimum: parseFloat(e.target.value) })}
                        className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer dark:bg-gray-700"
                      />
                      <p className="mt-1 text-xs text-gray-500 dark:text-gray-400">
                        Minimum confidence required to use an agent
                      </p>
                    </div>

                    <div>
                      <label className="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1">
                        Transition Threshold ({Math.round(confidenceThresholds.transition * 100)}%)
                      </label>
                      <input
                        type="range"
                        min="0"
                        max="1"
                        step="0.05"
                        value={confidenceThresholds.transition}
                        onChange={(e) => setConfidenceThresholds({ transition: parseFloat(e.target.value) })}
                        className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer dark:bg-gray-700"
                      />
                      <p className="mt-1 text-xs text-gray-500 dark:text-gray-400">
                        Confidence required to transition between agents
                      </p>
                    </div>

                    <div>
                      <label className="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1">
                        High Confidence ({Math.round(confidenceThresholds.high * 100)}%)
                      </label>
                      <input
                        type="range"
                        min="0"
                        max="1"
                        step="0.05"
                        value={confidenceThresholds.high}
                        onChange={(e) => setConfidenceThresholds({ high: parseFloat(e.target.value) })}
                        className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer dark:bg-gray-700"
                      />
                      <p className="mt-1 text-xs text-gray-500 dark:text-gray-400">
                        Threshold for high confidence responses
                      </p>
                    </div>
                  </div>
                </div>
              )}
            </div>
          </div>
        )}

        {/* Agent History */}
        <div className="mt-4">
          <div className="border border-gray-200 dark:border-gray-700 rounded-lg overflow-hidden">
            <button
              onClick={() => setShowAgentDetails(showAgentDetails === 'history' ? null : 'history')}
              className="flex justify-between w-full px-4 py-2 text-sm font-medium text-left text-gray-700 dark:text-gray-300 bg-gray-100 dark:bg-gray-800 hover:bg-gray-200 dark:hover:bg-gray-700 focus:outline-none focus-visible:ring focus-visible:ring-primary-500 focus-visible:ring-opacity-75"
              aria-expanded={showAgentDetails === 'history'}
            >
              <span className="flex items-center">
                <DocumentTextIcon className="h-4 w-4 mr-1" />
                Agent History ({agentHistory.length})
              </span>
              <ChevronUpIcon
                className={`${
                  showAgentDetails === 'history' ? 'transform rotate-180' : ''
                } w-5 h-5 text-gray-500`}
              />
            </button>

            {showAgentDetails === 'history' && (
              <div className="px-4 pt-4 pb-2 text-sm text-gray-500 dark:text-gray-400">
                {agentHistory.length > 0 ? (
                  <div className="space-y-2 max-h-60 overflow-y-auto">
                    {agentHistory.slice().reverse().map((agent, index) => (
                      agent.type && (
                        <div key={index} className="flex items-center justify-between p-2 bg-gray-50 dark:bg-gray-800 rounded-md">
                          <div className="flex items-center">
                            <EnhancedAgentIndicator
                              agentType={agent.type}
                              confidence={agent.confidence}
                              isActive={false}
                              className="scale-90"
                            />
                          </div>
                          <div className="flex flex-col items-end">
                            <span className="text-xs text-gray-500 dark:text-gray-400">
                              {formatTimestamp(agent.timestamp)}
                            </span>
                            <ConfidenceIndicator
                              confidence={agent.confidence}
                              size="sm"
                              className="mt-1"
                            />
                          </div>
                        </div>
                      )
                    ))}
                  </div>
                ) : (
                  <p>No agent history available.</p>
                )}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
