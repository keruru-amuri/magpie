/**
 * Custom hook for handling API errors
 */

import { useState, useCallback } from 'react';
import { ApiError } from '../types/api';

interface UseApiErrorOptions {
  initialError?: ApiError | null;
  onError?: (error: ApiError) => void;
}

export function useApiError(options: UseApiErrorOptions = {}) {
  const [error, setError] = useState<ApiError | null>(options.initialError || null);
  const [isVisible, setIsVisible] = useState(!!options.initialError);

  // Set error
  const handleError = useCallback((apiError: ApiError | null) => {
    setError(apiError);
    setIsVisible(!!apiError);
    
    if (apiError && options.onError) {
      options.onError(apiError);
    }
  }, [options]);

  // Clear error
  const clearError = useCallback(() => {
    setError(null);
    setIsVisible(false);
  }, []);

  // Hide error without clearing it
  const hideError = useCallback(() => {
    setIsVisible(false);
  }, []);

  // Show error if it exists
  const showError = useCallback(() => {
    if (error) {
      setIsVisible(true);
    }
  }, [error]);

  // Get error message
  const getErrorMessage = useCallback((defaultMessage: string = 'An error occurred') => {
    if (!error) {
      return defaultMessage;
    }
    
    return error.message || defaultMessage;
  }, [error]);

  // Get error status code
  const getErrorStatus = useCallback(() => {
    return error?.status || 0;
  }, [error]);

  // Check if error is a specific status code
  const isErrorStatus = useCallback((status: number) => {
    return error?.status === status;
  }, [error]);

  // Check if error is a client error (4xx)
  const isClientError = useCallback(() => {
    return error?.status ? error.status >= 400 && error.status < 500 : false;
  }, [error]);

  // Check if error is a server error (5xx)
  const isServerError = useCallback(() => {
    return error?.status ? error.status >= 500 : false;
  }, [error]);

  // Check if error is an authentication error (401)
  const isAuthError = useCallback(() => {
    return error?.status === 401;
  }, [error]);

  // Check if error is a permission error (403)
  const isPermissionError = useCallback(() => {
    return error?.status === 403;
  }, [error]);

  // Check if error is a not found error (404)
  const isNotFoundError = useCallback(() => {
    return error?.status === 404;
  }, [error]);

  // Check if error is a validation error (422)
  const isValidationError = useCallback(() => {
    return error?.status === 422;
  }, [error]);

  // Get validation errors
  const getValidationErrors = useCallback(() => {
    if (!error || !error.details || error.status !== 422) {
      return {};
    }
    
    return error.details;
  }, [error]);

  return {
    error,
    isVisible,
    handleError,
    clearError,
    hideError,
    showError,
    getErrorMessage,
    getErrorStatus,
    isErrorStatus,
    isClientError,
    isServerError,
    isAuthError,
    isPermissionError,
    isNotFoundError,
    isValidationError,
    getValidationErrors
  };
}
