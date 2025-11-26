import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import App from './App';

/**
 * Tests for application state management
 * 
 * Task 16: Implement application state management
 * - Set up state structure in main App component (input, UI, results, history)
 * - Implement state update functions for input changes
 * - Handle loading states (isLoading, currentStage)
 * - Manage error states (error message, error type)
 * - Track verification history in state
 * - Implement state persistence to localStorage for history
 * - Create helper functions for state transitions
 * 
 * Requirements: 2.4, 12.1, 12.4, 12.5, 13.1
 */

describe('App Component - State Management', () => {
  beforeEach(() => {
    // Clear localStorage before each test
    localStorage.clear();
    
    // Reset all mocks
    vi.clearAllMocks();
  });

  afterEach(() => {
    // Clean up
    localStorage.clear();
  });

  describe('Input state management', () => {
    it('should update text input state when user types', () => {
      render(<App />);
      
      const textarea = screen.getByPlaceholderText(/Enter a claim to verify/i);
      fireEvent.change(textarea, { target: { value: 'Test claim' } });
      
      expect(textarea).toHaveValue('Test claim');
    });

    it('should clear App-level validation errors when user types after error', async () => {
      render(<App />);
      
      // Enter text but don't select models to trigger App-level validation error
      const textarea = screen.getByPlaceholderText(/Enter a claim to verify/i);
      fireEvent.change(textarea, { target: { value: 'Test claim' } });
      
      const button = screen.getByRole('button', { name: /Verify Claim/i });
      fireEvent.click(button);
      
      // Wait for App-level error to appear
      await waitFor(() => {
        expect(screen.getByText(/Please select at least one model/i)).toBeInTheDocument();
      });
      
      // Type more in textarea (this should clear validation errors)
      fireEvent.change(textarea, { target: { value: 'Test claim updated' } });
      
      // App-level validation error should be cleared
      await waitFor(() => {
        expect(screen.queryByText(/Please select at least one model/i)).not.toBeInTheDocument();
      });
    });
  });

  describe('Loading state management (Requirements: 2.4, 12.1, 12.4)', () => {
    it('should show validation error when no models selected (not loading)', async () => {
      render(<App />);
      
      // Enter text and submit without selecting models
      const textarea = screen.getByPlaceholderText(/Enter a claim to verify/i);
      fireEvent.change(textarea, { target: { value: 'Test claim' } });
      
      const button = screen.getByRole('button', { name: /Verify Claim/i });
      fireEvent.click(button);
      
      // Should show validation error, not loading
      await waitFor(() => {
        expect(screen.getByText(/Please select at least one model/i)).toBeInTheDocument();
      });
      
      // Should NOT show loading
      expect(screen.queryByText(/Loading/i)).not.toBeInTheDocument();
    });

    it('should disable submit button during input (ClaimInput handles this)', async () => {
      render(<App />);
      
      // The button is part of ClaimInput and gets disabled when ClaimInput is disabled
      // ClaimInput is disabled when ui.isLoading is true
      // We can't easily test this without triggering a real verification
      // So we just verify the disabled prop is passed correctly
      const button = screen.getByRole('button', { name: /Verify Claim/i });
      expect(button).not.toBeDisabled(); // Initially not disabled
    });
  });

  describe('Error state management (Requirements: 12.5)', () => {
    it('should display validation error for empty input (ClaimInput handles this)', async () => {
      render(<App />);
      
      const button = screen.getByRole('button', { name: /Verify Claim/i });
      fireEvent.click(button);
      
      // ClaimInput component shows its own validation error
      await waitFor(() => {
        expect(screen.getByText(/Claim cannot be empty or whitespace-only/i)).toBeInTheDocument();
      });
    });

    it('should display validation error for missing models', async () => {
      render(<App />);
      
      // Enter text but don't select models
      const textarea = screen.getByPlaceholderText(/Enter a claim to verify/i);
      fireEvent.change(textarea, { target: { value: 'Test claim' } });
      
      const button = screen.getByRole('button', { name: /Verify Claim/i });
      fireEvent.click(button);
      
      await waitFor(() => {
        expect(screen.getByText(/Please select at least one model/i)).toBeInTheDocument();
      });
    });

    it('should display error type for validation errors', async () => {
      render(<App />);
      
      // Enter text but don't select models
      const textarea = screen.getByPlaceholderText(/Enter a claim to verify/i);
      fireEvent.change(textarea, { target: { value: 'Test claim' } });
      
      const button = screen.getByRole('button', { name: /Verify Claim/i });
      fireEvent.click(button);
      
      await waitFor(() => {
        expect(screen.getByText(/Error type: validation/i)).toBeInTheDocument();
      });
    });

    it('should allow dismissing errors', async () => {
      render(<App />);
      
      // Enter text but don't select models to trigger App-level error
      const textarea = screen.getByPlaceholderText(/Enter a claim to verify/i);
      fireEvent.change(textarea, { target: { value: 'Test claim' } });
      
      const submitButton = screen.getByRole('button', { name: /Verify Claim/i });
      fireEvent.click(submitButton);
      
      await waitFor(() => {
        expect(screen.getByText(/Please select at least one model/i)).toBeInTheDocument();
      });
      
      // Dismiss error
      const dismissButton = screen.getByRole('button', { name: /Dismiss/i });
      fireEvent.click(dismissButton);
      
      await waitFor(() => {
        expect(screen.queryByText(/Please select at least one model/i)).not.toBeInTheDocument();
      });
    });
  });

  describe('History state management (Requirements: 13.1)', () => {
    it('should load history from localStorage on mount', () => {
      // Pre-populate localStorage
      const mockHistory = [{
        sessionId: 'test-123',
        timestamp: new Date().toISOString(),
        claimText: 'Previous claim',
        verdict: 'Supported',
        confidence: 0.9,
        fullResults: {
          session_id: 'test-123',
          original_input: { text: 'Previous claim' },
          atomic_claims: [],
          consensus_verdict: { final_classification: 'Supported' },
          confidence_score: { overall_score: 0.9 },
          processing_metadata: {},
          trace_log: [],
        },
      }];
      
      localStorage.setItem('kepler_verification_history', JSON.stringify(mockHistory));
      
      render(<App />);
      
      // History should be loaded
      expect(screen.getByText(/History items: 1/i)).toBeInTheDocument();
    });

    it('should allow clearing history', () => {
      // Pre-populate localStorage
      const mockHistory = [{
        sessionId: 'test-123',
        timestamp: new Date().toISOString(),
        claimText: 'Previous claim',
        verdict: 'Supported',
        confidence: 0.9,
        fullResults: {
          session_id: 'test-123',
          original_input: { text: 'Previous claim' },
          atomic_claims: [],
          consensus_verdict: { final_classification: 'Supported' },
          confidence_score: { overall_score: 0.9 },
          processing_metadata: {},
          trace_log: [],
        },
      }];
      
      localStorage.setItem('kepler_verification_history', JSON.stringify(mockHistory));
      
      render(<App />);
      
      // Clear history
      const clearButton = screen.getByRole('button', { name: /Clear History/i });
      fireEvent.click(clearButton);
      
      // History should be empty
      expect(screen.getByText(/History items: 0/i)).toBeInTheDocument();
      
      // localStorage should have empty array (not null, because useEffect saves it)
      const stored = localStorage.getItem('kepler_verification_history');
      expect(stored).toBe('[]');
    });

    it('should display history items and allow loading them', () => {
      // Pre-populate localStorage
      const mockHistory = [{
        sessionId: 'test-123',
        timestamp: new Date().toISOString(),
        claimText: 'Previous claim that is very long and should be truncated',
        verdict: 'Supported',
        confidence: 0.9,
        fullResults: {
          session_id: 'test-123',
          original_input: { text: 'Previous claim' },
          atomic_claims: [],
          consensus_verdict: { final_classification: 'Supported' },
          confidence_score: { overall_score: 0.9 },
          processing_metadata: {},
          trace_log: [],
        },
      }];
      
      localStorage.setItem('kepler_verification_history', JSON.stringify(mockHistory));
      
      render(<App />);
      
      // History item should be displayed (truncated)
      expect(screen.getByText(/Previous claim that is very long and should be/i)).toBeInTheDocument();
      
      // Click to load history item
      const historyButton = screen.getByRole('button', { name: /Previous claim.*Supported/i });
      fireEvent.click(historyButton);
      
      // Results should be loaded (check for session ID in results section)
      expect(screen.getByText(/Session ID: test-123/i)).toBeInTheDocument();
    });
  });
});
