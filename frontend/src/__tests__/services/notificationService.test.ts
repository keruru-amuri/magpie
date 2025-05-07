/**
 * Notification Service Tests
 * 
 * This file contains tests for the notification service.
 */

import notificationService, { Notification } from '../../services/notificationService';

describe('Notification Service', () => {
  // Clear notifications before each test
  beforeEach(() => {
    notificationService.clear();
  });

  describe('show', () => {
    test('should show notification', () => {
      // Show notification
      const id = notificationService.show('info', 'Test Title', 'Test Message');

      // Get notifications
      const notifications = notificationService.getAll();

      // Check notification was added
      expect(notifications).toHaveLength(1);
      expect(notifications[0]).toEqual({
        id,
        type: 'info',
        title: 'Test Title',
        message: 'Test Message',
        autoClose: true,
        duration: 5000,
        timestamp: expect.any(Number)
      });
    });

    test('should show notification with custom options', () => {
      // Show notification with custom options
      const id = notificationService.show('warning', 'Test Title', 'Test Message', {
        autoClose: false,
        duration: 10000
      });

      // Get notifications
      const notifications = notificationService.getAll();

      // Check notification was added with custom options
      expect(notifications).toHaveLength(1);
      expect(notifications[0]).toEqual({
        id,
        type: 'warning',
        title: 'Test Title',
        message: 'Test Message',
        autoClose: false,
        duration: 10000,
        timestamp: expect.any(Number)
      });
    });
  });

  describe('dismiss', () => {
    test('should dismiss notification', () => {
      // Show notification
      const id = notificationService.show('info', 'Test Title', 'Test Message');

      // Check notification was added
      expect(notificationService.getAll()).toHaveLength(1);

      // Dismiss notification
      notificationService.dismiss(id);

      // Check notification was removed
      expect(notificationService.getAll()).toHaveLength(0);
    });
  });

  describe('clear', () => {
    test('should clear all notifications', () => {
      // Show multiple notifications
      notificationService.show('info', 'Test Title 1', 'Test Message 1');
      notificationService.show('success', 'Test Title 2', 'Test Message 2');
      notificationService.show('warning', 'Test Title 3', 'Test Message 3');

      // Check notifications were added
      expect(notificationService.getAll()).toHaveLength(3);

      // Clear notifications
      notificationService.clear();

      // Check all notifications were removed
      expect(notificationService.getAll()).toHaveLength(0);
    });
  });

  describe('listeners', () => {
    test('should notify listeners when notification is added', () => {
      // Set up listener
      const listener = jest.fn();
      const removeListener = notificationService.addListener(listener);

      // Show notification
      const id = notificationService.show('info', 'Test Title', 'Test Message');

      // Check listener was called with notification
      expect(listener).toHaveBeenCalledWith({
        id,
        type: 'info',
        title: 'Test Title',
        message: 'Test Message',
        autoClose: true,
        duration: 5000,
        timestamp: expect.any(Number)
      });

      // Remove listener
      removeListener();

      // Show another notification
      notificationService.show('success', 'Test Title 2', 'Test Message 2');

      // Check listener was not called again
      expect(listener).toHaveBeenCalledTimes(1);
    });
  });

  describe('helper methods', () => {
    test('showInfo should show info notification', () => {
      // Show info notification
      const id = notificationService.showInfo('Test Title', 'Test Message');

      // Get notifications
      const notifications = notificationService.getAll();

      // Check notification was added
      expect(notifications).toHaveLength(1);
      expect(notifications[0].type).toBe('info');
    });

    test('showSuccess should show success notification', () => {
      // Show success notification
      const id = notificationService.showSuccess('Test Title', 'Test Message');

      // Get notifications
      const notifications = notificationService.getAll();

      // Check notification was added
      expect(notifications).toHaveLength(1);
      expect(notifications[0].type).toBe('success');
    });

    test('showWarning should show warning notification', () => {
      // Show warning notification
      const id = notificationService.showWarning('Test Title', 'Test Message');

      // Get notifications
      const notifications = notificationService.getAll();

      // Check notification was added
      expect(notifications).toHaveLength(1);
      expect(notifications[0].type).toBe('warning');
    });

    test('showError should show error notification', () => {
      // Show error notification
      const id = notificationService.showError('Test Title', 'Test Message');

      // Get notifications
      const notifications = notificationService.getAll();

      // Check notification was added
      expect(notifications).toHaveLength(1);
      expect(notifications[0].type).toBe('error');
      expect(notifications[0].autoClose).toBe(false);
    });
  });
});
