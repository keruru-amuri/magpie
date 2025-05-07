'use client';

import React, { useEffect, useState } from 'react';
import NotificationToast from './NotificationToast';
import notificationService, { Notification } from '../../services/notificationService';

interface NotificationContainerProps {
  position?: 'top-right' | 'top-left' | 'bottom-right' | 'bottom-left';
  maxNotifications?: number;
}

export default function NotificationContainer({
  position = 'top-right',
  maxNotifications = 5
}: NotificationContainerProps) {
  const [notifications, setNotifications] = useState<Notification[]>([]);
  // Create a ref to track notifications that are exiting
  const exitingNotificationsRef = React.useRef(new Set<string>());

  // Position classes
  const positionClasses = {
    'top-right': 'top-0 right-0',
    'top-left': 'top-0 left-0',
    'bottom-right': 'bottom-0 right-0',
    'bottom-left': 'bottom-0 left-0'
  };

  // Listen for notifications
  useEffect(() => {
    // Add notification listener
    const removeListener = notificationService.addListener((notification) => {
      setNotifications(prev => {
        // Check if notification already exists
        const exists = prev.some(n => n.id === notification.id);

        if (exists) return prev;

        // Add new notification
        const updated = [notification, ...prev];

        // Limit number of notifications
        if (updated.length > maxNotifications) {
          return updated.slice(0, maxNotifications);
        }

        return updated;
      });
    });

    // Add cleanup listener
    const removeCleanupListener = notificationService.addCleanupListener((removedIds) => {
      if (removedIds.length === 0) return;

      // Mark notifications as exiting
      setNotifications(prev =>
        prev.map(n =>
          removedIds.includes(n.id)
            ? { ...n, isExiting: true }
            : n
        )
      );

      // Remove from state after animation completes
      setTimeout(() => {
        setNotifications(prev =>
          prev.filter(n => !removedIds.includes(n.id))
        );
      }, 300); // Match animation duration
    });

    return () => {
      removeListener();
      removeCleanupListener();
    };
  }, [maxNotifications]);

  // Handle dismiss
  const handleDismiss = (id: string) => {
    // First mark the notification as exiting for animation
    setNotifications(prev =>
      prev.map(n => n.id === id ? { ...n, isExiting: true } : n)
    );

    // Remove from service
    notificationService.dismiss(id);

    // Remove from state after animation completes
    setTimeout(() => {
      setNotifications(prev => prev.filter(n => n.id !== id));
    }, 300); // Match animation duration
  };

  // If no notifications, don't render anything
  if (notifications.length === 0) {
    return null;
  }

  return (
    <div
      className={`fixed z-50 p-4 max-h-screen overflow-hidden pointer-events-none ${positionClasses[position]}`}
      aria-live="assertive"
    >
      <div className="flex flex-col space-y-6 pointer-events-none">
        {notifications.map(notification => (
          <div key={notification.id} className="pointer-events-auto w-80">
            <NotificationToast
              notification={notification}
              onDismiss={handleDismiss}
            />
          </div>
        ))}
      </div>
    </div>
  );
}
