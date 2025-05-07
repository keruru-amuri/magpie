'use client';

import React, { useState } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { useAuth } from '../../contexts/AuthContext';
import { useAnalytics } from '../../hooks/useAnalytics';
import Button from '../common/Button';
import LoadingSpinner from '../common/LoadingSpinner';
import ErrorDisplay from '../common/ErrorDisplay';

interface ResetPasswordFormProps {
  token: string;
}

export default function ResetPasswordForm({ token }: ResetPasswordFormProps) {
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isSubmitted, setIsSubmitted] = useState(false);
  
  const { confirmPasswordReset } = useAuth();
  const analytics = useAnalytics();
  const router = useRouter();
  
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    // Validate passwords
    if (!password || !confirmPassword) {
      setError('Both fields are required');
      return;
    }
    
    if (password !== confirmPassword) {
      setError('Passwords do not match');
      return;
    }
    
    // Password strength validation
    if (password.length < 8) {
      setError('Password must be at least 8 characters long');
      return;
    }
    
    // Clear previous errors
    setError(null);
    setIsSubmitting(true);
    
    try {
      // Track password reset attempt
      analytics.trackEvent('password_reset_confirm');
      
      // Confirm password reset
      await confirmPasswordReset(token, password);
      
      // Set submitted state
      setIsSubmitted(true);
      
      // Redirect to login after 3 seconds
      setTimeout(() => {
        router.push('/login');
      }, 3000);
    } catch (err) {
      // Set error message
      setError(err instanceof Error ? err.message : 'Password reset failed');
      
      // Track password reset failure
      analytics.trackEvent('password_reset_confirm_failure', { 
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
            Password Reset Successful
          </h2>
          <p className="mt-2 text-center text-gray-600 dark:text-gray-400">
            Your password has been reset successfully. You will be redirected to the login page in a few seconds.
          </p>
        </div>
        <div className="mt-6">
          <Link
            href="/login"
            className="w-full flex justify-center py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-primary-600 hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500"
          >
            Go to Login
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
          Enter your new password below
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
        <div className="space-y-4">
          <div>
            <label htmlFor="password" className="block text-sm font-medium text-gray-700 dark:text-gray-300">
              New Password
            </label>
            <input
              id="password"
              name="password"
              type="password"
              autoComplete="new-password"
              required
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="mt-1 block w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm placeholder-gray-400 dark:placeholder-gray-500 dark:bg-gray-700 dark:text-white focus:outline-none focus:ring-primary-500 focus:border-primary-500"
              placeholder="Enter your new password"
              disabled={isSubmitting}
            />
            <p className="mt-1 text-xs text-gray-500 dark:text-gray-400">
              Password must be at least 8 characters long
            </p>
          </div>
          
          <div>
            <label htmlFor="confirmPassword" className="block text-sm font-medium text-gray-700 dark:text-gray-300">
              Confirm New Password
            </label>
            <input
              id="confirmPassword"
              name="confirmPassword"
              type="password"
              autoComplete="new-password"
              required
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
              className="mt-1 block w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm placeholder-gray-400 dark:placeholder-gray-500 dark:bg-gray-700 dark:text-white focus:outline-none focus:ring-primary-500 focus:border-primary-500"
              placeholder="Confirm your new password"
              disabled={isSubmitting}
            />
          </div>
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
                Resetting Password...
              </>
            ) : (
              'Reset Password'
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
