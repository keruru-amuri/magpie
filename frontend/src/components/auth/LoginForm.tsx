'use client';

import React, { useState } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { useAuth } from '../../contexts/AuthContext';
import { useAnalytics } from '../../hooks/useAnalytics';
import { useNotifications } from '../../hooks/useNotifications';
import Button from '../common/Button';
import LoadingSpinner from '../common/LoadingSpinner';
import ErrorDisplay from '../common/ErrorDisplay';

export default function LoginForm() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [rememberMe, setRememberMe] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const { login } = useAuth();
  const analytics = useAnalytics();
  const notifications = useNotifications();
  const router = useRouter();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    // Validate form
    if (!email || !password) {
      setError('Please enter both email and password');
      return;
    }

    // Clear previous errors
    setError(null);
    setIsSubmitting(true);

    try {
      // Track login attempt
      analytics.trackEvent('login_attempt', { email });

      // Attempt login with NextAuth
      await login(email, password);

      // Get redirect URL from URL params, session storage, or default to dashboard
      const urlParams = new URLSearchParams(window.location.search);
      const callbackUrl = urlParams.get('callbackUrl');
      const redirectUrl = callbackUrl ||
                          sessionStorage.getItem('redirectAfterLogin') ||
                          '/dashboard';

      sessionStorage.removeItem('redirectAfterLogin');

      // Redirect to dashboard or previous page
      router.push(redirectUrl);
    } catch (err) {
      // Set error message
      setError(err instanceof Error ? err.message : 'Invalid email or password');

      // Track login failure
      analytics.trackEvent('login_failure', { email, error: err instanceof Error ? err.message : 'Unknown error' });
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="w-full max-w-md p-8 space-y-8 bg-white dark:bg-gray-800 rounded-lg shadow-md">
      <div className="text-center">
        <h1 className="text-3xl font-bold text-gray-900 dark:text-white">Welcome to MAGPIE</h1>
        <p className="mt-2 text-gray-600 dark:text-gray-400">
          Sign in to your account
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
            <label htmlFor="password" className="block text-sm font-medium text-gray-700 dark:text-gray-300">
              Password
            </label>
            <input
              id="password"
              name="password"
              type="password"
              autoComplete="current-password"
              required
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="mt-1 block w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm placeholder-gray-400 dark:placeholder-gray-500 dark:bg-gray-700 dark:text-white focus:outline-none focus:ring-primary-500 focus:border-primary-500"
              placeholder="Enter your password"
              disabled={isSubmitting}
            />
          </div>
        </div>

        <div className="flex items-center justify-between">
          <div className="flex items-center">
            <input
              id="remember-me"
              name="remember-me"
              type="checkbox"
              checked={rememberMe}
              onChange={(e) => setRememberMe(e.target.checked)}
              className="h-4 w-4 text-primary-600 focus:ring-primary-500 border-gray-300 dark:border-gray-600 rounded"
            />
            <label htmlFor="remember-me" className="ml-2 block text-sm text-gray-700 dark:text-gray-300">
              Remember me
            </label>
          </div>

          <div className="text-sm">
            <Link
              href="/forgot-password"
              className="font-medium text-primary-600 hover:text-primary-500 dark:text-primary-400 dark:hover:text-primary-300"
            >
              Forgot your password?
            </Link>
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
                Signing in...
              </>
            ) : (
              'Sign in'
            )}
          </Button>
        </div>

        <div className="text-center text-sm">
          <span className="text-gray-600 dark:text-gray-400">
            Don't have an account?{' '}
          </span>
          <Link
            href="/register"
            className="font-medium text-primary-600 hover:text-primary-500 dark:text-primary-400 dark:hover:text-primary-300"
          >
            Sign up
          </Link>
        </div>
      </form>
    </div>
  );
}
