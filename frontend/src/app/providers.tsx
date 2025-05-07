'use client';

import React, { useEffect } from 'react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { AuthProvider } from '../contexts/AuthContext';
import { AgentProvider } from '../contexts/AgentContext';
import { OrchestratorProvider } from '../components/orchestrator/OrchestratorContext';
import NotificationContainer from '../components/common/NotificationContainer';

// Create a client
const queryClient = new QueryClient();

export default function Providers({ children }: { children: React.ReactNode }) {
  // Suppress specific Next.js development errors
  useEffect(() => {
    // Store the original console.error
    const originalConsoleError = console.error;

    // Override console.error to filter out specific errors
    console.error = (...args) => {
      // Check if this is the ResizeObserver error
      const errorMessage = args[0]?.toString?.() || '';
      if (
        errorMessage.includes('ResizeObserver') ||
        errorMessage.includes('Maximum update depth exceeded')
      ) {
        // Suppress these specific errors
        return;
      }

      // Pass through all other errors to the original console.error
      originalConsoleError(...args);
    };

    // Restore the original console.error when the component unmounts
    return () => {
      console.error = originalConsoleError;
    };
  }, []);

  return (
    <QueryClientProvider client={queryClient}>
      <AuthProvider>
        <AgentProvider>
          <OrchestratorProvider>
            {children}
            <NotificationContainer position="top-right" maxNotifications={5} />
          </OrchestratorProvider>
        </AgentProvider>
      </AuthProvider>
    </QueryClientProvider>
  );
}
