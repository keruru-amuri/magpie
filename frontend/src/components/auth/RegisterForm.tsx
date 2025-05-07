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

export default function RegisterForm() {
  const [formData, setFormData] = useState({
    name: '',
    email: '',
    password: '',
    confirmPassword: '',
  });
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [acceptTerms, setAcceptTerms] = useState(false);
  
  const { register } = useAuth();
  const analytics = useAnalytics();
  const notifications = useNotifications();
  const router = useRouter();
  
  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
  };
  
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    // Validate form
    if (!formData.name || !formData.email || !formData.password || !formData.confirmPassword) {
      setError('All fields are required');
      return;
    }
    
    if (formData.password !== formData.confirmPassword) {
      setError('Passwords do not match');
      return;
    }
    
    if (!acceptTerms) {
      setError('You must accept the terms and conditions');
      return;
    }
    
    // Password strength validation
    if (formData.password.length < 8) {
      setError('Password must be at least 8 characters long');
      return;
    }
    
    // Clear previous errors
    setError(null);
    setIsSubmitting(true);
    
    try {
      // Track registration attempt
      analytics.trackEvent('registration_attempt', { email: formData.email });
      
      // Attempt registration
      await register({
        name: formData.name,
        email: formData.email,
        password: formData.password,
      });
      
      // Track successful registration
      analytics.trackEvent('registration_success', { email: formData.email });
      
      // Redirect to login page
      router.push('/login');
    } catch (err) {
      // Set error message
      setError(err instanceof Error ? err.message : 'Registration failed');
      
      // Track registration failure
      analytics.trackEvent('registration_failure', { 
        email: formData.email, 
        error: err instanceof Error ? err.message : 'Unknown error' 
      });
    } finally {
      setIsSubmitting(false);
    }
  };
  
  return (
    <div className="w-full max-w-md p-8 space-y-8 bg-white dark:bg-gray-800 rounded-lg shadow-md">
      <div className="text-center">
        <h1 className="text-3xl font-bold text-gray-900 dark:text-white">Create an Account</h1>
        <p className="mt-2 text-gray-600 dark:text-gray-400">
          Join MAGPIE to access AI-powered aircraft maintenance tools
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
            <label htmlFor="name" className="block text-sm font-medium text-gray-700 dark:text-gray-300">
              Full Name
            </label>
            <input
              id="name"
              name="name"
              type="text"
              autoComplete="name"
              required
              value={formData.name}
              onChange={handleChange}
              className="mt-1 block w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm placeholder-gray-400 dark:placeholder-gray-500 dark:bg-gray-700 dark:text-white focus:outline-none focus:ring-primary-500 focus:border-primary-500"
              placeholder="Enter your full name"
              disabled={isSubmitting}
            />
          </div>
          
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
              value={formData.email}
              onChange={handleChange}
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
              autoComplete="new-password"
              required
              value={formData.password}
              onChange={handleChange}
              className="mt-1 block w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm placeholder-gray-400 dark:placeholder-gray-500 dark:bg-gray-700 dark:text-white focus:outline-none focus:ring-primary-500 focus:border-primary-500"
              placeholder="Create a password"
              disabled={isSubmitting}
            />
            <p className="mt-1 text-xs text-gray-500 dark:text-gray-400">
              Password must be at least 8 characters long
            </p>
          </div>
          
          <div>
            <label htmlFor="confirmPassword" className="block text-sm font-medium text-gray-700 dark:text-gray-300">
              Confirm Password
            </label>
            <input
              id="confirmPassword"
              name="confirmPassword"
              type="password"
              autoComplete="new-password"
              required
              value={formData.confirmPassword}
              onChange={handleChange}
              className="mt-1 block w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm placeholder-gray-400 dark:placeholder-gray-500 dark:bg-gray-700 dark:text-white focus:outline-none focus:ring-primary-500 focus:border-primary-500"
              placeholder="Confirm your password"
              disabled={isSubmitting}
            />
          </div>
        </div>
        
        <div className="flex items-center">
          <input
            id="accept-terms"
            name="accept-terms"
            type="checkbox"
            checked={acceptTerms}
            onChange={(e) => setAcceptTerms(e.target.checked)}
            className="h-4 w-4 text-primary-600 focus:ring-primary-500 border-gray-300 dark:border-gray-600 rounded"
            disabled={isSubmitting}
          />
          <label htmlFor="accept-terms" className="ml-2 block text-sm text-gray-700 dark:text-gray-300">
            I accept the <Link href="/terms" className="text-primary-600 hover:text-primary-500 dark:text-primary-400">Terms of Service</Link> and <Link href="/privacy" className="text-primary-600 hover:text-primary-500 dark:text-primary-400">Privacy Policy</Link>
          </label>
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
                Creating Account...
              </>
            ) : (
              'Create Account'
            )}
          </Button>
        </div>
        
        <div className="text-center text-sm">
          <span className="text-gray-600 dark:text-gray-400">
            Already have an account?{' '}
          </span>
          <Link
            href="/login"
            className="font-medium text-primary-600 hover:text-primary-500 dark:text-primary-400 dark:hover:text-primary-300"
          >
            Sign in
          </Link>
        </div>
      </form>
    </div>
  );
}
