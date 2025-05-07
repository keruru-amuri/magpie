import React, { createContext, useState, useContext } from 'react';
import api from '../services/api';

interface Agent {
  id: string;
  name: string;
  description: string;
  type: 'documentation' | 'troubleshooting' | 'maintenance';
  capabilities: string[];
}

interface Message {
  id: string;
  content: string;
  role: 'user' | 'assistant';
  timestamp: string;
  confidence?: number;
}

interface Conversation {
  id: string;
  agentId: string;
  title: string;
  messages: Message[];
  createdAt: string;
  updatedAt: string;
}

interface AgentContextType {
  agents: Agent[];
  isLoadingAgents: boolean;
  currentAgent: Agent | null;
  currentConversation: Conversation | null;
  conversations: Conversation[];
  isLoadingConversations: boolean;
  isSendingMessage: boolean;
  fetchAgents: () => Promise<void>;
  setCurrentAgent: (agent: Agent | null) => void;
  fetchConversations: () => Promise<void>;
  startConversation: (agentId: string) => Promise<Conversation>;
  sendMessage: (message: string) => Promise<Message>;
  loadConversation: (conversationId: string) => Promise<void>;
}

const AgentContext = createContext<AgentContextType | undefined>(undefined);

export function AgentProvider({ children }: { children: React.ReactNode }) {
  const [agents, setAgents] = useState<Agent[]>([]);
  const [isLoadingAgents, setIsLoadingAgents] = useState(false);
  const [currentAgent, setCurrentAgent] = useState<Agent | null>(null);
  const [currentConversation, setCurrentConversation] = useState<Conversation | null>(null);
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [isLoadingConversations, setIsLoadingConversations] = useState(false);
  const [isSendingMessage, setIsSendingMessage] = useState(false);

  const fetchAgents = async () => {
    setIsLoadingAgents(true);
    try {
      const agentsData = await api.agents.getAll();
      setAgents(agentsData);
    } catch (error) {
      console.error('Failed to fetch agents:', error);
    } finally {
      setIsLoadingAgents(false);
    }
  };

  const fetchConversations = async () => {
    setIsLoadingConversations(true);
    try {
      const conversationsData = await api.chat.getConversations();
      setConversations(conversationsData);
    } catch (error) {
      console.error('Failed to fetch conversations:', error);
    } finally {
      setIsLoadingConversations(false);
    }
  };

  const startConversation = async (agentId: string) => {
    // Find the agent
    const agent = agents.find(a => a.id === agentId);
    if (!agent) {
      throw new Error(`Agent with ID ${agentId} not found`);
    }
    
    setCurrentAgent(agent);
    
    // Create a new conversation (this is a mock since our API doesn't have this endpoint yet)
    const newConversation: Conversation = {
      id: `conv-${Date.now()}`,
      agentId,
      title: `New conversation with ${agent.name}`,
      messages: [],
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
    };
    
    setCurrentConversation(newConversation);
    setConversations(prev => [newConversation, ...prev]);
    
    return newConversation;
  };

  const sendMessage = async (message: string) => {
    if (!currentAgent || !currentConversation) {
      throw new Error('No active conversation');
    }
    
    setIsSendingMessage(true);
    
    try {
      // Add user message to conversation
      const userMessage: Message = {
        id: `msg-user-${Date.now()}`,
        content: message,
        role: 'user',
        timestamp: new Date().toISOString(),
      };
      
      // Update conversation with user message
      const updatedConversation = {
        ...currentConversation,
        messages: [...currentConversation.messages, userMessage],
        updatedAt: new Date().toISOString(),
      };
      
      setCurrentConversation(updatedConversation);
      
      // Send message to API
      const response = await api.chat.sendMessage(
        currentAgent.id,
        message,
        currentConversation.id
      );
      
      // Add assistant message to conversation
      const assistantMessage: Message = {
        id: response.id || `msg-assistant-${Date.now()}`,
        content: response.message || response.content,
        role: 'assistant',
        timestamp: new Date().toISOString(),
        confidence: response.confidence,
      };
      
      // Update conversation with assistant message
      const finalConversation = {
        ...updatedConversation,
        messages: [...updatedConversation.messages, assistantMessage],
        updatedAt: new Date().toISOString(),
      };
      
      setCurrentConversation(finalConversation);
      
      // Update conversations list
      setConversations(prev => 
        prev.map(conv => 
          conv.id === finalConversation.id ? finalConversation : conv
        )
      );
      
      return assistantMessage;
    } catch (error) {
      console.error('Failed to send message:', error);
      throw error;
    } finally {
      setIsSendingMessage(false);
    }
  };

  const loadConversation = async (conversationId: string) => {
    try {
      const conversation = await api.chat.getConversation(conversationId);
      setCurrentConversation(conversation);
      
      // Find and set the current agent
      const agent = agents.find(a => a.id === conversation.agentId);
      if (agent) {
        setCurrentAgent(agent);
      }
    } catch (error) {
      console.error('Failed to load conversation:', error);
      throw error;
    }
  };

  return (
    <AgentContext.Provider
      value={{
        agents,
        isLoadingAgents,
        currentAgent,
        currentConversation,
        conversations,
        isLoadingConversations,
        isSendingMessage,
        fetchAgents,
        setCurrentAgent,
        fetchConversations,
        startConversation,
        sendMessage,
        loadConversation,
      }}
    >
      {children}
    </AgentContext.Provider>
  );
}

export function useAgent() {
  const context = useContext(AgentContext);
  if (context === undefined) {
    throw new Error('useAgent must be used within an AgentProvider');
  }
  return context;
}
