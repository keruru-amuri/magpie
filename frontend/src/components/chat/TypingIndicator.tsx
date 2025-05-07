'use client';

import React from 'react';

export default function TypingIndicator() {
  return (
    <div className="flex items-center">
      <div className="h-10 w-10 rounded-full bg-gradient-to-br from-primary-500 to-primary-700 flex items-center justify-center text-white mr-3 flex-shrink-0 shadow-sm">
        <svg
          xmlns="http://www.w3.org/2000/svg"
          className="h-6 w-6"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="2"
          strokeLinecap="round"
          strokeLinejoin="round"
        >
          <path d="M22 12H8l4-4H8l-6 6 6 6h4l-4-4h14z" />
        </svg>
      </div>
      <div className="bg-gray-200 dark:bg-gray-800 rounded-lg px-4 py-2 text-gray-800 dark:text-gray-200">
        <div className="flex space-x-1">
          <div className="w-2 h-2 bg-gray-500 dark:bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }}></div>
          <div className="w-2 h-2 bg-gray-500 dark:bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }}></div>
          <div className="w-2 h-2 bg-gray-500 dark:bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }}></div>
        </div>
      </div>
    </div>
  );
}
