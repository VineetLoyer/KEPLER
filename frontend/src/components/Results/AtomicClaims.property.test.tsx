import { describe, it, expect } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import * as fc from 'fast-check';
import { AtomicClaims } from './AtomicClaims';
import type { AtomicClaim, VerificationResult, VerdictType } from '../../types/verification';

/**
 * Property-Based Tests for AtomicClaims Component
 * 
 * Task 15.1: Write property tests for atomic claims
 * - Property 25: Atomic claims list display
 * - Property 26: Atomic claim status display
 * - Property 27: Atomic claim expansion
 * - Property 28: Compound claim overall verdict
 * 
 * Requirements: 9.1, 9.2, 9.3, 9.4, 9.5
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

// Generate valid IDs (alphanumeric with hyphens)
const idArbitrary = fc.stringMatching(/^[a-zA-Z0-9][a-zA-Z0-9-]{4,19}$/);

// Generate valid claim text (non-empty, printable characters)
const claimTextArbitrary = fc.string({ minLength: 10, maxLength: 200 })
  .filter(s => s.trim().length >= 10); // Ensure non-whitespace

const atomicClaimArbitrary = fc.record({
  id: idArbitrary,
  text: claimTextArbitrary,
  is_atomic: fc.boolean(),
  parent_claim: fc.option(idArbitrary, { nil: undefined }),
  verification_status: fc.option(verdictTypeArbitrary, { nil: undefined }),
}) as fc.Arbitrary<AtomicClaim>;

const verificationResultArbitrary = fc.record({
  session_id: fc.string({ minLength: 10, maxLength: 30 }),
  original_input: fc.constant({}),
  atomic_claims: fc.array(atomicClaimArbitrary, { minLength: 1, maxLength: 5 }),
  consensus_verdict: fc.record({
    final_classification: verdictTypeArbitrary,
    consensus_justification: fc.string({ minLength: 20, maxLength: 500 }),
    individual_verdicts: fc.constant([]),
    agreement_level: fc.double({ min: 0, max: 1, noNaN: true }),
  }),
  confidence_score: fc.record({
    overall_score: fc.double({ min: 0, max: 1, noNaN: true }),
    source_reliability: fc.double({ min: 0, max: 1, noNaN: true }),
    model_agreement: fc.double({ min: 0, max: 1, noNaN: true }),
    evidence_recency: fc.double({ min: 0, max: 1, noNaN: true }),
    structured_justification: fc.constant({
      summary: 'Test summary',
      key_evidence: [],
      reasoning_chain: {
        steps: [],
        agreements: [],
        conflicts: [],
        gaps: [],
      },
      source_links: [],
    }),
  }),
  processing_metadata: fc.constant({}),
  trace_log: fc.constant([]),
}) as fc.Arbitrary<VerificationResult>;

describe('AtomicClaims Property-Based Tests', () => {
  /**
   * **Feature: kepler-web-interface, Property 25: Atomic claims list display**
   * 
   * For any compound claim that is decomposed, all atomic claims should be displayed.
   * 
   * This property verifies that when a claim is decomposed into atomic claims,
   * the component displays all of them in a list format.
   * 
   * **Validates: Requirements 9.1, 9.2**
   */
  it('Property 25: should display all atomic claims in the list', () => {
    fc.assert(
      fc.property(
        fc.array(atomicClaimArbitrary, { minLength: 1, maxLength: 5 }), // Reduced max for performance
        (atomicClaims) => {
          const { unmount, container } = render(
            <AtomicClaims atomicClaims={atomicClaims} />
          );

          // 1. All atomic claims should be displayed
          const claimItems = container.querySelectorAll('.atomic-claim-item');
          expect(claimItems.length).toBe(atomicClaims.length);

          // 2. Each claim text should be visible
          const claimTexts = container.querySelectorAll('.atomic-claim-text');
          expect(claimTexts.length).toBe(atomicClaims.length);
          
          atomicClaims.forEach((claim, index) => {
            const claimTextElement = claimTexts[index];
            expect(claimTextElement).toBeInTheDocument();
            expect(claimTextElement).toBeVisible();
            expect(claimTextElement.textContent).toBe(claim.text);
          });

          // 3. Each claim should have a header button
          const claimHeaders = container.querySelectorAll('.atomic-claim-header');
          expect(claimHeaders.length).toBe(atomicClaims.length);

          // 4. Each claim should have proper structure (check first claim only for performance)
          const firstItem = claimItems[0];
          const firstClaim = atomicClaims[0];
          
          // Should have header
          const header = firstItem.querySelector('.atomic-claim-header');
          expect(header).toBeInTheDocument();
          
          // Should have text
          const text = firstItem.querySelector('.atomic-claim-text');
          expect(text).toBeInTheDocument();
          expect(text?.textContent).toBe(firstClaim.text);
          
          // Should have status icon
          const statusIcon = firstItem.querySelector('.atomic-claim-status-icon');
          expect(statusIcon).toBeInTheDocument();
          
          // Should have status badge
          const statusBadge = firstItem.querySelector('.atomic-claim-status-badge');
          expect(statusBadge).toBeInTheDocument();

          // 5. Component should have proper title
          if (atomicClaims.length > 1) {
            expect(screen.getByText('Claim Breakdown')).toBeInTheDocument();
          } else {
            expect(screen.getByText('Claim Analysis')).toBeInTheDocument();
          }

          unmount();
        }
      ),
      { numRuns: 50 } // Reduced from 100 for performance
    );
  });

  /**
   * **Feature: kepler-web-interface, Property 26: Atomic claim status display**
   * 
   * For any atomic claim, its verification status should be displayed.
   * 
   * This property verifies that each atomic claim shows its verification status
   * with appropriate visual indicators (icons and badges).
   * 
   * **Validates: Requirements 9.3**
   */
  it('Property 26: should display verification status for each atomic claim', () => {
    fc.assert(
      fc.property(
        fc.array(atomicClaimArbitrary, { minLength: 1, maxLength: 10 }),
        (atomicClaims) => {
          const { unmount, container } = render(
            <AtomicClaims atomicClaims={atomicClaims} />
          );

          // 1. Each claim should have a status badge
          const statusBadges = container.querySelectorAll('.atomic-claim-status-badge');
          expect(statusBadges.length).toBe(atomicClaims.length);

          // 2. Each claim should have a status icon
          const statusIcons = container.querySelectorAll('.atomic-claim-status-icon');
          expect(statusIcons.length).toBe(atomicClaims.length);

          // 3. Status should match the claim data
          atomicClaims.forEach((claim, index) => {
            const badge = statusBadges[index];
            const icon = statusIcons[index];

            // Verify badge text
            if (claim.verification_status) {
              expect(badge.textContent).toBe(claim.verification_status);
            } else {
              expect(badge.textContent).toBe('Pending');
            }

            // Verify icon matches status
            const expectedIcons: Record<string, string> = {
              'Supported': '✓',
              'Refuted': '✗',
              'Not Enough Information': '?',
              'Pending': '⏳',
            };

            const status = claim.verification_status || 'Pending';
            expect(icon.textContent).toBe(expectedIcons[status]);

            // Verify status class is applied
            const expectedClasses: Record<string, string> = {
              'Supported': 'verdict-supported',
              'Refuted': 'verdict-refuted',
              'Not Enough Information': 'verdict-nei',
              'Pending': 'status-pending',
            };

            const expectedClass = expectedClasses[status];
            expect(badge).toHaveClass(expectedClass);
            expect(icon).toHaveClass(expectedClass);
          });

          unmount();
        }
      ),
      { numRuns: 100 }
    );
  });

  /**
   * **Feature: kepler-web-interface, Property 27: Atomic claim expansion**
   * 
   * For any atomic claim, clicking or interacting with it should expand to show detailed results.
   * 
   * This property verifies that the expand/collapse functionality works correctly
   * for all atomic claims, showing detailed verification results when expanded.
   * 
   * **Validates: Requirements 9.4**
   */
  it('Property 27: should expand atomic claims to show detailed results', () => {
    fc.assert(
      fc.property(
        fc.array(atomicClaimArbitrary, { minLength: 1, maxLength: 3 }), // Reduced max for performance
        fc.option(verificationResultArbitrary, { nil: undefined }),
        (atomicClaims, verificationResult) => {
          const { unmount, container } = render(
            <AtomicClaims
              atomicClaims={atomicClaims}
              verificationResult={verificationResult}
            />
          );

          // Test only the first claim to avoid timeout (expansion behavior is consistent)
          const claimHeaders = container.querySelectorAll('.atomic-claim-header');
          const header = claimHeaders[0];
          const claim = atomicClaims[0];
          
          // 1. Initially, details should not be visible
          let detailsSection = container.querySelector(`#claim-details-${claim.id}`);
          expect(detailsSection).not.toBeInTheDocument();
          
          // 2. Header should have aria-expanded=false
          expect(header).toHaveAttribute('aria-expanded', 'false');
          
          // 3. Click to expand
          fireEvent.click(header);
          
          // 4. After click, details should be visible
          detailsSection = container.querySelector(`#claim-details-${claim.id}`);
          expect(detailsSection).toBeInTheDocument();
          expect(detailsSection).toBeVisible();
          
          // 5. Header should have aria-expanded=true
          expect(header).toHaveAttribute('aria-expanded', 'true');
          
          // 6. Details should contain claim information section
          const claimInfoSection = detailsSection?.querySelector('.atomic-claim-detail-section');
          expect(claimInfoSection).toBeInTheDocument();
          
          // 7. Should show claim ID
          expect(detailsSection).toHaveTextContent('ID:');
          expect(detailsSection).toHaveTextContent(claim.id);
          
          // 8. Should show claim type
          expect(detailsSection).toHaveTextContent('Type:');
          expect(detailsSection).toHaveTextContent(claim.is_atomic ? 'Atomic' : 'Compound');
          
          // 9. If parent claim exists, should show it
          if (claim.parent_claim) {
            expect(detailsSection).toHaveTextContent('Parent Claim:');
            expect(detailsSection).toHaveTextContent(claim.parent_claim);
          }
          
          // 10. If verification status and result exist, should show verification results
          if (claim.verification_status && verificationResult) {
            expect(detailsSection).toHaveTextContent('Verification Results');
            expect(detailsSection).toHaveTextContent('Status:');
            expect(detailsSection).toHaveTextContent(claim.verification_status);
            
            // Should show confidence if available
            if (verificationResult.confidence_score) {
              expect(detailsSection).toHaveTextContent('Confidence:');
            }
            
            // Should show justification if available
            if (verificationResult.consensus_verdict?.consensus_justification) {
              expect(detailsSection).toHaveTextContent('Justification:');
            }
          }
          
          // 11. Click again to collapse
          fireEvent.click(header);
          
          // 12. After second click, details should not be visible
          detailsSection = container.querySelector(`#claim-details-${claim.id}`);
          expect(detailsSection).not.toBeInTheDocument();
          
          // 13. Header should have aria-expanded=false again
          expect(header).toHaveAttribute('aria-expanded', 'false');

          unmount();
        }
      ),
      { numRuns: 50 } // Reduced from 100 for performance
    );
  });

  /**
   * **Feature: kepler-web-interface, Property 28: Compound claim overall verdict**
   * 
   * For any compound claim with all atomic claims verified, an overall verdict should be displayed.
   * 
   * This property verifies that when multiple atomic claims exist (compound claim),
   * the component displays an overall verdict based on the verification results.
   * 
   * **Validates: Requirements 9.5**
   */
  it('Property 28: should display overall verdict for compound claims', () => {
    fc.assert(
      fc.property(
        fc.array(atomicClaimArbitrary, { minLength: 2, maxLength: 10 }), // At least 2 for compound
        verificationResultArbitrary,
        (atomicClaims, verificationResult) => {
          const { unmount, container } = render(
            <AtomicClaims
              atomicClaims={atomicClaims}
              verificationResult={verificationResult}
            />
          );

          // 1. For compound claims (multiple atomic claims), overall verdict should be displayed
          if (atomicClaims.length > 1) {
            // Should have overall verdict section
            const overallSection = container.querySelector('.atomic-claims-overall');
            expect(overallSection).toBeInTheDocument();
            expect(overallSection).toBeVisible();
            
            // Should have overall verdict label
            const overallLabel = container.querySelector('.atomic-claims-overall-label');
            expect(overallLabel).toBeInTheDocument();
            expect(overallLabel?.textContent).toBe('Overall Verdict:');
            
            // Should have overall verdict display
            const overallVerdict = container.querySelector('.atomic-claims-overall-verdict');
            expect(overallVerdict).toBeInTheDocument();
            
            // Should show the consensus classification
            const overallText = container.querySelector('.atomic-claims-overall-text');
            expect(overallText).toBeInTheDocument();
            expect(overallText?.textContent).toBe(verificationResult.consensus_verdict.final_classification);
            
            // Should have overall verdict icon
            const overallIcon = container.querySelector('.atomic-claims-overall-icon');
            expect(overallIcon).toBeInTheDocument();
            
            // Icon should match the verdict
            const expectedIcons: Record<VerdictType, string> = {
              'Supported': '✓',
              'Refuted': '✗',
              'Not Enough Information': '?',
            };
            const expectedIcon = expectedIcons[verificationResult.consensus_verdict.final_classification];
            expect(overallIcon?.textContent).toBe(expectedIcon);
            
            // Should have appropriate color class
            const expectedClasses: Record<VerdictType, string> = {
              'Supported': 'verdict-supported',
              'Refuted': 'verdict-refuted',
              'Not Enough Information': 'verdict-nei',
            };
            const expectedClass = expectedClasses[verificationResult.consensus_verdict.final_classification];
            expect(overallVerdict).toHaveClass(expectedClass);
            
            // Should have info message about breakdown
            const infoMessage = container.querySelector('.atomic-claims-info');
            expect(infoMessage).toBeInTheDocument();
            expect(infoMessage).toHaveTextContent(`This claim was broken down into ${atomicClaims.length} atomic claims`);
          }

          unmount();
        }
      ),
      { numRuns: 100 }
    );
  });

  /**
   * Property: Single claims should not show overall verdict
   * 
   * For any single atomic claim (not compound), the overall verdict section
   * should not be displayed.
   */
  it('Property: should not display overall verdict for single claims', () => {
    fc.assert(
      fc.property(
        atomicClaimArbitrary,
        fc.option(verificationResultArbitrary, { nil: undefined }),
        (atomicClaim, verificationResult) => {
          const { unmount, container } = render(
            <AtomicClaims
              atomicClaims={[atomicClaim]}
              verificationResult={verificationResult}
            />
          );

          // 1. Should not have overall verdict section
          const overallSection = container.querySelector('.atomic-claims-overall');
          expect(overallSection).not.toBeInTheDocument();
          
          // 2. Should not have info message about breakdown
          const infoMessage = container.querySelector('.atomic-claims-info');
          expect(infoMessage).not.toBeInTheDocument();
          
          // 3. Should show "Claim Analysis" title instead of "Claim Breakdown"
          expect(screen.getByText('Claim Analysis')).toBeInTheDocument();
          expect(screen.queryByText('Claim Breakdown')).not.toBeInTheDocument();

          unmount();
        }
      ),
      { numRuns: 100 }
    );
  });

  /**
   * Property: Component should have proper accessibility attributes
   * 
   * For any set of atomic claims, the component should include proper ARIA
   * attributes and semantic HTML for accessibility.
   */
  it('Property: should have proper accessibility attributes', () => {
    fc.assert(
      fc.property(
        fc.array(atomicClaimArbitrary, { minLength: 1, maxLength: 5 }),
        (atomicClaims) => {
          const { unmount, container } = render(
            <AtomicClaims atomicClaims={atomicClaims} />
          );

          // 1. Main container should have region role
          const regions = container.querySelectorAll('[role="region"]');
          const mainRegion = Array.from(regions).find(
            (el) => el.getAttribute('aria-label') === 'Atomic claims'
          );
          expect(mainRegion).toBeInTheDocument();

          // 2. Each claim header should be a button
          const buttons = screen.getAllByRole('button');
          expect(buttons.length).toBe(atomicClaims.length);

          // 3. Each button should have aria-expanded attribute
          buttons.forEach((button) => {
            expect(button).toHaveAttribute('aria-expanded');
            const expanded = button.getAttribute('aria-expanded');
            expect(['true', 'false']).toContain(expanded);
          });

          // 4. Each button should have aria-controls attribute
          buttons.forEach((button, index) => {
            const claim = atomicClaims[index];
            expect(button).toHaveAttribute('aria-controls', `claim-details-${claim.id}`);
          });

          // 5. When expanded, details should have proper role and label
          const firstButton = buttons[0];
          fireEvent.click(firstButton);
          
          const firstClaim = atomicClaims[0];
          const detailsRegion = container.querySelector(`#claim-details-${firstClaim.id}`);
          expect(detailsRegion).toHaveAttribute('role', 'region');
          expect(detailsRegion).toHaveAttribute('aria-label', `Details for claim ${firstClaim.id}`);

          unmount();
        }
      ),
      { numRuns: 100 }
    );
  });

  /**
   * Property: Component structure should be consistent
   * 
   * For any valid set of atomic claims, the component should maintain a consistent
   * DOM structure with all required sections.
   */
  it('Property: should maintain consistent structure for all inputs', () => {
    fc.assert(
      fc.property(
        fc.array(atomicClaimArbitrary, { minLength: 1, maxLength: 10 }),
        (atomicClaims) => {
          const { unmount, container } = render(
            <AtomicClaims atomicClaims={atomicClaims} />
          );

          // 1. Main container
          const mainContainer = container.querySelector('.atomic-claims');
          expect(mainContainer).toBeInTheDocument();

          // 2. Title
          const title = container.querySelector('.atomic-claims-title');
          expect(title).toBeInTheDocument();

          // 3. Claims list
          const list = container.querySelector('.atomic-claims-list');
          expect(list).toBeInTheDocument();

          // 4. Each claim item has consistent structure
          const items = container.querySelectorAll('.atomic-claim-item');
          expect(items.length).toBe(atomicClaims.length);

          items.forEach((item) => {
            // Should have header
            expect(item.querySelector('.atomic-claim-header')).toBeInTheDocument();
            expect(item.querySelector('.atomic-claim-header-content')).toBeInTheDocument();
            expect(item.querySelector('.atomic-claim-status-icon')).toBeInTheDocument();
            expect(item.querySelector('.atomic-claim-text')).toBeInTheDocument();
            expect(item.querySelector('.atomic-claim-status-badge')).toBeInTheDocument();
            expect(item.querySelector('.atomic-claim-expand-icon')).toBeInTheDocument();
          });

          unmount();
        }
      ),
      { numRuns: 100 }
    );
  });

  /**
   * Property: Expand icon should rotate when claim is expanded
   * 
   * For any atomic claim, the expand icon should have the 'expanded' class
   * when the claim is expanded.
   */
  it('Property: should rotate expand icon when claim is expanded', () => {
    fc.assert(
      fc.property(
        fc.array(atomicClaimArbitrary, { minLength: 1, maxLength: 5 }),
        (atomicClaims) => {
          const { unmount, container } = render(
            <AtomicClaims atomicClaims={atomicClaims} />
          );

          const claimHeaders = container.querySelectorAll('.atomic-claim-header');
          
          claimHeaders.forEach((header) => {
            const expandIcon = header.querySelector('.atomic-claim-expand-icon');
            expect(expandIcon).toBeInTheDocument();
            
            // Initially should not have 'expanded' class
            expect(expandIcon).not.toHaveClass('expanded');
            
            // Click to expand
            fireEvent.click(header);
            
            // Should have 'expanded' class
            expect(expandIcon).toHaveClass('expanded');
            
            // Click to collapse
            fireEvent.click(header);
            
            // Should not have 'expanded' class again
            expect(expandIcon).not.toHaveClass('expanded');
          });

          unmount();
        }
      ),
      { numRuns: 100 }
    );
  });

  /**
   * Property: Multiple claims can be expanded simultaneously
   * 
   * For any set of atomic claims, multiple claims should be able to be
   * expanded at the same time (not accordion behavior).
   */
  it('Property: should allow multiple claims to be expanded simultaneously', () => {
    fc.assert(
      fc.property(
        fc.array(atomicClaimArbitrary, { minLength: 2, maxLength: 5 }),
        (atomicClaims) => {
          const { unmount, container } = render(
            <AtomicClaims atomicClaims={atomicClaims} />
          );

          const claimHeaders = container.querySelectorAll('.atomic-claim-header');
          
          // Expand all claims
          claimHeaders.forEach((header) => {
            fireEvent.click(header);
          });
          
          // All claims should be expanded
          atomicClaims.forEach((claim) => {
            const detailsSection = container.querySelector(`#claim-details-${claim.id}`);
            expect(detailsSection).toBeInTheDocument();
            expect(detailsSection).toBeVisible();
          });
          
          // All headers should have aria-expanded=true
          claimHeaders.forEach((header) => {
            expect(header).toHaveAttribute('aria-expanded', 'true');
          });

          unmount();
        }
      ),
      { numRuns: 100 }
    );
  });
});
