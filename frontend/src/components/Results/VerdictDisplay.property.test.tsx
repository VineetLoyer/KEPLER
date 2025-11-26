import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import * as fc from 'fast-check';
import { VerdictDisplay } from './VerdictDisplay';
import type { ConsensusVerdict, ConfidenceScore, VerdictType } from '../../types/verification';

/**
 * Property-Based Tests for VerdictDisplay Component
 * 
 * Task 11.1: Write property tests for verdict display
 * - Property 5: Verdict display after completion
 * - Property 14: Distinct verdict styling
 * - Property 15: Confidence score percentage format
 * - Property 16: Confidence indicator presence
 * - Property 17: Justification text display
 * 
 * Requirements: 2.5, 5.1, 5.2, 5.3, 5.4, 5.5
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

const confidenceScoreArbitrary = fc.record({
  overall_score: fc.double({ min: 0, max: 1, noNaN: true }),
  source_reliability: fc.double({ min: 0, max: 1, noNaN: true }),
  model_agreement: fc.double({ min: 0, max: 1, noNaN: true }),
  evidence_recency: fc.double({ min: 0, max: 1, noNaN: true }),
  structured_justification: fc.record({
    summary: fc.string({ minLength: 10, maxLength: 200 }),
    key_evidence: fc.constant([]),
    reasoning_chain: fc.record({
      steps: fc.constant([]),
      agreements: fc.constant([]),
      conflicts: fc.constant([]),
      gaps: fc.constant([]),
    }),
    source_links: fc.constant([]),
  }),
}) as fc.Arbitrary<ConfidenceScore>;

const consensusVerdictArbitrary = fc.record({
  final_classification: verdictTypeArbitrary,
  consensus_justification: fc.string({ minLength: 20, maxLength: 500 }),
  individual_verdicts: fc.constant([]),
  agreement_level: fc.double({ min: 0, max: 1 }),
}) as fc.Arbitrary<ConsensusVerdict>;

describe('VerdictDisplay Property-Based Tests', () => {
  /**
   * **Feature: kepler-web-interface, Property 5: Verdict display after completion**
   * 
   * For any successful API response, the frontend should display the verdict classification.
   * 
   * This property verifies that the VerdictDisplay component always renders the verdict
   * classification badge regardless of which verdict type is provided.
   * 
   * **Validates: Requirements 2.5, 5.1**
   */
  it('Property 5: should display verdict classification for any valid verdict', () => {
    fc.assert(
      fc.property(
        consensusVerdictArbitrary,
        confidenceScoreArbitrary,
        (verdict, confidenceScore) => {
          const { unmount } = render(
            <VerdictDisplay verdict={verdict} confidenceScore={confidenceScore} />
          );

          // Verify that the verdict classification is displayed:
          
          // 1. The verdict badge element exists
          const verdictBadge = screen.getByText(verdict.final_classification);
          expect(verdictBadge).toBeInTheDocument();

          // 2. The verdict badge has the correct class
          expect(verdictBadge).toHaveClass('verdict-badge-text');

          // 3. The verdict badge is visible
          expect(verdictBadge).toBeVisible();

          // 4. The verdict display container exists with proper role
          const container = screen.getByRole('region', { name: /verification verdict/i });
          expect(container).toBeInTheDocument();

          unmount();
        }
      ),
      { numRuns: 100 }
    );
  });

  /**
   * **Feature: kepler-web-interface, Property 14: Distinct verdict styling**
   * 
   * For any two different verdict types (Supported vs Refuted vs Not Enough Information),
   * the visual styling should be distinguishable.
   * 
   * This property verifies that each verdict type has a unique CSS class that provides
   * distinct visual styling.
   * 
   * **Validates: Requirements 5.2**
   */
  it('Property 14: should apply distinct styling for different verdict types', () => {
    fc.assert(
      fc.property(
        // Generate two different verdict types
        fc.tuple(verdictTypeArbitrary, verdictTypeArbitrary)
          .filter(([v1, v2]) => v1 !== v2),
        confidenceScoreArbitrary,
        ([verdict1, verdict2], confidenceScore) => {
          // Render first verdict
          const { unmount: unmount1, container: container1 } = render(
            <VerdictDisplay
              verdict={{
                final_classification: verdict1,
                consensus_justification: 'Test justification',
                individual_verdicts: [],
                agreement_level: 0.8,
              }}
              confidenceScore={confidenceScore}
            />
          );

          // Get the verdict badge class for first verdict
          const badge1 = container1.querySelector('.verdict-badge');
          const classes1 = badge1?.className || '';

          unmount1();

          // Render second verdict
          const { unmount: unmount2, container: container2 } = render(
            <VerdictDisplay
              verdict={{
                final_classification: verdict2,
                consensus_justification: 'Test justification',
                individual_verdicts: [],
                agreement_level: 0.8,
              }}
              confidenceScore={confidenceScore}
            />
          );

          // Get the verdict badge class for second verdict
          const badge2 = container2.querySelector('.verdict-badge');
          const classes2 = badge2?.className || '';

          // Verify that the classes are different
          expect(classes1).not.toBe(classes2);

          // Verify that each has a specific verdict color class
          const expectedClasses = {
            'Supported': 'verdict-supported',
            'Refuted': 'verdict-refuted',
            'Not Enough Information': 'verdict-nei',
          };

          expect(classes1).toContain(expectedClasses[verdict1]);
          expect(classes2).toContain(expectedClasses[verdict2]);

          // Verify they don't share the same verdict color class
          expect(classes1.includes(expectedClasses[verdict2])).toBe(false);
          expect(classes2.includes(expectedClasses[verdict1])).toBe(false);

          unmount2();
        }
      ),
      { numRuns: 100 }
    );
  });

  /**
   * **Feature: kepler-web-interface, Property 15: Confidence score percentage format**
   * 
   * For any displayed confidence score, it should be formatted as a percentage (0-100%).
   * 
   * This property verifies that confidence scores are always displayed as percentages
   * with proper formatting, regardless of the input score value (0-1 range).
   * 
   * **Validates: Requirements 5.3**
   */
  it('Property 15: should format confidence scores as percentages', () => {
    fc.assert(
      fc.property(
        consensusVerdictArbitrary,
        confidenceScoreArbitrary,
        (verdict, confidenceScore) => {
          const { unmount, container } = render(
            <VerdictDisplay verdict={verdict} confidenceScore={confidenceScore} />
          );

          // Verify that confidence scores are formatted as percentages:
          
          // 1. Overall confidence score is displayed as percentage
          const overallPercentage = Math.round(confidenceScore.overall_score * 100);
          const percentageText = `${(confidenceScore.overall_score * 100).toFixed(1)}%`;
          
          // Find the large percentage display
          const largePercentage = container.querySelector('.verdict-confidence-percentage-large');
          expect(largePercentage).toBeInTheDocument();
          expect(largePercentage?.textContent).toBe(percentageText);

          // 2. Verify percentage is in valid range (0-100%)
          expect(overallPercentage).toBeGreaterThanOrEqual(0);
          expect(overallPercentage).toBeLessThanOrEqual(100);

          // 3. Verify percentage format includes '%' symbol
          expect(largePercentage?.textContent).toMatch(/%$/);

          // 4. Verify all confidence bars show percentages
          const confidenceBars = container.querySelectorAll('.confidence-bar-percentage');
          expect(confidenceBars.length).toBeGreaterThan(0);

          confidenceBars.forEach((bar) => {
            const text = bar.textContent || '';
            // Should end with %
            expect(text).toMatch(/%$/);
            // Should be a valid number
            const numValue = parseFloat(text.replace('%', ''));
            expect(numValue).toBeGreaterThanOrEqual(0);
            expect(numValue).toBeLessThanOrEqual(100);
          });

          unmount();
        }
      ),
      { numRuns: 100 }
    );
  });

  /**
   * **Feature: kepler-web-interface, Property 16: Confidence indicator presence**
   * 
   * For any verdict display, a visual confidence indicator should be present.
   * 
   * This property verifies that confidence indicators (progress bars) are always
   * rendered for the overall score and all confidence factors.
   * 
   * **Validates: Requirements 5.4**
   */
  it('Property 16: should display visual confidence indicators', () => {
    fc.assert(
      fc.property(
        consensusVerdictArbitrary,
        confidenceScoreArbitrary,
        (verdict, confidenceScore) => {
          const { unmount, container } = render(
            <VerdictDisplay verdict={verdict} confidenceScore={confidenceScore} />
          );

          // Verify that visual confidence indicators are present:
          
          // 1. At least one confidence bar track exists
          const confidenceTracks = container.querySelectorAll('.confidence-bar-track');
          expect(confidenceTracks.length).toBeGreaterThan(0);

          // 2. Each track has a fill element (the visual indicator)
          confidenceTracks.forEach((track) => {
            const fill = track.querySelector('.confidence-bar-fill');
            expect(fill).toBeInTheDocument();
            
            // 3. The fill has a width style set (representing the score)
            const style = (fill as HTMLElement)?.style;
            expect(style?.width).toBeTruthy();
            
            // 4. The width is a valid percentage
            const widthMatch = style?.width?.match(/^(\d+(?:\.\d+)?)%$/);
            expect(widthMatch).toBeTruthy();
            
            if (widthMatch) {
              const widthValue = parseFloat(widthMatch[1]);
              expect(widthValue).toBeGreaterThanOrEqual(0);
              expect(widthValue).toBeLessThanOrEqual(100);
            }
          });

          // 5. Confidence bars have proper ARIA attributes
          const progressBars = container.querySelectorAll('[role="progressbar"]');
          expect(progressBars.length).toBeGreaterThan(0);

          progressBars.forEach((bar) => {
            expect(bar).toHaveAttribute('aria-valuenow');
            expect(bar).toHaveAttribute('aria-valuemin', '0');
            expect(bar).toHaveAttribute('aria-valuemax', '100');
          });

          // 6. Verify we have confidence indicators for all factors
          // Should have: Overall, Source Reliability, Model Agreement, Evidence Recency
          expect(confidenceTracks.length).toBeGreaterThanOrEqual(4);

          unmount();
        }
      ),
      { numRuns: 100 }
    );
  });

  /**
   * **Feature: kepler-web-interface, Property 17: Justification text display**
   * 
   * For any verdict, the consensus justification text should be displayed.
   * 
   * This property verifies that the justification text is always rendered
   * and is visible to users.
   * 
   * **Validates: Requirements 5.5**
   */
  it('Property 17: should display consensus justification text', () => {
    fc.assert(
      fc.property(
        consensusVerdictArbitrary,
        confidenceScoreArbitrary,
        (verdict, confidenceScore) => {
          const { unmount, container } = render(
            <VerdictDisplay verdict={verdict} confidenceScore={confidenceScore} />
          );

          // Verify that justification text is displayed:
          
          // 1. The justification section exists
          const justificationSection = container.querySelector('.verdict-justification-section');
          expect(justificationSection).toBeInTheDocument();

          // 2. The justification text element exists
          const justificationText = container.querySelector('.verdict-justification-text');
          expect(justificationText).toBeInTheDocument();

          // 3. The justification text matches the provided text
          expect(justificationText?.textContent).toBe(verdict.consensus_justification);

          // 4. The justification text is not empty
          expect(justificationText?.textContent?.length).toBeGreaterThan(0);

          // 5. The justification text is visible
          expect(justificationText).toBeVisible();

          // 6. The section has a title
          const sectionTitle = justificationSection?.querySelector('.verdict-section-title');
          expect(sectionTitle).toBeInTheDocument();
          expect(sectionTitle?.textContent).toMatch(/justification/i);

          unmount();
        }
      ),
      { numRuns: 100 }
    );
  });

  /**
   * Additional property: Confidence factor breakdown should be complete
   * 
   * For any confidence score, all three confidence factors should be displayed
   * with their respective labels and values.
   */
  it('Property: should display all confidence factors in breakdown', () => {
    fc.assert(
      fc.property(
        consensusVerdictArbitrary,
        confidenceScoreArbitrary,
        (verdict, confidenceScore) => {
          const { unmount, container } = render(
            <VerdictDisplay verdict={verdict} confidenceScore={confidenceScore} />
          );

          // Verify that all confidence factors are displayed:
          
          // 1. The breakdown section exists
          const breakdownSection = container.querySelector('.verdict-breakdown-section');
          expect(breakdownSection).toBeInTheDocument();

          // 2. All three factors are present with labels
          const sourceReliability = screen.getByText(/Source Reliability/i);
          expect(sourceReliability).toBeInTheDocument();

          const modelAgreement = screen.getByText(/Model Agreement/i);
          expect(modelAgreement).toBeInTheDocument();

          const evidenceRecency = screen.getByText(/Evidence Recency/i);
          expect(evidenceRecency).toBeInTheDocument();

          // 3. Each factor has a confidence bar
          const breakdownItems = container.querySelectorAll('.verdict-breakdown-item');
          expect(breakdownItems.length).toBe(3);

          // 4. Each breakdown item contains a confidence bar
          breakdownItems.forEach((item) => {
            const bar = item.querySelector('.confidence-bar-container');
            expect(bar).toBeInTheDocument();
          });

          unmount();
        }
      ),
      { numRuns: 100 }
    );
  });

  /**
   * Property: Component structure should be consistent
   * 
   * For any valid input, the component should maintain a consistent DOM structure
   * with all required sections present.
   */
  it('Property: should maintain consistent structure for all inputs', () => {
    fc.assert(
      fc.property(
        consensusVerdictArbitrary,
        confidenceScoreArbitrary,
        (verdict, confidenceScore) => {
          const { unmount, container } = render(
            <VerdictDisplay verdict={verdict} confidenceScore={confidenceScore} />
          );

          // Verify consistent structure:
          
          // 1. Main container
          const mainContainer = container.querySelector('.verdict-display');
          expect(mainContainer).toBeInTheDocument();

          // 2. Verdict badge
          const badge = container.querySelector('.verdict-badge');
          expect(badge).toBeInTheDocument();

          // 3. Confidence section
          const confidenceSection = container.querySelector('.verdict-confidence-section');
          expect(confidenceSection).toBeInTheDocument();

          // 4. Justification section
          const justificationSection = container.querySelector('.verdict-justification-section');
          expect(justificationSection).toBeInTheDocument();

          // 5. Breakdown section
          const breakdownSection = container.querySelector('.verdict-breakdown-section');
          expect(breakdownSection).toBeInTheDocument();

          // 6. All sections have titles
          const sectionTitles = container.querySelectorAll('.verdict-section-title');
          expect(sectionTitles.length).toBe(3); // Confidence, Justification, Breakdown

          unmount();
        }
      ),
      { numRuns: 100 }
    );
  });

  /**
   * Property: Confidence scores should be properly bounded
   * 
   * For any confidence score values, the displayed percentages should be
   * within the valid range of 0-100%.
   */
  it('Property: should display confidence scores within valid range', () => {
    fc.assert(
      fc.property(
        consensusVerdictArbitrary,
        confidenceScoreArbitrary,
        (verdict, confidenceScore) => {
          const { unmount, container } = render(
            <VerdictDisplay verdict={verdict} confidenceScore={confidenceScore} />
          );

          // Verify all displayed percentages are within valid range:
          
          const percentageElements = container.querySelectorAll('.confidence-bar-percentage');
          
          percentageElements.forEach((element) => {
            const text = element.textContent || '';
            const value = parseFloat(text.replace('%', ''));
            
            // Should be a valid number
            expect(isNaN(value)).toBe(false);
            
            // Should be within 0-100 range
            expect(value).toBeGreaterThanOrEqual(0);
            expect(value).toBeLessThanOrEqual(100);
          });

          // Verify the large percentage display
          const largePercentage = container.querySelector('.verdict-confidence-percentage-large');
          if (largePercentage) {
            const text = largePercentage.textContent || '';
            const value = parseFloat(text.replace('%', ''));
            
            expect(isNaN(value)).toBe(false);
            expect(value).toBeGreaterThanOrEqual(0);
            expect(value).toBeLessThanOrEqual(100);
          }

          unmount();
        }
      ),
      { numRuns: 100 }
    );
  });
});
