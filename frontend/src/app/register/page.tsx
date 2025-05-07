'use client';

import React, { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '../../contexts/AuthContext';
import RegisterForm from '../../components/auth/RegisterForm';
import LoadingSpinner from '../../components/common/LoadingSpinner';

export default function RegisterPage() {
  const { isAuthenticated, isLoading } = useAuth();
  const router = useRouter();
  
  // Redirect to dashboard if already authenticated
  useEffect(() => {
    if (isAuthenticated && !isLoading) {
      router.push('/dashboard');
    }
  }, [isAuthenticated, isLoading, router]);
  
  // Show loading spinner while checking authentication
  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <LoadingSpinner size="lg" />
      </div>
    );
  }
  
  // If not authenticated, show registration form
  return (
    <div className="flex min-h-screen bg-gray-100 dark:bg-gray-900">
      <div className="flex-1 flex flex-col justify-center items-center px-4 sm:px-6 lg:px-8 py-12">
        <RegisterForm />
      </div>
      
      {/* Background image or branding */}
      <div className="hidden lg:block lg:w-1/2 bg-cover bg-center" style={{ backgroundImage: 'url(/images/aircraft-maintenance.jpg)' }}>
        <div className="h-full w-full bg-black bg-opacity-50 flex flex-col justify-center items-center text-white p-12">
          <h1 className="text-4xl font-bold mb-4">MAGPIE Platform</h1>
          <p className="text-xl mb-8 text-center">
            MAG Platform for Intelligent Execution - An AI-powered platform for aircraft MRO organizations
          </p>
          <div className="max-w-md">
            <p className="mb-4">
              Join MAGPIE to access powerful AI tools that help maintenance teams work more efficiently and effectively.
            </p>
            <ul className="list-disc list-inside space-y-2">
              <li>Instant access to technical documentation</li>
              <li>AI-powered troubleshooting assistance</li>
              <li>Automated maintenance procedure generation</li>
              <li>Seamless integration with existing MRO systems</li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
}
