import React from 'react';
import CardBody from './CardBody';

interface CardProps {
  children: React.ReactNode;
  title?: string;
  subtitle?: string;
  footer?: React.ReactNode;
  className?: string;
  noPadding?: boolean;
  bordered?: boolean;
  hoverable?: boolean;
}

export { CardBody };

export default function Card({
  children,
  title,
  subtitle,
  footer,
  className = '',
  noPadding = false,
  bordered = true,
  hoverable = false,
}: CardProps) {
  const baseClasses = 'bg-white dark:bg-gray-800 rounded-lg shadow-sm overflow-hidden';
  const borderClasses = bordered ? 'border border-gray-200 dark:border-gray-700' : '';
  const hoverClasses = hoverable ? 'transition-all duration-200 hover:shadow-md' : '';
  const combinedClasses = `${baseClasses} ${borderClasses} ${hoverClasses} ${className}`;

  return (
    <div className={combinedClasses}>
      {(title || subtitle) && (
        <div className="px-6 py-4 border-b border-gray-200 dark:border-gray-700">
          {title && <h3 className="text-lg font-medium text-gray-900 dark:text-white">{title}</h3>}
          {subtitle && <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">{subtitle}</p>}
        </div>
      )}

      <div className={noPadding ? '' : 'p-6'}>
        {children}
      </div>

      {footer && (
        <div className="px-6 py-4 bg-gray-50 dark:bg-gray-900 border-t border-gray-200 dark:border-gray-700">
          {footer}
        </div>
      )}
    </div>
  );
}
