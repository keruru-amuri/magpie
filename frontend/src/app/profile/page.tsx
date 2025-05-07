'use client';

import React from 'react';
import UserProfile from '../../components/profile/UserProfile';
import ProtectedRoute from '../../components/auth/ProtectedRoute';
import ChangePasswordForm from '../../components/profile/ChangePasswordForm';

export default function ProfilePage() {
  return (
    <ProtectedRoute>
      <div className="container mx-auto px-4 py-8">
        <h1 className="text-2xl font-bold text-gray-900 dark:text-white mb-6">
          My Profile
        </h1>
        
        <div className="grid grid-cols-1 gap-8 lg:grid-cols-3">
          <div className="lg:col-span-2">
            <UserProfile />
          </div>
          
          <div>
            <ChangePasswordForm />
          </div>
        </div>
      </div>
    </ProtectedRoute>
  );
}
