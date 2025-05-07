'use client';

import React from 'react';
import { XCircleIcon, XMarkIcon } from '@heroicons/react/24/outline';
import { ApiError } from '../../types/api';

interface ErrorDisplayProps {
  error: ApiError | string;
  onDismiss?: () => void;
  className?: string;
  showDetails?: boolean;
}

export default function ErrorDisplay({
  error,
  onDismiss,
  className = '',
  showDetails = false,
}: ErrorDisplayProps) {
  // Extract error message
  const errorMessage = typeof error === 'string' 
    ? error 
    : error.message || 'An unknown error occurred';
  
  // Extract error status
  const errorStatus = typeof error === 'string' 
    ? null 
    : error.status;
  
  // Extract error details
  const errorDetails = typeof error === 'string' 
    ? null 
    : error.details;

  return (
    <div className={`bg-red-50 dark:bg-red-900/30 border border-red-400 dark:border-red-800 text-red-700 dark:text-red-300 px-4 py-3 rounded relative ${className}`} role="alert">
      <div className="flex items-start">
        <div className="flex-shrink-0">
          <XCircleIcon className="h-5 w-5 text-red-400 dark:text-red-500" aria-hidden="true" />
        </div>
        <div className="ml-3 flex-1">
          <h3 className="text-sm font-medium">
            {errorStatus ? `Error ${errorStatus}: ` : ''}
            {errorMessage}
          </h3>
          
          {showDetails && errorDetails && (
            <div className="mt-2 text-sm">
              <ul className="list-disc pl-5 space-y-1">
                {Object.entries(errorDetails).map(([key, value]) => (
                  <li key={key}>
                    <strong>{key}:</strong> {typeof value === 'object' ? JSON.stringify(value) : value}
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
        
        {onDismiss && (
          <div className="ml-auto pl-3">
            <div className="-mx-1.5 -my-1.5">
              <button
                type="button"
                onClick={onDismiss}
                className="inline-flex rounded-md p-1.5 text-red-500 dark:text-red-400 hover:bg-red-100 dark:hover:bg-red-800 focus:outline-none focus:ring-2 focus:ring-red-600 dark:focus:ring-red-500"
              >
                <span className="sr-only">Dismiss</span>
                <XMarkIcon className="h-5 w-5" aria-hidden="true" />
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
