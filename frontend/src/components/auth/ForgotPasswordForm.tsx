'use client';

import React, { useState } from 'react';
import Link from 'next/link';
import { useAuth } from '../../contexts/AuthContext';
import { useAnalytics } from '../../hooks/useAnalytics';
import Button from '../common/Button';
import LoadingSpinner from '../common/LoadingSpinner';
import ErrorDisplay from '../common/ErrorDisplay';

export default function ForgotPasswordForm() {
  const [email, setEmail] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isSubmitted, setIsSubmitted] = useState(false);
  
  const { requestPasswordReset } = useAuth();
  const analytics = useAnalytics();
  
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    // Validate email
    if (!email) {
      setError('Email is required');
      return;
    }
    
    // Clear previous errors
    setError(null);
    setIsSubmitting(true);
    
    try {
      // Track password reset request
      analytics.trackEvent('password_reset_request', { email });
      
      // Request password reset
      await requestPasswordReset(email);
      
      // Set submitted state
      setIsSubmitted(true);
    } catch (err) {
      // Set error message (should not happen due to security measures in requestPasswordReset)
      setError(err instanceof Error ? err.message : 'An error occurred');
      
      // Track password reset request failure
      analytics.trackEvent('password_reset_request_failure', { 
        email, 
        error: err instanceof Error ? err.message : 'Unknown error' 
      });
    } finally {
      setIsSubmitting(false);
    }
  };
  
  // If form has been submitted, show success message
  if (isSubmitted) {
    return (
      <div className="w-full max-w-md p-8 space-y-8 bg-white dark:bg-gray-800 rounded-lg shadow-md">
        <div className="text-center">
          <svg
            className="mx-auto h-12 w-12 text-green-500"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
            xmlns="http://www.w3.org/2000/svg"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"
            />
          </svg>
          <h2 className="mt-6 text-center text-2xl font-bold text-gray-900 dark:text-white">
            Check Your Email
          </h2>
          <p className="mt-2 text-center text-gray-600 dark:text-gray-400">
            If an account exists with the email {email}, we've sent instructions to reset your password.
          </p>
        </div>
        <div className="mt-6">
          <Link
            href="/login"
            className="w-full flex justify-center py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-primary-600 hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500"
          >
            Return to Login
          </Link>
        </div>
      </div>
    );
  }
  
  return (
    <div className="w-full max-w-md p-8 space-y-8 bg-white dark:bg-gray-800 rounded-lg shadow-md">
      <div className="text-center">
        <h1 className="text-3xl font-bold text-gray-900 dark:text-white">Reset Your Password</h1>
        <p className="mt-2 text-gray-600 dark:text-gray-400">
          Enter your email address and we'll send you instructions to reset your password
        </p>
      </div>
      
      {error && (
        <ErrorDisplay
          error={error}
          onDismiss={() => setError(null)}
          className="mb-4"
        />
      )}
      
      <form className="mt-8 space-y-6" onSubmit={handleSubmit}>
        <div>
          <label htmlFor="email" className="block text-sm font-medium text-gray-700 dark:text-gray-300">
            Email Address
          </label>
          <input
            id="email"
            name="email"
            type="email"
            autoComplete="email"
            required
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            className="mt-1 block w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm placeholder-gray-400 dark:placeholder-gray-500 dark:bg-gray-700 dark:text-white focus:outline-none focus:ring-primary-500 focus:border-primary-500"
            placeholder="Enter your email address"
            disabled={isSubmitting}
          />
        </div>
        
        <div>
          <Button
            type="submit"
            variant="primary"
            className="w-full flex justify-center"
            disabled={isSubmitting}
          >
            {isSubmitting ? (
              <>
                <LoadingSpinner size="sm" color="white" className="mr-2" />
                Sending...
              </>
            ) : (
              'Send Reset Instructions'
            )}
          </Button>
        </div>
        
        <div className="text-center text-sm">
          <Link
            href="/login"
            className="font-medium text-primary-600 hover:text-primary-500 dark:text-primary-400 dark:hover:text-primary-300"
          >
            Back to Login
          </Link>
        </div>
      </form>
    </div>
  );
}
