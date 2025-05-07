'use client';

import React, { useState } from 'react';
import { useAuth } from '../../contexts/AuthContext';
import { useAnalytics } from '../../hooks/useAnalytics';
import { useNotifications } from '../../hooks/useNotifications';
import Button from '../common/Button';
import LoadingSpinner from '../common/LoadingSpinner';
import ErrorDisplay from '../common/ErrorDisplay';

export default function UserProfile() {
  const { user, updateUser } = useAuth();
  const analytics = useAnalytics();
  const notifications = useNotifications();
  
  const [isEditing, setIsEditing] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  const [formData, setFormData] = useState({
    name: user?.name || '',
    email: user?.email || '',
    firstName: user?.firstName || '',
    lastName: user?.lastName || '',
  });
  
  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
  };
  
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    // Validate form
    if (!formData.name || !formData.email) {
      setError('Name and email are required');
      return;
    }
    
    // Clear previous errors
    setError(null);
    setIsSubmitting(true);
    
    try {
      // Track profile update attempt
      analytics.trackEvent('profile_update_attempt');
      
      // Call API to update profile
      const response = await fetch('/api/user/profile', {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(formData),
      });
      
      if (!response.ok) {
        const data = await response.json();
        throw new Error(data.message || 'Failed to update profile');
      }
      
      // Update user in context
      updateUser(formData);
      
      // Show success notification
      notifications.showSuccess(
        'Profile Updated',
        'Your profile has been updated successfully'
      );
      
      // Track successful profile update
      analytics.trackEvent('profile_update_success');
      
      // Exit edit mode
      setIsEditing(false);
    } catch (err) {
      // Set error message
      setError(err instanceof Error ? err.message : 'Failed to update profile');
      
      // Track profile update failure
      analytics.trackEvent('profile_update_failure', { 
        error: err instanceof Error ? err.message : 'Unknown error' 
      });
    } finally {
      setIsSubmitting(false);
    }
  };
  
  if (!user) {
    return (
      <div className="text-center p-8">
        <p className="text-gray-600 dark:text-gray-400">
          Please log in to view your profile
        </p>
      </div>
    );
  }
  
  return (
    <div className="bg-white dark:bg-gray-800 shadow rounded-lg overflow-hidden">
      <div className="px-4 py-5 sm:px-6 border-b border-gray-200 dark:border-gray-700">
        <h3 className="text-lg leading-6 font-medium text-gray-900 dark:text-white">
          User Profile
        </h3>
        <p className="mt-1 max-w-2xl text-sm text-gray-500 dark:text-gray-400">
          Personal details and account information
        </p>
      </div>
      
      {error && (
        <div className="px-4 py-3">
          <ErrorDisplay
            error={error}
            onDismiss={() => setError(null)}
          />
        </div>
      )}
      
      <div className="px-4 py-5 sm:p-6">
        {isEditing ? (
          <form onSubmit={handleSubmit}>
            <div className="grid grid-cols-1 gap-6 sm:grid-cols-2">
              <div>
                <label htmlFor="name" className="block text-sm font-medium text-gray-700 dark:text-gray-300">
                  Full Name
                </label>
                <input
                  type="text"
                  name="name"
                  id="name"
                  value={formData.name}
                  onChange={handleChange}
                  className="mt-1 block w-full border border-gray-300 dark:border-gray-600 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-primary-500 focus:border-primary-500 sm:text-sm dark:bg-gray-700 dark:text-white"
                  disabled={isSubmitting}
                />
              </div>
              
              <div>
                <label htmlFor="email" className="block text-sm font-medium text-gray-700 dark:text-gray-300">
                  Email Address
                </label>
                <input
                  type="email"
                  name="email"
                  id="email"
                  value={formData.email}
                  onChange={handleChange}
                  className="mt-1 block w-full border border-gray-300 dark:border-gray-600 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-primary-500 focus:border-primary-500 sm:text-sm dark:bg-gray-700 dark:text-white"
                  disabled={isSubmitting}
                />
              </div>
              
              <div>
                <label htmlFor="firstName" className="block text-sm font-medium text-gray-700 dark:text-gray-300">
                  First Name
                </label>
                <input
                  type="text"
                  name="firstName"
                  id="firstName"
                  value={formData.firstName}
                  onChange={handleChange}
                  className="mt-1 block w-full border border-gray-300 dark:border-gray-600 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-primary-500 focus:border-primary-500 sm:text-sm dark:bg-gray-700 dark:text-white"
                  disabled={isSubmitting}
                />
              </div>
              
              <div>
                <label htmlFor="lastName" className="block text-sm font-medium text-gray-700 dark:text-gray-300">
                  Last Name
                </label>
                <input
                  type="text"
                  name="lastName"
                  id="lastName"
                  value={formData.lastName}
                  onChange={handleChange}
                  className="mt-1 block w-full border border-gray-300 dark:border-gray-600 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-primary-500 focus:border-primary-500 sm:text-sm dark:bg-gray-700 dark:text-white"
                  disabled={isSubmitting}
                />
              </div>
            </div>
            
            <div className="mt-6 flex space-x-3">
              <Button
                type="submit"
                variant="primary"
                disabled={isSubmitting}
              >
                {isSubmitting ? (
                  <>
                    <LoadingSpinner size="sm" color="white" className="mr-2" />
                    Saving...
                  </>
                ) : (
                  'Save Changes'
                )}
              </Button>
              
              <Button
                type="button"
                variant="secondary"
                onClick={() => {
                  setIsEditing(false);
                  setFormData({
                    name: user.name || '',
                    email: user.email || '',
                    firstName: user.firstName || '',
                    lastName: user.lastName || '',
                  });
                }}
                disabled={isSubmitting}
              >
                Cancel
              </Button>
            </div>
          </form>
        ) : (
          <div className="space-y-6">
            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
              <div>
                <h4 className="text-sm font-medium text-gray-500 dark:text-gray-400">Full Name</h4>
                <p className="mt-1 text-sm text-gray-900 dark:text-white">{user.name}</p>
              </div>
              
              <div>
                <h4 className="text-sm font-medium text-gray-500 dark:text-gray-400">Email Address</h4>
                <p className="mt-1 text-sm text-gray-900 dark:text-white">{user.email}</p>
              </div>
              
              <div>
                <h4 className="text-sm font-medium text-gray-500 dark:text-gray-400">Role</h4>
                <p className="mt-1 text-sm text-gray-900 dark:text-white capitalize">{user.role}</p>
              </div>
              
              <div>
                <h4 className="text-sm font-medium text-gray-500 dark:text-gray-400">Account ID</h4>
                <p className="mt-1 text-sm text-gray-900 dark:text-white">{user.id}</p>
              </div>
              
              {user.firstName && (
                <div>
                  <h4 className="text-sm font-medium text-gray-500 dark:text-gray-400">First Name</h4>
                  <p className="mt-1 text-sm text-gray-900 dark:text-white">{user.firstName}</p>
                </div>
              )}
              
              {user.lastName && (
                <div>
                  <h4 className="text-sm font-medium text-gray-500 dark:text-gray-400">Last Name</h4>
                  <p className="mt-1 text-sm text-gray-900 dark:text-white">{user.lastName}</p>
                </div>
              )}
            </div>
            
            <div>
              <Button
                type="button"
                variant="primary"
                onClick={() => setIsEditing(true)}
              >
                Edit Profile
              </Button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
