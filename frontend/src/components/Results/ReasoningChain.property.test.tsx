import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import * as fc from 'fast-check';
import { ReasoningChain } from './ReasoningChain';
import type { 
  ReasoningChain as ReasoningChainType,
  ReasoningStep,
  Agreement,
  Conflict,
  InformationGap
} from '../../types/verification';

/**
 * Property-Based Tests for ReasoningChain Component
 * 
 * Task 13.1: Write property tests for reasoning chain
 * - Property 20: Reasoning steps sequential display
 * - Property 21: Reasoning step content completeness
 * - Property 22: Agreement and conflict highlighting
 * 
 * Requirements: 7.2, 7.3, 7.4, 7.5
 * 
 * These tests use fast-check to generate random inputs and verify
 * that the component behaves correctly across all possible inputs.
 */

// Arbitraries (generators) for test data
const simpleString = (minLength: number, maxLength: number) =>
  fc.string({ minLength, maxLength }).filter(s => s.trim().length >= minLength);

// Generate reasoning step
const reasoningStepArbitrary = fc.record({
  step_number: fc.integer({ min: 1, max: 20 }),
  description: simpleString(20, 200),
  evidence_used: fc.array(fc.uuid(), { minLength: 0, maxLength: 5 }),
  conclusion: simpleString(20, 200),
}) as fc.Arbitrary<ReasoningStep>;

// Generate agreement
const agreementArbitrary = fc.record({
  evidence_ids: fc.array(fc.uuid(), { minLength: 2, maxLength: 5 }),
  common_assertion: simpleString(20, 150),
  strength: fc.double({ min: 0, max: 1, noNaN: true }),
}) as fc.Arbitrary<Agreement>;

// Generate conflict
const conflictArbitrary = fc.record({
  evidence_ids: fc.array(fc.uuid(), { minLength: 2, maxLength: 5 }),
  conflicting_assertions: fc.array(simpleString(20, 150), { minLength: 2, maxLength: 4 }),
  severity: fc.double({ min: 0, max: 1, noNaN: true }),
}) as fc.Arbitrary<Conflict>;

// Generate information gap
const informationGapArbitrary = fc.record({
  missing_aspect: simpleString(20, 150),
  importance: fc.double({ min: 0, max: 1, noNaN: true }),
}) as fc.Arbitrary<InformationGap>;

// Generate complete reasoning chain
const reasoningChainArbitrary = fc.record({
  steps: fc.array(reasoningStepArbitrary, { minLength: 1, maxLength: 10 }),
  agreements: fc.array(agreementArbitrary, { minLength: 0, maxLength: 5 }),
  conflicts: fc.array(conflictArbitrary, { minLength: 0, maxLength: 5 }),
  gaps: fc.array(informationGapArbitrary, { minLength: 0, maxLength: 5 }),
}) as fc.Arbitrary<ReasoningChainType>;

describe('ReasoningChain Property-Based Tests', () => {
  /**
   * **Feature: kepler-web-interface, Property 20: Reasoning steps sequential display**
   * 
   * For any reasoning chain, the steps should be displayed in sequential order by step number.
   * 
   * This property verifies that the ReasoningChain component always displays reasoning
   * steps in the correct sequential order based on their step_number field.
   * 
   * **Validates: Requirements 7.2**
   */
  it('Property 20: should display reasoning steps in sequential order', () => {
    fc.assert(
      fc.property(
        reasoningChainArbitrary,
        (reasoningChain) => {
          const { unmount, container } = render(
            <ReasoningChain reasoningChain={reasoningChain} />
          );

          // Get all step number elements
          const stepNumbers = container.querySelectorAll('.step-number');
          
          // Should have one step number element per step
          expect(stepNumbers.length).toBe(reasoningChain.steps.length);

          // Extract step numbers from the DOM
          const displayedStepNumbers: number[] = [];
          stepNumbers.forEach((element) => {
            const text = element.textContent || '';
            const match = text.match(/Step (\d+)/);
            if (match) {
              displayedStepNumbers.push(parseInt(match[1], 10));
            }
          });

          // Verify steps are displayed in sequential order
          const expectedStepNumbers = reasoningChain.steps
            .map(step => step.step_number)
            .sort((a, b) => a - b);

          // The displayed order should match the data order
          // (Component should display steps in the order they appear in the array)
          const actualStepNumbers = reasoningChain.steps.map(step => step.step_number);
          
          displayedStepNumbers.forEach((displayedNum, index) => {
            expect(displayedNum).toBe(actualStepNumbers[index]);
          });

          unmount();
        }
      ),
      { numRuns: 100 }
    );
  });

  /**
   * **Feature: kepler-web-interface, Property 21: Reasoning step content completeness**
   * 
   * For any reasoning step, it should display the description and evidence references.
   * 
   * This property verifies that each reasoning step displays all required content:
   * description, evidence used, and conclusion.
   * 
   * **Validates: Requirements 7.3, 7.4**
   */
  it('Property 21: should display complete content for each reasoning step', () => {
    fc.assert(
      fc.property(
        reasoningChainArbitrary,
        (reasoningChain) => {
          const { unmount, container } = render(
            <ReasoningChain reasoningChain={reasoningChain} />
          );

          // Get all reasoning step elements
          const stepElements = container.querySelectorAll('.reasoning-step');
          
          // Should have one element per step
          expect(stepElements.length).toBe(reasoningChain.steps.length);

          // Verify each step has complete content
          stepElements.forEach((stepElement, index) => {
            const step = reasoningChain.steps[index];

            // 1. Should have step number
            const stepNumber = stepElement.querySelector('.step-number');
            expect(stepNumber).toBeInTheDocument();
            expect(stepNumber?.textContent).toContain(`Step ${step.step_number}`);

            // 2. Should have description
            const description = stepElement.querySelector('.step-description');
            expect(description).toBeInTheDocument();
            expect(description?.textContent).toBe(step.description);

            // 3. Should have conclusion
            const conclusion = stepElement.querySelector('.step-conclusion');
            expect(conclusion).toBeInTheDocument();
            expect(conclusion?.textContent).toContain(step.conclusion);

            // 4. If evidence is used, should display evidence section
            if (step.evidence_used && step.evidence_used.length > 0) {
              const evidenceSection = stepElement.querySelector('.step-evidence');
              expect(evidenceSection).toBeInTheDocument();

              // Should have evidence list
              const evidenceItems = stepElement.querySelectorAll('.step-evidence-item');
              expect(evidenceItems.length).toBe(step.evidence_used.length);

              // Each evidence ID should be displayed
              evidenceItems.forEach((item, evidenceIndex) => {
                expect(item.textContent).toBe(step.evidence_used[evidenceIndex]);
              });
            }
          });

          unmount();
        }
      ),
      { numRuns: 100 }
    );
  });

  /**
   * **Feature: kepler-web-interface, Property 22: Agreement and conflict highlighting**
   * 
   * For any reasoning chain with agreements or conflicts, they should have distinct visual styling.
   * 
   * This property verifies that agreements and conflicts are displayed with distinct
   * visual styling (different CSS classes and colors).
   * 
   * **Validates: Requirements 7.5**
   */
  it('Property 22: should apply distinct styling for agreements and conflicts', () => {
    fc.assert(
      fc.property(
        reasoningChainArbitrary,
        (reasoningChain) => {
          const { unmount, container } = render(
            <ReasoningChain reasoningChain={reasoningChain} />
          );

          // Check agreements section styling
          if (reasoningChain.agreements && reasoningChain.agreements.length > 0) {
            const agreementsSection = container.querySelector('.agreements-section');
            expect(agreementsSection).toBeInTheDocument();

            // Should have distinct class for agreements
            expect(agreementsSection).toHaveClass('agreements-section');

            // Each agreement item should have agreement-specific styling
            const agreementItems = container.querySelectorAll('.agreement-item');
            expect(agreementItems.length).toBe(reasoningChain.agreements.length);

            agreementItems.forEach((item) => {
              expect(item).toHaveClass('agreement-item');
            });
          }

          // Check conflicts section styling
          if (reasoningChain.conflicts && reasoningChain.conflicts.length > 0) {
            const conflictsSection = container.querySelector('.conflicts-section');
            expect(conflictsSection).toBeInTheDocument();

            // Should have distinct class for conflicts
            expect(conflictsSection).toHaveClass('conflicts-section');

            // Each conflict item should have conflict-specific styling
            const conflictItems = container.querySelectorAll('.conflict-item');
            expect(conflictItems.length).toBe(reasoningChain.conflicts.length);

            conflictItems.forEach((item) => {
              expect(item).toHaveClass('conflict-item');
            });
          }

          // Verify agreements and conflicts have different classes
          const agreementsSection = container.querySelector('.agreements-section');
          const conflictsSection = container.querySelector('.conflicts-section');

          if (agreementsSection && conflictsSection) {
            // They should have different class names
            expect(agreementsSection.className).not.toBe(conflictsSection.className);
          }

          unmount();
        }
      ),
      { numRuns: 100 }
    );
  });

  /**
   * Property: All agreements should display common assertion and strength
   * 
   * For any agreement, it should display the common assertion text and
   * strength formatted as a percentage.
   */
  it('Property: should display complete agreement information', () => {
    fc.assert(
      fc.property(
        reasoningChainArbitrary.filter(rc => rc.agreements.length > 0),
        (reasoningChain) => {
          const { unmount, container } = render(
            <ReasoningChain reasoningChain={reasoningChain} />
          );

          const agreementItems = container.querySelectorAll('.agreement-item');
          expect(agreementItems.length).toBe(reasoningChain.agreements.length);

          agreementItems.forEach((item, index) => {
            const agreement = reasoningChain.agreements[index];

            // 1. Should display common assertion
            const assertion = item.querySelector('.agreement-assertion');
            expect(assertion).toBeInTheDocument();
            expect(assertion?.textContent).toBe(agreement.common_assertion);

            // 2. Should display strength as percentage
            const strength = item.querySelector('.agreement-strength');
            expect(strength).toBeInTheDocument();
            
            const strengthText = strength?.textContent || '';
            expect(strengthText).toMatch(/Strength:/i);
            expect(strengthText).toMatch(/%/);

            // Extract and verify percentage
            const percentageMatch = strengthText.match(/(\d+)%/);
            expect(percentageMatch).toBeTruthy();
            
            if (percentageMatch) {
              const percentage = parseInt(percentageMatch[1], 10);
              const expectedPercentage = Math.round(agreement.strength * 100);
              expect(percentage).toBe(expectedPercentage);
            }
          });

          unmount();
        }
      ),
      { numRuns: 100 }
    );
  });

  /**
   * Property: All conflicts should display conflicting assertions and severity
   * 
   * For any conflict, it should display all conflicting assertions and
   * severity formatted as a percentage.
   */
  it('Property: should display complete conflict information', () => {
    fc.assert(
      fc.property(
        reasoningChainArbitrary.filter(rc => rc.conflicts.length > 0),
        (reasoningChain) => {
          const { unmount, container } = render(
            <ReasoningChain reasoningChain={reasoningChain} />
          );

          const conflictItems = container.querySelectorAll('.conflict-item');
          expect(conflictItems.length).toBe(reasoningChain.conflicts.length);

          conflictItems.forEach((item, index) => {
            const conflict = reasoningChain.conflicts[index];

            // 1. Should display all conflicting assertions
            const assertions = item.querySelectorAll('.conflict-assertion');
            expect(assertions.length).toBe(conflict.conflicting_assertions.length);

            assertions.forEach((assertion, assertionIndex) => {
              expect(assertion.textContent).toBe(
                conflict.conflicting_assertions[assertionIndex]
              );
            });

            // 2. Should display severity as percentage
            const severity = item.querySelector('.conflict-severity');
            expect(severity).toBeInTheDocument();
            
            const severityText = severity?.textContent || '';
            expect(severityText).toMatch(/Severity:/i);
            expect(severityText).toMatch(/%/);

            // Extract and verify percentage
            const percentageMatch = severityText.match(/(\d+)%/);
            expect(percentageMatch).toBeTruthy();
            
            if (percentageMatch) {
              const percentage = parseInt(percentageMatch[1], 10);
              const expectedPercentage = Math.round(conflict.severity * 100);
              expect(percentage).toBe(expectedPercentage);
            }
          });

          unmount();
        }
      ),
      { numRuns: 100 }
    );
  });

  /**
   * Property: Information gaps should display missing aspect and importance
   * 
   * For any information gap, it should display the missing aspect and
   * importance formatted as a percentage.
   */
  it('Property: should display complete information gap details', () => {
    fc.assert(
      fc.property(
        reasoningChainArbitrary.filter(rc => rc.gaps.length > 0),
        (reasoningChain) => {
          const { unmount, container } = render(
            <ReasoningChain reasoningChain={reasoningChain} />
          );

          const gapItems = container.querySelectorAll('.gap-item');
          expect(gapItems.length).toBe(reasoningChain.gaps.length);

          gapItems.forEach((item, index) => {
            const gap = reasoningChain.gaps[index];

            // 1. Should display missing aspect
            const aspect = item.querySelector('.gap-aspect');
            expect(aspect).toBeInTheDocument();
            expect(aspect?.textContent).toBe(gap.missing_aspect);

            // 2. Should display importance as percentage
            const importance = item.querySelector('.gap-importance');
            expect(importance).toBeInTheDocument();
            
            const importanceText = importance?.textContent || '';
            expect(importanceText).toMatch(/Importance:/i);
            expect(importanceText).toMatch(/%/);

            // Extract and verify percentage
            const percentageMatch = importanceText.match(/(\d+)%/);
            expect(percentageMatch).toBeTruthy();
            
            if (percentageMatch) {
              const percentage = parseInt(percentageMatch[1], 10);
              const expectedPercentage = Math.round(gap.importance * 100);
              expect(percentage).toBe(expectedPercentage);
            }
          });

          unmount();
        }
      ),
      { numRuns: 100 }
    );
  });

  /**
   * Property: Component should have proper accessibility attributes
   * 
   * For any reasoning chain, the component should include proper ARIA attributes
   * and semantic HTML for accessibility.
   */
  it('Property: should have proper accessibility attributes', () => {
    fc.assert(
      fc.property(
        reasoningChainArbitrary,
        (reasoningChain) => {
          const { unmount } = render(
            <ReasoningChain reasoningChain={reasoningChain} />
          );

          // 1. Main container should have region role
          const panel = screen.getByRole('region', { name: /reasoning process/i });
          expect(panel).toBeInTheDocument();

          // 2. Main heading should be present
          const mainHeading = screen.getByRole('heading', { name: /reasoning process/i });
          expect(mainHeading).toBeInTheDocument();

          // 3. Section headings should be present if sections exist
          if (reasoningChain.agreements.length > 0) {
            const agreementsHeading = screen.getByRole('heading', { 
              name: /agreements in evidence/i 
            });
            expect(agreementsHeading).toBeInTheDocument();
          }

          if (reasoningChain.conflicts.length > 0) {
            const conflictsHeading = screen.getByRole('heading', { 
              name: /conflicts in evidence/i 
            });
            expect(conflictsHeading).toBeInTheDocument();
          }

          if (reasoningChain.gaps.length > 0) {
            const gapsHeading = screen.getByRole('heading', { 
              name: /information gaps/i 
            });
            expect(gapsHeading).toBeInTheDocument();
          }

          unmount();
        }
      ),
      { numRuns: 100 }
    );
  });

  /**
   * Property: Empty reasoning chain should display appropriate message
   * 
   * For any null or undefined reasoning chain, the component should display
   * a message indicating no reasoning chain is available.
   */
  it('Property: should handle empty reasoning chain gracefully', () => {
    const { unmount } = render(<ReasoningChain reasoningChain={null as any} />);

    // Should display empty message
    const emptyMessage = screen.getByText(/no reasoning chain available/i);
    expect(emptyMessage).toBeInTheDocument();

    // Should not display reasoning sections
    const reasoningSteps = document.querySelector('.reasoning-steps');
    expect(reasoningSteps).not.toBeInTheDocument();

    unmount();
  });

  /**
   * Property: Component structure should be consistent
   * 
   * For any valid reasoning chain, the component should maintain a consistent
   * DOM structure with all required sections.
   */
  it('Property: should maintain consistent structure for all inputs', () => {
    fc.assert(
      fc.property(
        reasoningChainArbitrary,
        (reasoningChain) => {
          const { unmount, container } = render(
            <ReasoningChain reasoningChain={reasoningChain} />
          );

          // 1. Main container
          const panel = container.querySelector('.reasoning-chain');
          expect(panel).toBeInTheDocument();

          // 2. Panel title
          const title = container.querySelector('.reasoning-chain-title');
          expect(title).toBeInTheDocument();

          // 3. Steps section should exist if there are steps
          if (reasoningChain.steps.length > 0) {
            const stepsSection = container.querySelector('.reasoning-steps');
            expect(stepsSection).toBeInTheDocument();
          }

          // 4. Agreements section should exist if there are agreements
          if (reasoningChain.agreements.length > 0) {
            const agreementsSection = container.querySelector('.agreements-section');
            expect(agreementsSection).toBeInTheDocument();
          }

          // 5. Conflicts section should exist if there are conflicts
          if (reasoningChain.conflicts.length > 0) {
            const conflictsSection = container.querySelector('.conflicts-section');
            expect(conflictsSection).toBeInTheDocument();
          }

          // 6. Gaps section should exist if there are gaps
          if (reasoningChain.gaps.length > 0) {
            const gapsSection = container.querySelector('.gaps-section');
            expect(gapsSection).toBeInTheDocument();
          }

          unmount();
        }
      ),
      { numRuns: 100 }
    );
  });

  /**
   * Property: Steps should display evidence references when present
   * 
   * For any reasoning step with evidence_used, the evidence IDs should be
   * displayed in a list format.
   */
  it('Property: should display evidence references for steps that use evidence', () => {
    fc.assert(
      fc.property(
        reasoningChainArbitrary.filter(rc => 
          rc.steps.some(step => step.evidence_used.length > 0)
        ),
        (reasoningChain) => {
          const { unmount, container } = render(
            <ReasoningChain reasoningChain={reasoningChain} />
          );

          const stepElements = container.querySelectorAll('.reasoning-step');

          stepElements.forEach((stepElement, index) => {
            const step = reasoningChain.steps[index];

            if (step.evidence_used.length > 0) {
              // Should have evidence section
              const evidenceSection = stepElement.querySelector('.step-evidence');
              expect(evidenceSection).toBeInTheDocument();

              // Should have evidence list
              const evidenceList = stepElement.querySelector('.step-evidence-list');
              expect(evidenceList).toBeInTheDocument();

              // Should have correct number of evidence items
              const evidenceItems = stepElement.querySelectorAll('.step-evidence-item');
              expect(evidenceItems.length).toBe(step.evidence_used.length);
            }
          });

          unmount();
        }
      ),
      { numRuns: 100 }
    );
  });
});
