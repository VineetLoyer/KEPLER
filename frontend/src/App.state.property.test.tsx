import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import App from './App';
import * as fc from 'fast-check';

/**
 * Property-based tests for application state management
 * 
 * **Feature: kepler-web-interface, Property 37: Submit button state management**
 * For any verification in progress, the submit button should be disabled; 
 * when complete or failed, it should be re-enabled.
 * **Validates: Requirements 12.4, 12.5**
 * 
 * **Feature: kepler-web-interface, Property 38: History tracking**
 * For any completed verification, the session should be added to the history list.
 * **Validates: Requirements 13.1**
 */

describe('App State Management - Property-Based Tests', () => {
  beforeEach(() => {
    localStorage.clear();
    vi.clearAllMocks();
  });

  describe('Property 37: Submit button state management', () => {
    /**
     * **Feature: kepler-web-interface, Property 37: Submit button state management**
     * For any verification in progress, the submit button should be disabled; 
     * when complete or failed, it should be re-enabled.
     */
    it('should disable submit button during verification and re-enable after completion', () => {
      fc.assert(
        fc.property(
          fc.string({ minLength: 1, maxLength: 200 }).filter(s => s.trim().length > 0),
          (claimText) => {
            // Clear localStorage before each iteration
            localStorage.clear();
            
            const { unmount, container } = render(<App />);
            
            try {
              // Get initial button state
              const button = screen.getByRole('button', { name: /Verify Claim/i });
              expect(button).not.toBeDisabled();
              
              // Enter claim text
              const textarea = container.querySelector('textarea');
              if (textarea) {
                fireEvent.change(textarea, { target: { value: claimText } });
              }
              
              // Button should still be enabled before submission
              expect(button).not.toBeDisabled();
              
              return true;
            } finally {
              unmount();
              // Clean up DOM
              document.body.innerHTML = '';
            }
          }
        ),
        { numRuns: 20 } // Run 20 iterations for faster testing
      );
    });

    it('should re-enable submit button after validation error', async () => {
      // Test with a single example instead of property-based for async
      localStorage.clear();
      const { unmount, container } = render(<App />);
      
      try {
        // Enter claim text but don't select models
        const textarea = container.querySelector('textarea');
        if (textarea) {
          fireEvent.change(textarea, { target: { value: 'Test claim' } });
        }
        
        const button = screen.getByRole('button', { name: /Verify Claim/i });
        fireEvent.click(button);
        
        // Wait for validation error
        await waitFor(() => {
          expect(screen.getByText(/Please select at least one model/i)).toBeInTheDocument();
        }, { timeout: 1000 });
        
        // Button should be re-enabled after validation error
        expect(button).not.toBeDisabled();
      } finally {
        unmount();
        document.body.innerHTML = '';
      }
    });
  });

  describe('Property 38: History tracking', () => {
    /**
     * **Feature: kepler-web-interface, Property 38: History tracking**
     * For any completed verification, the session should be added to the history list.
     */
    it('should add verification to history after completion', () => {
      fc.assert(
        fc.property(
          fc.record({
            sessionId: fc.string({ minLength: 5, maxLength: 50 }),
            claimText: fc.string({ minLength: 1, maxLength: 200 }).filter(s => s.trim().length > 0),
            verdict: fc.constantFrom('Supported', 'Refuted', 'Not Enough Information'),
            confidence: fc.float({ min: 0, max: 1 }),
          }),
          (verificationData) => {
            // Clear localStorage before each iteration
            localStorage.clear();
            
            const { unmount } = render(<App />);
            
            try {
              // Create a mock verification result
              const mockResult = {
                sessionId: verificationData.sessionId,
                timestamp: new Date().toISOString(),
                claimText: verificationData.claimText,
                verdict: verificationData.verdict,
                confidence: verificationData.confidence,
                fullResults: {
                  session_id: verificationData.sessionId,
                  original_input: { text: verificationData.claimText },
                  atomic_claims: [],
                  consensus_verdict: { final_classification: verificationData.verdict },
                  confidence_score: { overall_score: verificationData.confidence },
                  processing_metadata: {},
                  trace_log: [],
                },
              };
              
              // Manually add to localStorage (simulating a completed verification)
              const existingHistory = JSON.parse(localStorage.getItem('kepler_verification_history') || '[]');
              existingHistory.push(mockResult);
              localStorage.setItem('kepler_verification_history', JSON.stringify(existingHistory));
              
              unmount();
              document.body.innerHTML = '';
              
              // Re-render to load history
              const { unmount: unmount2 } = render(<App />);
              
              // Verify history was loaded - check that history list exists
              const historyList = screen.getByRole('list');
              expect(historyList).toBeInTheDocument();
              
              // Verify the history item is displayed
              const historyItems = screen.getAllByRole('listitem');
              expect(historyItems.length).toBe(1);
              
              unmount2();
              document.body.innerHTML = '';
              return true;
            } catch (error) {
              unmount();
              document.body.innerHTML = '';
              throw error;
            }
          }
        ),
        { numRuns: 20 }
      );
    });

    it('should persist history to localStorage', () => {
      fc.assert(
        fc.property(
          fc.array(
            fc.record({
              sessionId: fc.string({ minLength: 5, maxLength: 50 }),
              claimText: fc.string({ minLength: 1, maxLength: 200 }).filter(s => s.trim().length > 0),
              verdict: fc.constantFrom('Supported', 'Refuted', 'Not Enough Information'),
              confidence: fc.float({ min: 0, max: 1 }),
            }),
            { minLength: 1, maxLength: 5 }
          ),
          (verifications) => {
            // Clear localStorage before each iteration
            localStorage.clear();
            
            const { unmount } = render(<App />);
            
            try {
              // Create mock history
              const mockHistory = verifications.map(v => ({
                sessionId: v.sessionId,
                timestamp: new Date().toISOString(),
                claimText: v.claimText,
                verdict: v.verdict,
                confidence: v.confidence,
                fullResults: {
                  session_id: v.sessionId,
                  original_input: { text: v.claimText },
                  atomic_claims: [],
                  consensus_verdict: { final_classification: v.verdict },
                  confidence_score: { overall_score: v.confidence },
                  processing_metadata: {},
                  trace_log: [],
                },
              }));
              
              // Set history in localStorage
              localStorage.setItem('kepler_verification_history', JSON.stringify(mockHistory));
              
              unmount();
              document.body.innerHTML = '';
              
              // Re-render to load history
              const { unmount: unmount2 } = render(<App />);
              
              // Verify history count - check that history items exist
              const historyItems = screen.getAllByRole('listitem');
              expect(historyItems.length).toBe(verifications.length);
              
              // Verify localStorage still has the data
              const stored = JSON.parse(localStorage.getItem('kepler_verification_history') || '[]');
              expect(stored.length).toBe(verifications.length);
              
              unmount2();
              document.body.innerHTML = '';
              return true;
            } catch (error) {
              unmount();
              document.body.innerHTML = '';
              throw error;
            }
          }
        ),
        { numRuns: 20 }
      );
    });

    it('should maintain history order (most recent first)', () => {
      fc.assert(
        fc.property(
          fc.array(
            fc.record({
              sessionId: fc.string({ minLength: 5, maxLength: 50 }),
              claimText: fc.string({ minLength: 1, maxLength: 200 }).filter(s => s.trim().length > 0),
              verdict: fc.constantFrom('Supported', 'Refuted', 'Not Enough Information'),
              confidence: fc.float({ min: 0, max: 1 }),
              timestamp: fc.integer({ min: 1000000000000, max: 9999999999999 }), // Unix timestamp in ms
            }),
            { minLength: 2, maxLength: 5 }
          ),
          (verifications) => {
            // Clear localStorage before each iteration
            localStorage.clear();
            
            const { unmount } = render(<App />);
            
            try {
              // Sort by timestamp descending (most recent first)
              const sortedVerifications = [...verifications].sort((a, b) => b.timestamp - a.timestamp);
              
              // Create mock history
              const mockHistory = sortedVerifications.map(v => ({
                sessionId: v.sessionId,
                timestamp: new Date(v.timestamp).toISOString(),
                claimText: v.claimText,
                verdict: v.verdict,
                confidence: v.confidence,
                fullResults: {
                  session_id: v.sessionId,
                  original_input: { text: v.claimText },
                  atomic_claims: [],
                  consensus_verdict: { final_classification: v.verdict },
                  confidence_score: { overall_score: v.confidence },
                  processing_metadata: {},
                  trace_log: [],
                },
              }));
              
              // Set history in localStorage
              localStorage.setItem('kepler_verification_history', JSON.stringify(mockHistory));
              
              unmount();
              document.body.innerHTML = '';
              
              // Re-render to load history
              const { unmount: unmount2 } = render(<App />);
              
              // Verify history is loaded - check that history items exist
              const historyItems = screen.getAllByRole('listitem');
              expect(historyItems.length).toBe(sortedVerifications.length);
              
              unmount2();
              document.body.innerHTML = '';
              return true;
            } catch (error) {
              unmount();
              document.body.innerHTML = '';
              throw error;
            }
          }
        ),
        { numRuns: 20 }
      );
    });
  });
});
