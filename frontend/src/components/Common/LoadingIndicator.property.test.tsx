import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import * as fc from 'fast-check';
import { LoadingIndicator, type VerificationStage } from './LoadingIndicator';

/**
 * Property-Based Tests for LoadingIndicator Component
 * 
 * Task 10.1: Write property tests for loading indicator
 * - Property 4: Loading indicator during verification
 * - Property 36: Progress message display
 * 
 * Requirements: 2.4, 12.1, 12.2
 * 
 * These tests use fast-check to generate random inputs and verify
 * that the component behaves correctly across all possible inputs.
 */

describe('LoadingIndicator Property-Based Tests', () => {
  /**
   * **Feature: kepler-web-interface, Property 4: Loading indicator during verification**
   * 
   * For any verification request in progress, the frontend should display a loading indicator.
   * 
   * This property verifies that the LoadingIndicator component always renders the essential
   * loading UI elements regardless of the stage provided.
   * 
   * **Validates: Requirements 2.4, 12.1**
   */
  it('Property 4: should always display loading indicator elements', () => {
    fc.assert(
      fc.property(
        // Generate any valid verification stage or undefined
        fc.oneof(
          fc.constantFrom<VerificationStage>(
            'initializing',
            'decomposing',
            'retrieving',
            'reranking',
            'verifying',
            'aggregating',
            'scoring',
            'finalizing'
          ),
          fc.constant(undefined)
        ),
        (stage) => {
          const { unmount, container } = render(
            <LoadingIndicator currentStage={stage} />
          );

          // Verify that essential loading indicator elements are present:
          
          // 1. The loading indicator container with proper role
          const indicator = screen.getByRole('status');
          expect(indicator).toBeInTheDocument();
          expect(indicator).toHaveClass('loading-indicator');

          // 2. The loading spinner (SVG) is present
          const spinner = container.querySelector('.loading-spinner');
          expect(spinner).toBeInTheDocument();
          expect(spinner?.tagName).toBe('svg');

          // 3. The helper text is always displayed
          const helperText = screen.getByText(/This may take a moment\.\.\./i);
          expect(helperText).toBeInTheDocument();
          expect(helperText).toHaveClass('loading-helper-text');

          // 4. A stage message is displayed (even if stage is undefined, defaults to 'initializing')
          const stageMessage = container.querySelector('.loading-stage-message');
          expect(stageMessage).toBeInTheDocument();
          expect(stageMessage?.textContent).toBeTruthy();
          expect(stageMessage?.textContent?.length).toBeGreaterThan(0);

          // 5. Accessibility: aria-live attribute for screen readers
          expect(indicator).toHaveAttribute('aria-live', 'polite');

          // 6. Screen reader text is present
          const srText = container.querySelector('.sr-only');
          expect(srText).toBeInTheDocument();
          expect(srText?.textContent).toContain('Loading:');

          unmount();
        }
      ),
      { numRuns: 100 } // Run 100 iterations as specified in design doc
    );
  });

  /**
   * **Feature: kepler-web-interface, Property 36: Progress message display**
   * 
   * For any verification in progress, the frontend should display messages 
   * indicating the current pipeline stage.
   * 
   * This property verifies that for each valid verification stage, a specific
   * and meaningful progress message is displayed to inform the user about
   * what's happening.
   * 
   * **Validates: Requirements 12.2**
   */
  it('Property 36: should display stage-specific progress messages for all stages', () => {
    fc.assert(
      fc.property(
        // Generate all valid verification stages
        fc.constantFrom<VerificationStage>(
          'initializing',
          'decomposing',
          'retrieving',
          'reranking',
          'verifying',
          'aggregating',
          'scoring',
          'finalizing'
        ),
        (stage) => {
          const { unmount, container } = render(
            <LoadingIndicator currentStage={stage} />
          );

          // Verify that a stage-specific message is displayed:
          
          // 1. The stage message element exists
          const stageMessage = container.querySelector('.loading-stage-message');
          expect(stageMessage).toBeInTheDocument();

          // 2. The message is not empty
          const messageText = stageMessage?.textContent || '';
          expect(messageText.length).toBeGreaterThan(0);

          // 3. The message is stage-specific (contains relevant keywords)
          // Each stage should have a unique, descriptive message
          const stageKeywords: Record<VerificationStage, string[]> = {
            initializing: ['Initializing', 'verification', 'process'],
            decomposing: ['Breaking', 'claim', 'atomic', 'components'],
            retrieving: ['Retrieving', 'evidence', 'sources'],
            reranking: ['Ranking', 'evidence', 'relevance'],
            verifying: ['Verifying', 'claim', 'evidence'],
            aggregating: ['Aggregating', 'results', 'models'],
            scoring: ['Calculating', 'confidence', 'scores'],
            finalizing: ['Finalizing', 'verification', 'results'],
          };

          // At least one keyword from the stage should be in the message
          const keywords = stageKeywords[stage];
          const hasRelevantKeyword = keywords.some(keyword =>
            messageText.toLowerCase().includes(keyword.toLowerCase())
          );
          expect(hasRelevantKeyword).toBe(true);

          // 4. The message ends with ellipsis (indicating ongoing process)
          expect(messageText).toMatch(/\.{3}$/);

          // 5. Screen reader text includes the stage message
          const srText = container.querySelector('.sr-only');
          expect(srText?.textContent).toContain(messageText);

          // 6. The message is visible (not hidden)
          expect(stageMessage).toBeVisible();

          unmount();
        }
      ),
      { numRuns: 100 } // Run 100 iterations as specified in design doc
    );
  });

  /**
   * Additional property: Stage message updates should be reflected immediately
   * 
   * For any sequence of stage transitions, the displayed message should
   * always match the current stage.
   */
  it('Property: should update progress message when stage changes', () => {
    fc.assert(
      fc.property(
        // Generate two different stages
        fc.tuple(
          fc.constantFrom<VerificationStage>(
            'initializing',
            'decomposing',
            'retrieving',
            'reranking',
            'verifying',
            'aggregating',
            'scoring',
            'finalizing'
          ),
          fc.constantFrom<VerificationStage>(
            'initializing',
            'decomposing',
            'retrieving',
            'reranking',
            'verifying',
            'aggregating',
            'scoring',
            'finalizing'
          )
        ).filter(([stage1, stage2]) => stage1 !== stage2), // Ensure they're different
        ([initialStage, newStage]) => {
          const { unmount, container, rerender } = render(
            <LoadingIndicator currentStage={initialStage} />
          );

          // Get initial message
          const initialMessage = container.querySelector('.loading-stage-message');
          const initialText = initialMessage?.textContent || '';
          expect(initialText.length).toBeGreaterThan(0);

          // Update to new stage
          rerender(<LoadingIndicator currentStage={newStage} />);

          // Get updated message
          const updatedMessage = container.querySelector('.loading-stage-message');
          const updatedText = updatedMessage?.textContent || '';
          expect(updatedText.length).toBeGreaterThan(0);

          // Verify the message changed
          expect(updatedText).not.toBe(initialText);

          // Verify the new message is appropriate for the new stage
          const stageKeywords: Record<VerificationStage, string[]> = {
            initializing: ['Initializing', 'verification', 'process'],
            decomposing: ['Breaking', 'claim', 'atomic', 'components'],
            retrieving: ['Retrieving', 'evidence', 'sources'],
            reranking: ['Ranking', 'evidence', 'relevance'],
            verifying: ['Verifying', 'claim', 'evidence'],
            aggregating: ['Aggregating', 'results', 'models'],
            scoring: ['Calculating', 'confidence', 'scores'],
            finalizing: ['Finalizing', 'verification', 'results'],
          };

          const newKeywords = stageKeywords[newStage];
          const hasRelevantKeyword = newKeywords.some(keyword =>
            updatedText.toLowerCase().includes(keyword.toLowerCase())
          );
          expect(hasRelevantKeyword).toBe(true);

          unmount();
        }
      ),
      { numRuns: 100 }
    );
  });

  /**
   * Property: Loading indicator should maintain accessibility across all stages
   * 
   * For any stage, the component should maintain proper accessibility attributes
   * to ensure screen reader users are informed of the loading state.
   */
  it('Property: should maintain accessibility attributes for all stages', () => {
    fc.assert(
      fc.property(
        fc.constantFrom<VerificationStage>(
          'initializing',
          'decomposing',
          'retrieving',
          'reranking',
          'verifying',
          'aggregating',
          'scoring',
          'finalizing'
        ),
        (stage) => {
          const { unmount, container } = render(
            <LoadingIndicator currentStage={stage} />
          );

          // 1. role="status" for live region
          const indicator = screen.getByRole('status');
          expect(indicator).toBeInTheDocument();

          // 2. aria-live="polite" for non-intrusive updates
          expect(indicator).toHaveAttribute('aria-live', 'polite');

          // 3. Screen reader text with "Loading:" prefix
          const srText = container.querySelector('.sr-only');
          expect(srText).toBeInTheDocument();
          expect(srText?.textContent).toMatch(/^Loading:/);

          // 4. SVG spinner is hidden from screen readers
          const spinner = container.querySelector('.loading-spinner');
          expect(spinner).toHaveAttribute('aria-hidden', 'true');

          // 5. Screen reader text includes the current stage message
          const stageMessage = container.querySelector('.loading-stage-message');
          const messageText = stageMessage?.textContent || '';
          expect(srText?.textContent).toContain(messageText);

          unmount();
        }
      ),
      { numRuns: 100 }
    );
  });

  /**
   * Property: Loading indicator structure should be consistent
   * 
   * For any stage, the component should maintain a consistent DOM structure
   * with all required elements present.
   */
  it('Property: should maintain consistent structure for all stages', () => {
    fc.assert(
      fc.property(
        fc.constantFrom<VerificationStage>(
          'initializing',
          'decomposing',
          'retrieving',
          'reranking',
          'verifying',
          'aggregating',
          'scoring',
          'finalizing'
        ),
        (stage) => {
          const { unmount, container } = render(
            <LoadingIndicator currentStage={stage} />
          );

          // Verify consistent structure:
          
          // 1. Main container
          const indicator = container.querySelector('.loading-indicator');
          expect(indicator).toBeInTheDocument();

          // 2. Spinner container
          const spinnerContainer = container.querySelector('.loading-spinner-container');
          expect(spinnerContainer).toBeInTheDocument();

          // 3. Spinner SVG
          const spinner = container.querySelector('.loading-spinner');
          expect(spinner).toBeInTheDocument();

          // 4. Two circles in spinner (track and path)
          const circles = container.querySelectorAll('.loading-spinner circle');
          expect(circles.length).toBe(2);

          // 5. Content container
          const content = container.querySelector('.loading-content');
          expect(content).toBeInTheDocument();

          // 6. Stage message
          const stageMessage = container.querySelector('.loading-stage-message');
          expect(stageMessage).toBeInTheDocument();

          // 7. Helper text
          const helperText = container.querySelector('.loading-helper-text');
          expect(helperText).toBeInTheDocument();

          // 8. Screen reader text
          const srText = container.querySelector('.sr-only');
          expect(srText).toBeInTheDocument();

          unmount();
        }
      ),
      { numRuns: 100 }
    );
  });
});
