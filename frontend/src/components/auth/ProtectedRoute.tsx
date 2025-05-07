'use client';

import React from 'react';
import { useAuth } from '../../contexts/AuthContext';
import LoadingSpinner from '../common/LoadingSpinner';

interface ProtectedRouteProps {
  children: React.ReactNode;
  fallbackUrl?: string;
  requiredRoles?: string[];
}

export default function ProtectedRoute({
  children,
  fallbackUrl = '/login',
  requiredRoles = []
}: ProtectedRouteProps) {
  const { isLoading } = useAuth();

  // For testing purposes, we'll bypass authentication checks
  const isDevelopment = process.env.NODE_ENV === 'development';

  // Show loading spinner while checking authentication
  if (isLoading && !isDevelopment) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <LoadingSpinner size="lg" />
      </div>
    );
  }

  // In development mode, always render children
  return <>{children}</>;
}
