import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import * as fc from 'fast-check';
import { History } from './History';
import type { HistoryItemData } from './History';
import type { VerdictType, VerificationResult } from '../../types/verification';

/**
 * Property-Based Tests for History Component
 * 
 * Task 17.1: Write property tests for history
 * - Property 39: History item content
 * - Property 40: History item interaction
 * 
 * Requirements: 13.2, 13.3, 13.4, 13.5
 * 
 * These tests use fast-check to generate random inputs and verify
 * that the component behaves correctly across all possible inputs.
 */

// Arbitraries (generators) for test data

const verdictTypeArbitrary = fc.constantFrom<VerdictType>(
  'Supported',
  'Refuted',
  'Not Enough Information'
);

const verificationResultArbitrary = fc.record({
  session_id: fc.uuid(),
  original_input: fc.constant({}),
  atomic_claims: fc.constant([]),
  consensus_verdict: fc.record({
    final_classification: verdictTypeArbitrary,
    consensus_justification: fc.string({ minLength: 20, maxLength: 200 }),
    individual_verdicts: fc.constant([]),
    agreement_level: fc.double({ min: 0, max: 1 }),
  }),
  confidence_score: fc.record({
    overall_score: fc.double({ min: 0, max: 1, noNaN: true }),
    source_reliability: fc.double({ min: 0, max: 1, noNaN: true }),
    model_agreement: fc.double({ min: 0, max: 1, noNaN: true }),
    evidence_recency: fc.double({ min: 0, max: 1, noNaN: true }),
    structured_justification: fc.record({
      summary: fc.string(),
      key_evidence: fc.constant([]),
      reasoning_chain: fc.record({
        steps: fc.constant([]),
        agreements: fc.constant([]),
        conflicts: fc.constant([]),
        gaps: fc.constant([]),
      }),
      source_links: fc.constant([]),
    }),
  }),
  processing_metadata: fc.constant({}),
  trace_log: fc.constant([]),
}) as fc.Arbitrary<VerificationResult>;

const historyItemArbitrary = fc.uuid().chain(sessionId =>
  fc.record({
    sessionId: fc.constant(sessionId),
    timestamp: fc.integer({ min: Date.parse('2020-01-01'), max: Date.now() }).map(ms => new Date(ms).toISOString()),
    claimText: fc.string({ minLength: 10, maxLength: 500 }),
    verdict: verdictTypeArbitrary,
    confidence: fc.double({ min: 0, max: 1, noNaN: true }),
    fullResults: fc.record({
      session_id: fc.constant(sessionId),
      original_input: fc.constant({}),
      atomic_claims: fc.constant([]),
      consensus_verdict: fc.record({
        final_classification: verdictTypeArbitrary,
        consensus_justification: fc.string({ minLength: 20, maxLength: 200 }),
        individual_verdicts: fc.constant([]),
        agreement_level: fc.double({ min: 0, max: 1 }),
      }),
      confidence_score: fc.record({
        overall_score: fc.double({ min: 0, max: 1, noNaN: true }),
        source_reliability: fc.double({ min: 0, max: 1, noNaN: true }),
        model_agreement: fc.double({ min: 0, max: 1, noNaN: true }),
        evidence_recency: fc.double({ min: 0, max: 1, noNaN: true }),
        structured_justification: fc.record({
          summary: fc.string(),
          key_evidence: fc.constant([]),
          reasoning_chain: fc.record({
            steps: fc.constant([]),
            agreements: fc.constant([]),
            conflicts: fc.constant([]),
            gaps: fc.constant([]),
          }),
          source_links: fc.constant([]),
        }),
      }),
      processing_metadata: fc.constant({}),
      trace_log: fc.constant([]),
    }) as fc.Arbitrary<VerificationResult>,
  }) as fc.Arbitrary<HistoryItemData>
);

const historyListArbitrary = fc.array(historyItemArbitrary, { minLength: 1, maxLength: 20 });

describe('History Property-Based Tests', () => {
  /**
   * **Feature: kepler-web-interface, Property 39: History item content**
   * 
   * For any history item, it should display claim text, verdict, and timestamp.
   * 
   * This property verifies that every history item in the list displays all
   * required information: the claim text (possibly truncated), the verdict
   * classification, and a formatted timestamp.
   * 
   * **Validates: Requirements 13.2, 13.3, 13.4**
   */
  it('Property 39: should display claim text, verdict, and timestamp for all history items', () => {
    fc.assert(
      fc.property(
        historyListArbitrary,
        (historyItems) => {
          const mockOnItemClick = () => {};
          const mockOnClearHistory = () => {};

          const { unmount, container } = render(
            <History
              history={historyItems}
              onItemClick={mockOnItemClick}
              onClearHistory={mockOnClearHistory}
            />
          );

          // Verify that each history item displays all required content:
          
          // Get all history item buttons
          const historyItemButtons = container.querySelectorAll('.history-item');
          
          // Verify the number of history items matches
          expect(historyItemButtons.length).toBe(historyItems.length);
          
          // Check each rendered history item
          historyItemButtons.forEach((button, index) => {
            const item = historyItems[index];
            
            // 1. Claim text should be present (possibly truncated)
            const claimDiv = button.querySelector('.history-item-claim');
            expect(claimDiv).toBeInTheDocument();
            expect(claimDiv?.textContent).toBeTruthy();
            
            // The claim text might be truncated, so we check it's not empty
            const displayedClaim = claimDiv?.textContent || '';
            expect(displayedClaim.length).toBeGreaterThan(0);
            
            // If the original claim is short enough, it should match exactly
            // Otherwise, it should be a prefix of the original
            if (item.claimText.length <= 80) {
              expect(displayedClaim.trim()).toBe(item.claimText.trim());
            } else {
              // Should be truncated with "..."
              expect(displayedClaim).toContain('...');
            }
            
            // 2. Verdict should be displayed
            const verdictSpan = button.querySelector('.history-item-verdict');
            expect(verdictSpan).toBeInTheDocument();
            expect(verdictSpan?.textContent).toBe(item.verdict);
            
            // 3. Verdict should have appropriate styling class
            const verdictClass = verdictSpan?.className || '';
            expect(verdictClass).toMatch(/verdict-(supported|refuted|nei)/);
            
            // 4. Timestamp should be displayed
            const timestampDiv = button.querySelector('.history-item-timestamp');
            expect(timestampDiv).toBeInTheDocument();
            expect(timestampDiv?.textContent).toBeTruthy();
            expect(timestampDiv?.textContent?.length).toBeGreaterThan(0);
            
            // 5. Confidence score should be displayed
            const confidenceSpan = button.querySelector('.history-item-confidence');
            expect(confidenceSpan).toBeInTheDocument();
            
            // Confidence should be formatted as percentage
            const confidenceText = confidenceSpan?.textContent || '';
            expect(confidenceText).toMatch(/%$/);
            
            // Confidence value should be in valid range
            const confidenceValue = parseFloat(confidenceText.replace('%', ''));
            expect(confidenceValue).toBeGreaterThanOrEqual(0);
            expect(confidenceValue).toBeLessThanOrEqual(100);
          });

          unmount();
        }
      ),
      { numRuns: 100 }
    );
  });

  /**
   * **Feature: kepler-web-interface, Property 40: History item interaction**
   * 
   * For any history item click, the full verification results should be displayed.
   * 
   * This property verifies that clicking on any history item triggers the
   * onItemClick callback with the correct history item data, which should
   * then display the full verification results.
   * 
   * **Validates: Requirements 13.5**
   */
  it('Property 40: should trigger callback with full results when history item is clicked', () => {
    fc.assert(
      fc.property(
        historyListArbitrary,
        (historyItems) => {
          let clickedItem: HistoryItemData | null = null;
          const mockOnItemClick = (item: HistoryItemData) => {
            clickedItem = item;
          };
          const mockOnClearHistory = () => {};

          const { unmount, container } = render(
            <History
              history={historyItems}
              onItemClick={mockOnItemClick}
              onClearHistory={mockOnClearHistory}
            />
          );

          // Select a random history item to click
          const randomIndex = Math.floor(Math.random() * historyItems.length);
          const itemToClick = historyItems[randomIndex];

          // Find and click the history item
          const historyItemButtons = container.querySelectorAll('.history-item');
          const buttonToClick = historyItemButtons[randomIndex];
          
          expect(buttonToClick).toBeInTheDocument();

          // Click the history item using fireEvent (synchronous)
          const clickEvent = new MouseEvent('click', { bubbles: true });
          buttonToClick.dispatchEvent(clickEvent);

          // Verify that the callback was called with the correct item:
          
          // 1. Callback should have been called
          expect(clickedItem).not.toBeNull();
          
          if (clickedItem) {
            // 2. The clicked item should match the expected item
            expect(clickedItem.sessionId).toBe(itemToClick.sessionId);
            expect(clickedItem.claimText).toBe(itemToClick.claimText);
            expect(clickedItem.verdict).toBe(itemToClick.verdict);
            expect(clickedItem.confidence).toBe(itemToClick.confidence);
            expect(clickedItem.timestamp).toBe(itemToClick.timestamp);
            
            // 3. The full results should be included
            expect(clickedItem.fullResults).toBeDefined();
            expect(clickedItem.fullResults).toBe(itemToClick.fullResults);
            
            // 4. The full results should contain all required fields
            expect(clickedItem.fullResults.session_id).toBeDefined();
            expect(clickedItem.fullResults.consensus_verdict).toBeDefined();
            expect(clickedItem.fullResults.confidence_score).toBeDefined();
            expect(clickedItem.fullResults.atomic_claims).toBeDefined();
            
            // 5. The session ID in full results should match
            expect(clickedItem.fullResults.session_id).toBe(itemToClick.sessionId);
          }

          unmount();
        }
      ),
      { numRuns: 100 }
    );
  });

  /**
   * Additional property: History items should be clickable and accessible
   * 
   * For any history item, it should be rendered as an interactive button
   * with proper accessibility attributes.
   */
  it('Property: should render history items as accessible interactive buttons', () => {
    fc.assert(
      fc.property(
        historyListArbitrary,
        (historyItems) => {
          const mockOnItemClick = () => {};
          const mockOnClearHistory = () => {};

          const { unmount, container } = render(
            <History
              history={historyItems}
              onItemClick={mockOnItemClick}
              onClearHistory={mockOnClearHistory}
            />
          );

          // Verify accessibility and interactivity:
          
          const historyItemButtons = container.querySelectorAll('.history-item');
          
          historyItemButtons.forEach((button) => {
            // 1. Should be a button element
            expect(button.tagName).toBe('BUTTON');
            
            // 2. Should have role="listitem"
            expect(button).toHaveAttribute('role', 'listitem');
            
            // 3. Should have aria-label
            expect(button).toHaveAttribute('aria-label');
            const ariaLabel = button.getAttribute('aria-label') || '';
            expect(ariaLabel.length).toBeGreaterThan(0);
            expect(ariaLabel).toMatch(/view verification/i);
            
            // 4. Should be keyboard accessible (not disabled)
            expect(button).not.toBeDisabled();
          });

          unmount();
        }
      ),
      { numRuns: 100 }
    );
  });

  /**
   * Additional property: Empty history should display appropriate message
   * 
   * When history is empty, the component should display a helpful message
   * instead of an empty list.
   */
  it('Property: should display empty state message when history is empty', () => {
    const mockOnItemClick = () => {};
    const mockOnClearHistory = () => {};

    const { unmount } = render(
      <History
        history={[]}
        onItemClick={mockOnItemClick}
        onClearHistory={mockOnClearHistory}
      />
    );

    // Verify empty state:
    
    // 1. Empty message should be displayed
    const emptyMessage = screen.getByText(/no verification history yet/i);
    expect(emptyMessage).toBeInTheDocument();
    
    // 2. Hint message should be displayed
    const hintMessage = screen.getByText(/submit a claim/i);
    expect(hintMessage).toBeInTheDocument();
    
    // 3. No history items should be rendered
    const historyItems = document.querySelectorAll('.history-item');
    expect(historyItems.length).toBe(0);
    
    // 4. Clear button should not be displayed
    const clearButton = document.querySelector('.history-clear-button');
    expect(clearButton).not.toBeInTheDocument();

    unmount();
  });

  /**
   * Additional property: History count should be accurate
   * 
   * For any non-empty history, the history count badge should display
   * the correct number of items.
   */
  it('Property: should display accurate history count', () => {
    fc.assert(
      fc.property(
        historyListArbitrary,
        (historyItems) => {
          const mockOnItemClick = () => {};
          const mockOnClearHistory = () => {};

          const { unmount } = render(
            <History
              history={historyItems}
              onItemClick={mockOnItemClick}
              onClearHistory={mockOnClearHistory}
            />
          );

          // Verify history count:
          
          // 1. Count badge should be displayed
          const countBadge = screen.getByText(`(${historyItems.length})`);
          expect(countBadge).toBeInTheDocument();
          
          // 2. Count should match actual number of items
          expect(countBadge.textContent).toBe(`(${historyItems.length})`);
          
          // 3. Count should be a positive integer
          const count = historyItems.length;
          expect(count).toBeGreaterThan(0);
          expect(Number.isInteger(count)).toBe(true);

          unmount();
        }
      ),
      { numRuns: 100 }
    );
  });

  /**
   * Additional property: Verdict styling should be consistent with verdict type
   * 
   * For any history item, the verdict badge should have styling that matches
   * the verdict type (Supported, Refuted, Not Enough Information).
   */
  it('Property: should apply consistent verdict styling across history items', () => {
    fc.assert(
      fc.property(
        historyListArbitrary,
        (historyItems) => {
          const mockOnItemClick = () => {};
          const mockOnClearHistory = () => {};

          const { unmount, container } = render(
            <History
              history={historyItems}
              onItemClick={mockOnItemClick}
              onClearHistory={mockOnClearHistory}
            />
          );

          // Verify verdict styling consistency:
          
          const expectedClasses = {
            'Supported': 'verdict-supported',
            'Refuted': 'verdict-refuted',
            'Not Enough Information': 'verdict-nei',
          };

          historyItems.forEach((item) => {
            const historyItemButtons = container.querySelectorAll('.history-item');
            
            historyItemButtons.forEach((button) => {
              const verdictSpan = button.querySelector('.history-item-verdict');
              
              if (verdictSpan?.textContent === item.verdict) {
                // Verdict badge should have the correct color class
                const className = verdictSpan.className;
                const expectedClass = expectedClasses[item.verdict];
                expect(className).toContain(expectedClass);
              }
            });
          });

          unmount();
        }
      ),
      { numRuns: 100 }
    );
  });

  /**
   * Additional property: Timestamps should be formatted consistently
   * 
   * For any history item, the timestamp should be formatted in a
   * human-readable format.
   */
  it('Property: should format timestamps consistently', () => {
    fc.assert(
      fc.property(
        historyListArbitrary,
        (historyItems) => {
          const mockOnItemClick = () => {};
          const mockOnClearHistory = () => {};

          const { unmount, container } = render(
            <History
              history={historyItems}
              onItemClick={mockOnItemClick}
              onClearHistory={mockOnClearHistory}
            />
          );

          // Verify timestamp formatting:
          
          const timestampElements = container.querySelectorAll('.history-item-timestamp');
          
          expect(timestampElements.length).toBe(historyItems.length);
          
          timestampElements.forEach((timestampElement) => {
            const timestampText = timestampElement.textContent || '';
            
            // 1. Timestamp should not be empty
            expect(timestampText.length).toBeGreaterThan(0);
            
            // 2. Timestamp should be human-readable (not ISO format)
            // Should not contain 'T' or 'Z' from ISO format
            expect(timestampText).not.toMatch(/T\d{2}:/);
            expect(timestampText).not.toMatch(/Z$/);
            
            // 3. Timestamp should contain some date/time information
            // Could be relative (e.g., "2 hours ago") or absolute (e.g., "Jan 15, 2024")
            expect(timestampText.length).toBeGreaterThan(5);
          });

          unmount();
        }
      ),
      { numRuns: 100 }
    );
  });
});
