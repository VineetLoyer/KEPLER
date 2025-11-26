import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import * as fc from 'fast-check';
import { ModelVerdicts } from './ModelVerdicts';
import type { ConsensusVerdict, Verdict, VerdictType } from '../../types/verification';

/**
 * Property-Based Tests for ModelVerdicts Component
 * 
 * Task 14.1: Write property tests for model verdicts
 * - Property 23: Individual verdict display completeness
 * - Property 24: Disagreement visualization
 * 
 * Requirements: 8.2, 8.3, 8.4, 8.5
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

const modelIdArbitrary = fc.constantFrom(
  'gpt-4',
  'gpt-3.5-turbo',
  'claude-3-opus',
  'claude-3-sonnet',
  'gemini-pro',
  'gemini-ultra',
  'llama-2-70b',
  'mistral-large'
);

const verdictArbitrary = fc.record({
  model_id: modelIdArbitrary,
  classification: verdictTypeArbitrary,
  justification: fc.string({ minLength: 20, maxLength: 500 }),
  confidence: fc.double({ min: 0, max: 1, noNaN: true }),
  evidence_references: fc.array(fc.string({ minLength: 5, maxLength: 20 }), { minLength: 0, maxLength: 5 }),
}) as fc.Arbitrary<Verdict>;

const consensusVerdictArbitrary = fc.record({
  final_classification: verdictTypeArbitrary,
  consensus_justification: fc.string({ minLength: 20, maxLength: 500 }),
  individual_verdicts: fc.array(verdictArbitrary, { minLength: 1, maxLength: 5 }),
  agreement_level: fc.double({ min: 0, max: 1, noNaN: true }),
}) as fc.Arbitrary<ConsensusVerdict>;

describe('ModelVerdicts Property-Based Tests', () => {
  /**
   * **Feature: kepler-web-interface, Property 23: Individual verdict display completeness**
   * 
   * For any individual model verdict, it should display model name, classification, and justification.
   * 
   * This property verifies that the ModelVerdicts component always displays all required
   * information for each individual model verdict: model name/ID, classification, and justification.
   * 
   * **Validates: Requirements 8.2, 8.3, 8.4**
   */
  it('Property 23: should display complete individual verdict information', () => {
    fc.assert(
      fc.property(
        consensusVerdictArbitrary,
        (consensusVerdict) => {
          const { unmount, container } = render(
            <ModelVerdicts consensusVerdict={consensusVerdict} />
          );

          const { individual_verdicts } = consensusVerdict;

          // Verify that all required information is displayed for each verdict:
          
          // 1. All model names/IDs should be displayed
          const modelNameElements = container.querySelectorAll('.model-verdict-model-name');
          expect(modelNameElements.length).toBe(individual_verdicts.length);
          
          individual_verdicts.forEach((verdict) => {
            // Find the model name element with this text
            const modelName = Array.from(modelNameElements).find(
              (el) => el.textContent === verdict.model_id
            );
            expect(modelName).toBeTruthy();
          });

          // 2. All classifications should be displayed
          const classificationBadges = container.querySelectorAll('.model-verdict-badge');
          expect(classificationBadges.length).toBe(individual_verdicts.length);
          
          individual_verdicts.forEach((verdict) => {
            // Find the badge with this classification text
            const badge = Array.from(classificationBadges).find(
              (el) => el.textContent === verdict.classification
            );
            expect(badge).toBeTruthy();
          });

          // 3. All justifications should be displayed
          const justificationTexts = container.querySelectorAll('.model-verdict-justification-text');
          expect(justificationTexts.length).toBe(individual_verdicts.length);
          
          individual_verdicts.forEach((verdict) => {
            const justificationElement = Array.from(justificationTexts).find(
              (el) => el.textContent === verdict.justification
            );
            expect(justificationElement).toBeTruthy();
            expect(justificationElement).toBeVisible();
          });

          // 4. All confidence scores should be displayed
          const confidenceBars = container.querySelectorAll('.confidence-bar-container');
          expect(confidenceBars.length).toBe(individual_verdicts.length);

          // 5. Each verdict card should have all required sections
          const verdictCards = container.querySelectorAll('.model-verdict-card');
          expect(verdictCards.length).toBe(individual_verdicts.length);
          
          verdictCards.forEach((card) => {
            // Should have header with model info
            expect(card.querySelector('.model-verdict-header')).toBeInTheDocument();
            expect(card.querySelector('.model-verdict-model-info')).toBeInTheDocument();
            expect(card.querySelector('.model-verdict-model-name')).toBeInTheDocument();
            
            // Should have classification badge
            expect(card.querySelector('.model-verdict-badge')).toBeInTheDocument();
            
            // Should have confidence section
            expect(card.querySelector('.model-verdict-confidence')).toBeInTheDocument();
            
            // Should have justification section
            expect(card.querySelector('.model-verdict-justification')).toBeInTheDocument();
            expect(card.querySelector('.model-verdict-justification-title')).toBeInTheDocument();
            expect(card.querySelector('.model-verdict-justification-text')).toBeInTheDocument();
          });

          unmount();
        }
      ),
      { numRuns: 100 }
    );
  });

  /**
   * **Feature: kepler-web-interface, Property 24: Disagreement visualization**
   * 
   * For any set of model verdicts where classifications differ, the frontend should
   * visually indicate the disagreement.
   * 
   * This property verifies that when models disagree (have different classifications),
   * the component visually highlights the disagreement with special styling and indicators.
   * 
   * **Validates: Requirements 8.5**
   */
  it('Property 24: should visually indicate disagreements between models', () => {
    fc.assert(
      fc.property(
        consensusVerdictArbitrary,
        (consensusVerdict) => {
          const { unmount, container } = render(
            <ModelVerdicts consensusVerdict={consensusVerdict} />
          );

          const { individual_verdicts, final_classification } = consensusVerdict;

          // Determine if there are any disagreements
          const hasDisagreements = individual_verdicts.some(
            (verdict) => verdict.classification !== final_classification
          );

          // Count disagreeing verdicts
          const disagreeingVerdicts = individual_verdicts.filter(
            (verdict) => verdict.classification !== final_classification
          );

          if (hasDisagreements) {
            // 1. Disagreement badge should be displayed in header
            const disagreementBadge = screen.getByText('Disagreements Detected');
            expect(disagreementBadge).toBeInTheDocument();
            expect(disagreementBadge).toHaveClass('model-verdicts-disagreement-badge');
            expect(disagreementBadge).toBeVisible();

            // 2. Disagreeing verdict cards should have special class
            const disagreeingCards = container.querySelectorAll('.model-verdict-disagreeing');
            expect(disagreeingCards.length).toBe(disagreeingVerdicts.length);

            // 3. Each disagreeing card should have disagreement indicator
            disagreeingCards.forEach((card) => {
              const indicator = card.querySelector('.model-verdict-disagreement-indicator');
              expect(indicator).toBeInTheDocument();
              expect(indicator?.textContent).toBe('Disagrees with consensus');
              expect(indicator).toBeVisible();
            });

            // 4. Verify that only disagreeing verdicts have the special styling
            const allCards = container.querySelectorAll('.model-verdict-card');
            allCards.forEach((card, index) => {
              const verdict = individual_verdicts[index];
              const isDisagreeing = verdict.classification !== final_classification;
              
              if (isDisagreeing) {
                expect(card).toHaveClass('model-verdict-disagreeing');
                expect(card.querySelector('.model-verdict-disagreement-indicator')).toBeInTheDocument();
              } else {
                expect(card).not.toHaveClass('model-verdict-disagreeing');
                expect(card.querySelector('.model-verdict-disagreement-indicator')).not.toBeInTheDocument();
              }
            });

          } else {
            // 5. When all models agree, no disagreement indicators should be shown
            const disagreementBadge = screen.queryByText('Disagreements Detected');
            expect(disagreementBadge).not.toBeInTheDocument();

            const disagreeingCards = container.querySelectorAll('.model-verdict-disagreeing');
            expect(disagreeingCards.length).toBe(0);

            const disagreementIndicators = container.querySelectorAll('.model-verdict-disagreement-indicator');
            expect(disagreementIndicators.length).toBe(0);
          }

          unmount();
        }
      ),
      { numRuns: 100 }
    );
  });

  /**
   * Property: Confidence scores should be displayed for all models
   * 
   * For any model verdict with a confidence score, the score should be displayed
   * as a visual indicator (progress bar) with percentage.
   */
  it('Property: should display confidence scores for all model verdicts', () => {
    fc.assert(
      fc.property(
        consensusVerdictArbitrary,
        (consensusVerdict) => {
          const { unmount, container } = render(
            <ModelVerdicts consensusVerdict={consensusVerdict} />
          );

          const { individual_verdicts } = consensusVerdict;

          // 1. Each verdict should have a confidence bar
          const confidenceBars = container.querySelectorAll('.confidence-bar-container');
          expect(confidenceBars.length).toBe(individual_verdicts.length);

          // 2. Each confidence bar should have proper structure
          confidenceBars.forEach((bar) => {
            // Should have track
            const track = bar.querySelector('.confidence-bar-track');
            expect(track).toBeInTheDocument();

            // Should have fill
            const fill = bar.querySelector('.confidence-bar-fill');
            expect(fill).toBeInTheDocument();

            // Should have percentage display
            const percentage = bar.querySelector('.confidence-bar-percentage');
            expect(percentage).toBeInTheDocument();
            expect(percentage?.textContent).toMatch(/%$/);
          });

          // 3. Confidence values should match the data
          const verdictCards = container.querySelectorAll('.model-verdict-card');
          verdictCards.forEach((card, index) => {
            const verdict = individual_verdicts[index];
            // ConfidenceBar uses Math.round() which doesn't include decimals for whole numbers
            const expectedPercentage = Math.round(verdict.confidence * 100) + '%';
            
            const percentageElement = card.querySelector('.confidence-bar-percentage');
            expect(percentageElement?.textContent).toBe(expectedPercentage);
          });

          unmount();
        }
      ),
      { numRuns: 100 }
    );
  });

  /**
   * Property: Verdict classifications should have distinct styling
   * 
   * For any verdict classification, it should have a specific color class
   * that provides distinct visual styling.
   */
  it('Property: should apply distinct styling for different verdict classifications', () => {
    fc.assert(
      fc.property(
        consensusVerdictArbitrary,
        (consensusVerdict) => {
          const { unmount, container } = render(
            <ModelVerdicts consensusVerdict={consensusVerdict} />
          );

          const { individual_verdicts } = consensusVerdict;

          // Get all verdict badges
          const badges = container.querySelectorAll('.model-verdict-badge');
          expect(badges.length).toBe(individual_verdicts.length);

          // Verify each badge has the correct verdict color class
          badges.forEach((badge, index) => {
            const verdict = individual_verdicts[index];
            const expectedClasses = {
              'Supported': 'verdict-supported',
              'Refuted': 'verdict-refuted',
              'Not Enough Information': 'verdict-nei',
            };

            const expectedClass = expectedClasses[verdict.classification];
            expect(badge).toHaveClass(expectedClass);
          });

          // Verify that different classifications have different classes
          const uniqueClassifications = new Set(
            individual_verdicts.map((v) => v.classification)
          );

          if (uniqueClassifications.size > 1) {
            const classificationToClass = new Map<VerdictType, string>();
            
            badges.forEach((badge, index) => {
              const classification = individual_verdicts[index].classification;
              const classes = badge.className;
              
              if (!classificationToClass.has(classification)) {
                classificationToClass.set(classification, classes);
              } else {
                // Same classification should have same classes
                expect(classes).toBe(classificationToClass.get(classification));
              }
            });

            // Different classifications should have different classes
            const classValues = Array.from(classificationToClass.values());
            const uniqueClasses = new Set(classValues);
            expect(uniqueClasses.size).toBe(classificationToClass.size);
          }

          unmount();
        }
      ),
      { numRuns: 100 }
    );
  });

  /**
   * Property: Evidence references should be displayed when available
   * 
   * For any verdict with evidence references, they should be displayed
   * in a list format.
   */
  it('Property: should display evidence references when available', () => {
    fc.assert(
      fc.property(
        consensusVerdictArbitrary,
        (consensusVerdict) => {
          const { unmount, container } = render(
            <ModelVerdicts consensusVerdict={consensusVerdict} />
          );

          const { individual_verdicts } = consensusVerdict;

          individual_verdicts.forEach((verdict, index) => {
            const card = container.querySelectorAll('.model-verdict-card')[index];
            
            if (verdict.evidence_references && verdict.evidence_references.length > 0) {
              // Should have evidence section
              const evidenceSection = card.querySelector('.model-verdict-evidence');
              expect(evidenceSection).toBeInTheDocument();

              // Should have evidence title
              const evidenceTitle = card.querySelector('.model-verdict-evidence-title');
              expect(evidenceTitle).toBeInTheDocument();
              expect(evidenceTitle?.textContent).toBe('Evidence Used');

              // Should have evidence list
              const evidenceList = card.querySelector('.model-verdict-evidence-list');
              expect(evidenceList).toBeInTheDocument();

              // Should have correct number of evidence items
              const evidenceItems = card.querySelectorAll('.model-verdict-evidence-item');
              expect(evidenceItems.length).toBe(verdict.evidence_references.length);

              // Each evidence reference should be displayed
              verdict.evidence_references.forEach((ref) => {
                const refElement = Array.from(evidenceItems).find(
                  (el) => el.textContent === ref
                );
                expect(refElement).toBeTruthy();
              });
            } else {
              // Should not have evidence section if no references
              const evidenceSection = card.querySelector('.model-verdict-evidence');
              expect(evidenceSection).not.toBeInTheDocument();
            }
          });

          unmount();
        }
      ),
      { numRuns: 100 }
    );
  });

  /**
   * Property: Agreement level should be displayed
   * 
   * For any consensus verdict, the agreement level should be displayed
   * as a percentage in the summary section.
   */
  it('Property: should display agreement level in summary', () => {
    fc.assert(
      fc.property(
        consensusVerdictArbitrary,
        (consensusVerdict) => {
          const { unmount, container } = render(
            <ModelVerdicts consensusVerdict={consensusVerdict} />
          );

          // 1. Summary section should exist
          const summary = container.querySelector('.model-verdicts-summary');
          expect(summary).toBeInTheDocument();

          // 2. Agreement section should exist
          const agreementSection = container.querySelector('.model-verdicts-agreement');
          expect(agreementSection).toBeInTheDocument();

          // 3. Agreement label should be displayed
          const agreementLabel = container.querySelector('.model-verdicts-agreement-label');
          expect(agreementLabel).toBeInTheDocument();
          expect(agreementLabel?.textContent).toBe('Agreement Level:');

          // 4. Agreement value should be displayed as percentage
          const agreementValue = container.querySelector('.model-verdicts-agreement-value');
          expect(agreementValue).toBeInTheDocument();
          
          const expectedPercentage = Math.round(consensusVerdict.agreement_level * 100) + '%';
          expect(agreementValue?.textContent).toBe(expectedPercentage);

          // 5. Percentage should be in valid range
          const percentageText = agreementValue?.textContent || '';
          const percentageMatch = percentageText.match(/(\d+)%/);
          expect(percentageMatch).toBeTruthy();
          
          if (percentageMatch) {
            const percentage = parseInt(percentageMatch[1], 10);
            expect(percentage).toBeGreaterThanOrEqual(0);
            expect(percentage).toBeLessThanOrEqual(100);
          }

          unmount();
        }
      ),
      { numRuns: 100 }
    );
  });

  /**
   * Property: Component should have proper accessibility attributes
   * 
   * For any consensus verdict, the component should include proper ARIA
   * attributes and semantic HTML for accessibility.
   */
  it('Property: should have proper accessibility attributes', () => {
    fc.assert(
      fc.property(
        consensusVerdictArbitrary,
        (consensusVerdict) => {
          const { unmount } = render(
            <ModelVerdicts consensusVerdict={consensusVerdict} />
          );

          // 1. Main container should have region role
          const region = screen.getByRole('region', { name: /individual model verdicts/i });
          expect(region).toBeInTheDocument();

          // 2. Main title should be a heading
          const mainHeading = screen.getByRole('heading', { name: /individual model verdicts/i });
          expect(mainHeading).toBeInTheDocument();

          // 3. Each verdict card should have proper structure
          const justificationTitles = screen.getAllByText('Justification');
          expect(justificationTitles.length).toBe(consensusVerdict.individual_verdicts.length);

          unmount();
        }
      ),
      { numRuns: 100 }
    );
  });

  /**
   * Property: Component structure should be consistent
   * 
   * For any valid consensus verdict, the component should maintain a consistent
   * DOM structure with all required sections.
   */
  it('Property: should maintain consistent structure for all inputs', () => {
    fc.assert(
      fc.property(
        consensusVerdictArbitrary,
        (consensusVerdict) => {
          const { unmount, container } = render(
            <ModelVerdicts consensusVerdict={consensusVerdict} />
          );

          // 1. Main container
          const mainContainer = container.querySelector('.model-verdicts');
          expect(mainContainer).toBeInTheDocument();

          // 2. Header section
          const header = container.querySelector('.model-verdicts-header');
          expect(header).toBeInTheDocument();

          // 3. Title
          const title = container.querySelector('.model-verdicts-title');
          expect(title).toBeInTheDocument();

          // 4. Verdicts list
          const list = container.querySelector('.model-verdicts-list');
          expect(list).toBeInTheDocument();

          // 5. Summary section
          const summary = container.querySelector('.model-verdicts-summary');
          expect(summary).toBeInTheDocument();

          // 6. Each verdict card has consistent structure
          const cards = container.querySelectorAll('.model-verdict-card');
          expect(cards.length).toBe(consensusVerdict.individual_verdicts.length);

          cards.forEach((card) => {
            expect(card.querySelector('.model-verdict-header')).toBeInTheDocument();
            expect(card.querySelector('.model-verdict-model-info')).toBeInTheDocument();
            expect(card.querySelector('.model-verdict-model-name')).toBeInTheDocument();
            expect(card.querySelector('.model-verdict-badge')).toBeInTheDocument();
            expect(card.querySelector('.model-verdict-confidence')).toBeInTheDocument();
            expect(card.querySelector('.model-verdict-justification')).toBeInTheDocument();
          });

          unmount();
        }
      ),
      { numRuns: 100 }
    );
  });
});
