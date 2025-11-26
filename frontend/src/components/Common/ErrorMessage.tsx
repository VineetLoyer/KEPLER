/**
 * ErrorMessage Component
 * 
 * Task 20: Implement error handling UI
 * - Display validation errors inline
 * - Display API errors with retry option
 * - Handle network failures gracefully
 * 
 * Requirements: 1.5, 11.1, 11.2, 11.4
 */

import React from 'react';
import './ErrorMessage.css';

export interface ErrorMessageProps {
  message: string;
  type?: 'validation' | 'api' | 'network' | 'general';
  onRetry?: () => void;
  onDismiss?: () => void;
}

/**
 * ErrorMessage Component
 * 
 * Displays error messages with appropriate styling and actions.
 * 
 * Requirements: 1.5, 11.1, 11.2, 11.4
 */
export const ErrorMessage: React.FC<ErrorMessageProps> = ({
  message,
  type = 'general',
  onRetry,
  onDismiss,
}) => {
  const getErrorIcon = () => {
    switch (type) {
      case 'validation':
        return '⚠️';
      case 'api':
        return '❌';
      case 'network':
        return '🌐';
      default:
        return '⚠️';
    }
  };

  const getErrorTitle = () => {
    switch (type) {
      case 'validation':
        return 'Validation Error';
      case 'api':
        return 'API Error';
      case 'network':
        return 'Network Error';
      default:
        return 'Error';
    }
  };

  return (
    <div className={`error-message-container error-message-${type}`} role="alert">
      <div className="error-message-content">
        <span className="error-message-icon" aria-hidden="true">
          {getErrorIcon()}
        </span>
        <div className="error-message-text">
          <h4 className="error-message-title">{getErrorTitle()}</h4>
          <p className="error-message-description">{message}</p>
        </div>
      </div>
      
      {(onRetry || onDismiss) && (
        <div className="error-message-actions">
          {onRetry && (
            <button
              className="error-message-button error-message-retry"
              onClick={onRetry}
              aria-label="Retry"
            >
              Retry
            </button>
          )}
          {onDismiss && (
            <button
              className="error-message-button error-message-dismiss"
              onClick={onDismiss}
              aria-label="Dismiss error"
            >
              Dismiss
            </button>
          )}
        </div>
      )}
    </div>
  );
};

export default ErrorMessage;
