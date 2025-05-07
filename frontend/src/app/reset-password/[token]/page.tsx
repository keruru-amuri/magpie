'use client';

import React from 'react';
import ResetPasswordForm from '../../../components/auth/ResetPasswordForm';

interface ResetPasswordPageProps {
  params: {
    token: string;
  };
}

export default function ResetPasswordPage({ params }: ResetPasswordPageProps) {
  const { token } = params;
  
  return (
    <div className="flex min-h-screen bg-gray-100 dark:bg-gray-900">
      <div className="flex-1 flex flex-col justify-center items-center px-4 sm:px-6 lg:px-8 py-12">
        <ResetPasswordForm token={token} />
      </div>
      
      {/* Background image or branding */}
      <div className="hidden lg:block lg:w-1/2 bg-cover bg-center" style={{ backgroundImage: 'url(/images/aircraft-maintenance.jpg)' }}>
        <div className="h-full w-full bg-black bg-opacity-50 flex flex-col justify-center items-center text-white p-12">
          <h1 className="text-4xl font-bold mb-4">MAGPIE Platform</h1>
          <p className="text-xl mb-8 text-center">
            Reset Your Password
          </p>
          <div className="max-w-md">
            <p className="mb-4">
              Create a new password for your MAGPIE account. Make sure to choose a strong password that you haven't used elsewhere.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
