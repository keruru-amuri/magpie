'use client';

import React, { createContext, useContext, useState, useEffect, useCallback, ReactNode } from 'react';

// Agent types supported by the platform
type AgentType = 'documentation' | 'troubleshooting' | 'maintenance' | null;

// Context type for storing preserved context between agent transitions
interface ContextData {
  key: string;
  value: any;
  agentType: AgentType;
  timestamp: Date;
  isShared: boolean; // Whether this context is shared between agents
}

// Agent state representation
interface AgentState {
  type: AgentType;
  confidence: number;
  timestamp: Date;
  metadata?: Record<string, any>; // Additional metadata about the agent state
}

// Transition between agents
interface AgentTransition {
  fromAgent: AgentType;
  toAgent: AgentType;
  reason: string;
  contextSummary?: string;
  timestamp: Date;
  confidenceScore: number; // How confident the orchestrator is about this transition
  preservedContext?: string[]; // Keys of context data preserved during transition
}

// State for multi-agent collaboration
interface MultiAgentState {
  isCollaborating: boolean;
  agents: {
    type: AgentType;
    role: string;
    contribution?: string;
    confidence?: number;
  }[];
  primaryAgent: AgentType;
  startTime: Date;
  endTime?: Date;
}

// Confidence threshold configuration
interface ConfidenceThresholds {
  minimum: number; // Minimum confidence to use an agent
  high: number; // Threshold for high confidence
  transition: number; // Minimum confidence to transition between agents
}

// Orchestrator context type definition
interface OrchestratorContextType {
  // Agent state
  currentAgent: AgentState | null;
  previousAgent: AgentState | null;
  agentHistory: AgentState[];
  transitions: AgentTransition[];

  // Multi-agent collaboration
  multiAgentState: MultiAgentState | null;

  // UI state
  showTransition: boolean;

  // Context preservation
  preservedContext: ContextData[];

  // Configuration
  confidenceThresholds: ConfidenceThresholds;

  // Methods
  setAgent: (type: AgentType, confidence?: number, metadata?: Record<string, any>) => void;
  clearAgent: () => void;
  startMultiAgentCollaboration: (agents: MultiAgentState['agents'], primaryAgent: AgentType) => void;
  endMultiAgentCollaboration: () => void;
  dismissTransition: () => void;
  setConfidenceThresholds: (thresholds: Partial<ConfidenceThresholds>) => void;
  preserveContext: (key: string, value: any, isShared?: boolean) => void;
  getPreservedContext: (key: string) => any;
  clearPreservedContext: (keys?: string[]) => void;
  getAgentConfidence: (agentType: AgentType) => number;
}

const OrchestratorContext = createContext<OrchestratorContextType | undefined>(undefined);

export function OrchestratorProvider({ children }: { children: ReactNode }) {
  // Agent state
  const [currentAgent, setCurrentAgent] = useState<AgentState | null>(null);
  const [previousAgent, setPreviousAgent] = useState<AgentState | null>(null);
  const [agentHistory, setAgentHistory] = useState<AgentState[]>([]);
  const [transitions, setTransitions] = useState<AgentTransition[]>([]);

  // Multi-agent collaboration state
  const [multiAgentState, setMultiAgentState] = useState<MultiAgentState | null>(null);

  // UI state
  const [showTransition, setShowTransition] = useState(false);

  // Context preservation
  const [preservedContext, setPreservedContext] = useState<ContextData[]>([]);

  // Configuration
  const [confidenceThresholds, setConfidenceThresholds] = useState<ConfidenceThresholds>({
    minimum: 0.6,  // Minimum confidence to use an agent
    high: 0.85,    // Threshold for high confidence
    transition: 0.75, // Minimum confidence to transition between agents
  });

  // Update confidence thresholds
  const updateConfidenceThresholds = useCallback((thresholds: Partial<ConfidenceThresholds>) => {
    setConfidenceThresholds(prev => ({
      ...prev,
      ...thresholds
    }));
  }, []);

  // Preserve context data for agent transitions
  const preserveContext = useCallback((key: string, value: any, isShared = true) => {
    setPreservedContext(prev => {
      // Remove any existing context with the same key
      const filtered = prev.filter(item => item.key !== key);

      // Add the new context
      return [...filtered, {
        key,
        value,
        agentType: currentAgent?.type || null,
        timestamp: new Date(),
        isShared
      }];
    });
  }, [currentAgent?.type]);

  // Get preserved context by key
  const getPreservedContext = useCallback((key: string) => {
    const contextItem = preservedContext.find(item => item.key === key);
    return contextItem?.value || null;
  }, [preservedContext]);

  // Clear preserved context
  const clearPreservedContext = useCallback((keys?: string[]) => {
    if (!keys || keys.length === 0) {
      setPreservedContext([]);
    } else {
      setPreservedContext(prev => prev.filter(item => !keys.includes(item.key)));
    }
  }, []);

  // Get confidence score for a specific agent type
  const getAgentConfidence = useCallback((agentType: AgentType) => {
    if (!agentType) return 0;

    // If it's the current agent, return its confidence
    if (currentAgent?.type === agentType) {
      return currentAgent.confidence;
    }

    // If it's in multi-agent collaboration, find its confidence
    if (multiAgentState?.isCollaborating) {
      const agent = multiAgentState.agents.find(a => a.type === agentType);
      return agent?.confidence || 0;
    }

    // Otherwise, return 0
    return 0;
  }, [currentAgent, multiAgentState]);

  // Set the current agent with enhanced transition logic
  const setAgent = useCallback((type: AgentType, confidence = 0.8, metadata?: Record<string, any>) => {
    if (!type) {
      clearAgent();
      return;
    }

    // If confidence is below minimum threshold, don't change agent
    if (confidence < confidenceThresholds.minimum) {
      console.warn(`Agent confidence too low (${confidence}), minimum required: ${confidenceThresholds.minimum}`);
      return;
    }

    // If there's a current agent and it's different from the new one, create a transition
    if (currentAgent && currentAgent.type !== type) {
      // Only transition if confidence is above transition threshold
      if (confidence >= confidenceThresholds.transition) {
        setPreviousAgent(currentAgent);

        // Get preserved context keys that will be carried over
        const preservedKeys = preservedContext
          .filter(item => item.isShared)
          .map(item => item.key);

        const transition: AgentTransition = {
          fromAgent: currentAgent.type,
          toAgent: type,
          reason: 'Your query requires specialized knowledge from a different agent.',
          contextSummary: 'Previous context has been preserved for continuity.',
          timestamp: new Date(),
          confidenceScore: confidence,
          preservedContext: preservedKeys
        };

        setTransitions(prev => [...prev, transition]);
        setShowTransition(true);

        // Auto-dismiss transition after 5 seconds
        setTimeout(() => {
          setShowTransition(false);
        }, 5000);
      } else {
        console.warn(`Agent transition confidence too low (${confidence}), minimum required: ${confidenceThresholds.transition}`);
        return;
      }
    }

    const newAgentState: AgentState = {
      type,
      confidence,
      timestamp: new Date(),
      metadata
    };

    setCurrentAgent(newAgentState);
    setAgentHistory(prev => [...prev, newAgentState]);
  }, [currentAgent, confidenceThresholds, preservedContext]);

  // Clear the current agent
  const clearAgent = useCallback(() => {
    setPreviousAgent(currentAgent);
    setCurrentAgent(null);
  }, [currentAgent]);

  // Start multi-agent collaboration with enhanced tracking
  const startMultiAgentCollaboration = useCallback((
    agents: MultiAgentState['agents'],
    primaryAgent: AgentType
  ) => {
    setMultiAgentState({
      isCollaborating: true,
      agents,
      primaryAgent,
      startTime: new Date()
    });

    // Set the primary agent as the current agent
    if (primaryAgent) {
      // Find the primary agent's confidence if available
      const primaryAgentData = agents.find(a => a.type === primaryAgent);
      const confidence = primaryAgentData?.confidence || 0.8;

      setAgent(primaryAgent, confidence);
    }
  }, [setAgent]);

  // End multi-agent collaboration with timestamp
  const endMultiAgentCollaboration = useCallback(() => {
    setMultiAgentState(prev =>
      prev ? { ...prev, isCollaborating: false, endTime: new Date() } : null
    );
  }, []);

  // Dismiss the transition notification
  const dismissTransition = useCallback(() => {
    setShowTransition(false);
  }, []);

  // Create context value
  const value = {
    // State
    currentAgent,
    previousAgent,
    agentHistory,
    transitions,
    multiAgentState,
    showTransition,
    preservedContext,
    confidenceThresholds,

    // Methods
    setAgent,
    clearAgent,
    startMultiAgentCollaboration,
    endMultiAgentCollaboration,
    dismissTransition,
    setConfidenceThresholds: updateConfidenceThresholds,
    preserveContext,
    getPreservedContext,
    clearPreservedContext,
    getAgentConfidence
  };

  return (
    <OrchestratorContext.Provider value={value}>
      {children}
    </OrchestratorContext.Provider>
  );
}

export function useOrchestrator() {
  const context = useContext(OrchestratorContext);
  if (context === undefined) {
    throw new Error('useOrchestrator must be used within an OrchestratorProvider');
  }
  return context;
}

export default OrchestratorContext;
