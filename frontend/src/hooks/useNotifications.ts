/**
 * Custom hook for notifications
 */

import { useCallback } from 'react';
import notificationService from '../services/notificationService';

export function useNotifications() {
  // Show info notification
  const showInfo = useCallback((
    title: string,
    message: string,
    options?: { autoClose?: boolean; duration?: number }
  ) => {
    return notificationService.showInfo(title, message, options);
  }, []);
  
  // Show success notification
  const showSuccess = useCallback((
    title: string,
    message: string,
    options?: { autoClose?: boolean; duration?: number }
  ) => {
    return notificationService.showSuccess(title, message, options);
  }, []);
  
  // Show warning notification
  const showWarning = useCallback((
    title: string,
    message: string,
    options?: { autoClose?: boolean; duration?: number }
  ) => {
    return notificationService.showWarning(title, message, options);
  }, []);
  
  // Show error notification
  const showError = useCallback((
    title: string,
    message: string,
    options?: { autoClose?: boolean; duration?: number }
  ) => {
    return notificationService.showError(title, message, options);
  }, []);
  
  // Dismiss notification
  const dismiss = useCallback((id: string) => {
    notificationService.dismiss(id);
  }, []);
  
  // Clear all notifications
  const clearAll = useCallback(() => {
    notificationService.clear();
  }, []);
  
  return {
    showInfo,
    showSuccess,
    showWarning,
    showError,
    dismiss,
    clearAll
  };
}
