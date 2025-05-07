'use client';

import React from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';

export default function TestNavigation() {
  const pathname = usePathname();
  
  // Define test pages
  const testPages = [
    { path: '/test-visualizations', label: 'Test Visualizations' },
    { path: '/test-history', label: 'Test Conversation History' },
    { path: '/history', label: 'Conversation History Page' }
  ];
  
  // Check if current path is a test page
  const isTestPage = testPages.some(page => pathname === page.path);
  
  // If not a test page, don't render the navigation
  if (!isTestPage && !pathname.startsWith('/test-')) {
    return null;
  }
  
  return (
    <div className="bg-blue-600 text-white p-2">
      <div className="container mx-auto flex items-center justify-between">
        <div className="font-bold">MAGPIE Test Pages</div>
        
        <nav className="flex space-x-4">
          {testPages.map((page) => (
            <Link
              key={page.path}
              href={page.path}
              className={`px-3 py-1 rounded-md ${
                pathname === page.path
                  ? 'bg-blue-800 text-white'
                  : 'text-blue-100 hover:bg-blue-700'
              }`}
            >
              {page.label}
            </Link>
          ))}
        </nav>
      </div>
    </div>
  );
}
