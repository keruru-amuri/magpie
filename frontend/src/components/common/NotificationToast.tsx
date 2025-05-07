'use client';

import React from 'react';
import {
  CheckCircleIcon,
  ExclamationCircleIcon,
  InformationCircleIcon,
  XCircleIcon,
  XMarkIcon
} from '@heroicons/react/24/outline';
import { Notification, NotificationType } from '../../services/notificationService';

interface NotificationToastProps {
  notification: Notification;
  onDismiss: (id: string) => void;
}

export default function NotificationToast({
  notification,
  onDismiss
}: NotificationToastProps) {
  // Handle manual dismiss
  const handleDismiss = () => {
    onDismiss(notification.id);
  };

  // Get icon based on notification type
  const getIcon = (type: NotificationType) => {
    switch (type) {
      case 'info':
        return <InformationCircleIcon className="h-6 w-6 text-blue-400" />;
      case 'success':
        return <CheckCircleIcon className="h-6 w-6 text-green-400" />;
      case 'warning':
        return <ExclamationCircleIcon className="h-6 w-6 text-yellow-400" />;
      case 'error':
        return <XCircleIcon className="h-6 w-6 text-red-400" />;
    }
  };

  // Get background color based on notification type
  const getBgColor = (type: NotificationType) => {
    switch (type) {
      case 'info':
        return 'bg-blue-50 dark:bg-blue-900/30 border-blue-200 dark:border-blue-800';
      case 'success':
        return 'bg-green-50 dark:bg-green-900/30 border-green-200 dark:border-green-800';
      case 'warning':
        return 'bg-yellow-50 dark:bg-yellow-900/30 border-yellow-200 dark:border-yellow-800';
      case 'error':
        return 'bg-red-50 dark:bg-red-900/30 border-red-200 dark:border-red-800';
    }
  };

  // Get text color based on notification type
  const getTextColor = (type: NotificationType) => {
    switch (type) {
      case 'info':
        return 'text-blue-800 dark:text-blue-200';
      case 'success':
        return 'text-green-800 dark:text-green-200';
      case 'warning':
        return 'text-yellow-800 dark:text-yellow-200';
      case 'error':
        return 'text-red-800 dark:text-red-200';
    }
  };

  return (
    <div
      className={`max-w-sm w-full ${getBgColor(notification.type)} border shadow-lg rounded-lg pointer-events-auto overflow-hidden transition-all duration-300 ${
        notification.isExiting ? 'opacity-0 translate-x-full' : 'opacity-100'
      }`}
      role="alert"
      aria-live="assertive"
    >
      <div className="p-4">
        <div className="flex items-start">
          <div className="flex-shrink-0">
            {getIcon(notification.type)}
          </div>
          <div className="ml-3 w-0 flex-1 pt-0.5">
            <p className={`text-sm font-bold ${getTextColor(notification.type)}`}>
              {notification.title}
            </p>
            <p className={`mt-1 text-sm ${getTextColor(notification.type)} opacity-90`}>
              {notification.message}
            </p>
          </div>
          <div className="ml-4 flex-shrink-0 flex">
            <button
              className={`bg-transparent rounded-md inline-flex ${getTextColor(notification.type)} hover:opacity-75 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500`}
              onClick={handleDismiss}
            >
              <span className="sr-only">Close</span>
              <XMarkIcon className="h-5 w-5" aria-hidden="true" />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
