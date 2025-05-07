import React from 'react';
import Link from 'next/link';
import Card from '../common/Card';
import Button from '../common/Button';

interface AgentCardProps {
  title: string;
  description: string;
  icon: React.ReactNode;
  href: string;
  capabilities?: string[];
  className?: string;
}

export default function AgentCard({
  title,
  description,
  icon,
  href,
  capabilities = [],
  className = '',
}: AgentCardProps) {
  return (
    <Card 
      className={`h-full flex flex-col ${className}`}
      hoverable
    >
      <div className="flex items-start mb-4">
        <div className="flex-shrink-0 h-12 w-12 rounded-md bg-primary-100 dark:bg-primary-900 flex items-center justify-center text-primary-600 dark:text-primary-300 mr-4">
          {icon}
        </div>
        <div>
          <h3 className="text-lg font-medium text-gray-900 dark:text-white">{title}</h3>
          <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">{description}</p>
        </div>
      </div>
      
      {capabilities.length > 0 && (
        <div className="mt-2 mb-4">
          <h4 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">Capabilities:</h4>
          <ul className="space-y-1">
            {capabilities.map((capability, index) => (
              <li key={index} className="flex items-start">
                <svg className="h-5 w-5 text-green-500 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                </svg>
                <span className="text-sm text-gray-600 dark:text-gray-400">{capability}</span>
              </li>
            ))}
          </ul>
        </div>
      )}
      
      <div className="mt-auto pt-4">
        <Button 
          href={href}
          variant="primary"
          fullWidth
          rightIcon={
            <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14 5l7 7m0 0l-7 7m7-7H3" />
            </svg>
          }
        >
          Open Agent
        </Button>
      </div>
    </Card>
  );
}
