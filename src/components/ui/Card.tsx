import { HTMLAttributes, ReactNode } from 'react';

interface CardProps extends HTMLAttributes<HTMLDivElement> {
  children: ReactNode;
  variant?: 'default' | 'bordered' | 'elevated';
}

const Card = ({ children, variant = 'default', className = '', ...props }: CardProps) => {
  const baseClasses = 'bg-white dark:bg-gray-800 rounded-lg overflow-hidden';
  
  const variantClasses = {
    default: 'shadow',
    bordered: 'border border-gray-200 dark:border-gray-700',
    elevated: 'shadow-lg',
  };
  
  const cardClasses = `${baseClasses} ${variantClasses[variant]} ${className}`;
  
  return (
    <div className={cardClasses} {...props}>
      {children}
    </div>
  );
};

export const CardHeader = ({ children, className = '', ...props }: HTMLAttributes<HTMLDivElement>) => {
  return (
    <div className={`px-6 py-4 border-b border-gray-200 dark:border-gray-700 ${className}`} {...props}>
      {children}
    </div>
  );
};

export const CardBody = ({ children, className = '', ...props }: HTMLAttributes<HTMLDivElement>) => {
  return (
    <div className={`px-6 py-4 ${className}`} {...props}>
      {children}
    </div>
  );
};

export const CardFooter = ({ children, className = '', ...props }: HTMLAttributes<HTMLDivElement>) => {
  return (
    <div className={`px-6 py-4 border-t border-gray-200 dark:border-gray-700 ${className}`} {...props}>
      {children}
    </div>
  );
};

export default Card;
