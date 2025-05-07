/**
 * Notification Service for MAGPIE Platform
 *
 * This service provides notification functionality for displaying alerts,
 * toasts, and other notifications to the user.
 */

// Notification types
export type NotificationType = 'info' | 'success' | 'warning' | 'error';

// Notification interface
export interface Notification {
  id: string;
  type: NotificationType;
  title: string;
  message: string;
  autoClose?: boolean;
  duration?: number;
  timestamp: number;
  isExiting?: boolean;
}

// Notification listeners
type NotificationListener = (notification: Notification) => void;
type CleanupListener = (removedIds: string[]) => void;
const listeners: NotificationListener[] = [];
const cleanupListeners: CleanupListener[] = [];

// Active notifications
let notifications: Notification[] = [];

/**
 * Add a notification listener
 * @param listener Function to call when a notification is added
 * @returns Function to remove the listener
 */
export function addNotificationListener(listener: NotificationListener): () => void {
  listeners.push(listener);
  return () => {
    const index = listeners.indexOf(listener);
    if (index !== -1) {
      listeners.splice(index, 1);
    }
  };
}

/**
 * Add a cleanup listener
 * @param listener Function to call when notifications are removed
 * @returns Function to remove the listener
 */
export function addCleanupListener(listener: CleanupListener): () => void {
  cleanupListeners.push(listener);
  return () => {
    const index = cleanupListeners.indexOf(listener);
    if (index !== -1) {
      cleanupListeners.splice(index, 1);
    }
  };
}

/**
 * Notify all listeners of a new notification
 * @param notification Notification to send
 */
function notifyListeners(notification: Notification): void {
  listeners.forEach(listener => {
    try {
      listener(notification);
    } catch (error) {
      console.error('Error in notification listener:', error);
    }
  });
}

/**
 * Notify all cleanup listeners of removed notifications
 * @param removedIds IDs of removed notifications
 */
function notifyCleanupListeners(removedIds: string[]): void {
  if (removedIds.length === 0) return;

  cleanupListeners.forEach(listener => {
    try {
      listener(removedIds);
    } catch (error) {
      console.error('Error in cleanup listener:', error);
    }
  });
}

/**
 * Show a notification
 * @param type Notification type
 * @param title Notification title
 * @param message Notification message
 * @param options Additional options
 * @returns Notification ID
 */
export function showNotification(
  type: NotificationType,
  title: string,
  message: string,
  options: {
    autoClose?: boolean;
    duration?: number;
  } = {}
): string {
  // Default options
  const { autoClose = true, duration = 5000 } = options;

  // Create notification
  const id = `notification-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
  const notification: Notification = {
    id,
    type,
    title,
    message,
    autoClose,
    duration,
    timestamp: Date.now()
  };

  // Add to notifications
  notifications.push(notification);

  // Notify listeners
  notifyListeners(notification);

  // Auto-close notification
  if (autoClose) {
    setTimeout(() => {
      dismissNotification(id);
    }, duration);
  }

  return id;
}

/**
 * Dismiss a notification
 * @param id Notification ID
 */
export function dismissNotification(id: string): void {
  const index = notifications.findIndex(n => n.id === id);
  if (index !== -1) {
    notifications.splice(index, 1);
    notifyCleanupListeners([id]);
  }
}

/**
 * Get all active notifications
 * @returns Active notifications
 */
export function getNotifications(): Notification[] {
  return [...notifications];
}

/**
 * Clear all notifications
 */
export function clearNotifications(): void {
  const notificationIds = notifications.map(n => n.id);
  notifications = [];
  notifyCleanupListeners(notificationIds);
}

/**
 * Show an info notification
 * @param title Notification title
 * @param message Notification message
 * @param options Additional options
 * @returns Notification ID
 */
export function showInfo(
  title: string,
  message: string,
  options?: { autoClose?: boolean; duration?: number }
): string {
  return showNotification('info', title, message, options);
}

/**
 * Show a success notification
 * @param title Notification title
 * @param message Notification message
 * @param options Additional options
 * @returns Notification ID
 */
export function showSuccess(
  title: string,
  message: string,
  options?: { autoClose?: boolean; duration?: number }
): string {
  return showNotification('success', title, message, options);
}

/**
 * Show a warning notification
 * @param title Notification title
 * @param message Notification message
 * @param options Additional options
 * @returns Notification ID
 */
export function showWarning(
  title: string,
  message: string,
  options?: { autoClose?: boolean; duration?: number }
): string {
  return showNotification('warning', title, message, options);
}

/**
 * Show an error notification
 * @param title Notification title
 * @param message Notification message
 * @param options Additional options
 * @returns Notification ID
 */
export function showError(
  title: string,
  message: string,
  options?: { autoClose?: boolean; duration?: number }
): string {
  return showNotification('error', title, message, { autoClose: false, ...options });
}

// Export notification service
const notificationService = {
  addListener: addNotificationListener,
  addCleanupListener,
  show: showNotification,
  dismiss: dismissNotification,
  getAll: getNotifications,
  clear: clearNotifications,
  showInfo,
  showSuccess,
  showWarning,
  showError
};

export default notificationService;
