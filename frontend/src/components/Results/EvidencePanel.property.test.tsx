import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import * as fc from 'fast-check';
import { EvidencePanel } from './EvidencePanel';
import type { EvidencePiece, Source } from '../../types/verification';

/**
 * Property-Based Tests for EvidencePanel Component
 * 
 * Task 12.1: Write property tests for evidence panel
 * - Property 18: Evidence source completeness
 * - Property 19: Evidence URL link behavior
 * 
 * Requirements: 6.2, 6.3, 6.4, 6.5
 * 
 * These tests use fast-check to generate random inputs and verify
 * that the component behaves correctly across all possible inputs.
 */

// Arbitraries (generators) for test data
// Generate simple strings (alphanumeric)
const simpleString = (minLength: number, maxLength: number) =>
  fc.string({ minLength, maxLength }).filter(s => s.trim().length >= minLength);

// Generate valid dates (between 2000 and 2030)
const validDateArbitrary = fc.integer({ min: Date.parse('2000-01-01'), max: Date.parse('2030-12-31') })
  .map(timestamp => new Date(timestamp));

const sourceArbitrary = fc.record({
  url: fc.webUrl(),
  title: simpleString(5, 100),
  publish_date: fc.option(validDateArbitrary.map(d => d.toISOString()), { nil: undefined }),
  domain: fc.domain(),
  content_type: fc.constantFrom('article', 'blog', 'news', 'research', 'social'),
}) as fc.Arbitrary<Source>;

const evidencePieceArbitrary = fc.record({
  id: fc.uuid(),
  source: sourceArbitrary,
  summary: simpleString(20, 300),
  raw_content: simpleString(50, 1000),
  relevance_score: fc.option(fc.double({ min: 0, max: 1, noNaN: true }), { nil: undefined }),
  credibility_score: fc.option(fc.double({ min: 0, max: 1, noNaN: true }), { nil: undefined }),
  recency_score: fc.option(fc.double({ min: 0, max: 1, noNaN: true }), { nil: undefined }),
  final_rank_score: fc.option(fc.double({ min: 0, max: 1, noNaN: true }), { nil: undefined }),
}) as fc.Arbitrary<EvidencePiece>;

const evidenceListArbitrary = fc.array(evidencePieceArbitrary, { minLength: 1, maxLength: 10 });

describe('EvidencePanel Property-Based Tests', () => {
  /**
   * **Feature: kepler-web-interface, Property 18: Evidence source completeness**
   * 
   * For any displayed evidence piece, it should include title, URL, and credibility score.
   * 
   * This property verifies that the EvidencePanel component always displays all required
   * information for each evidence source: title, URL, and credibility score.
   * 
   * **Validates: Requirements 6.2, 6.3, 6.4**
   */
  it('Property 18: should display complete evidence source information', () => {
    fc.assert(
      fc.property(
        evidenceListArbitrary,
        (evidence) => {
          const { unmount } = render(<EvidencePanel evidence={evidence} />);

          // Verify that all required information is displayed by checking the DOM structure
          const { container } = render(<EvidencePanel evidence={evidence} />);
          
          // 1. All titles should be displayed
          const titles = container.querySelectorAll('.evidence-title');
          expect(titles.length).toBe(evidence.length);
          
          // 2. All URLs should be present as clickable links
          const links = container.querySelectorAll('.evidence-link');
          expect(links.length).toBe(evidence.length);
          links.forEach((link, index) => {
            expect(link).toHaveAttribute('href', evidence[index].source.url);
            expect(link).toHaveAttribute('target', '_blank');
            expect(link).toHaveAttribute('rel', 'noopener noreferrer');
          });

          // 3. All credibility scores should be displayed as percentages
          const credibilityScores = container.querySelectorAll('.evidence-credibility-score');
          expect(credibilityScores.length).toBe(evidence.length);
          credibilityScores.forEach((scoreElement, index) => {
            const expectedScore = evidence[index].credibility_score || 0;
            const expectedPercentage = Math.round(expectedScore * 100);
            expect(scoreElement.textContent).toContain(`${expectedPercentage}%`);
          });

          // 4. All summaries should be displayed
          const summaries = container.querySelectorAll('.evidence-summary');
          expect(summaries.length).toBe(evidence.length);

          unmount();
        }
      ),
      { numRuns: 20 }
    );
  });

  /**
   * **Feature: kepler-web-interface, Property 19: Evidence URL link behavior**
   * 
   * For any evidence source URL click, the link should open in a new browser tab.
   * 
   * This property verifies that all evidence source links have the correct attributes
   * to open in a new tab (target="_blank") and include security attributes
   * (rel="noopener noreferrer").
   * 
   * **Validates: Requirements 6.5**
   */
  it('Property 19: should configure links to open in new tab with security attributes', () => {
    fc.assert(
      fc.property(
        evidenceListArbitrary,
        (evidence) => {
          const { unmount, container } = render(<EvidencePanel evidence={evidence} />);

          // Get all evidence links
          const links = container.querySelectorAll('.evidence-link');
          
          // Should have one link per evidence piece
          expect(links.length).toBe(evidence.length);

          // Verify each link has correct attributes
          links.forEach((link, index) => {
            const evidenceItem = evidence[index];

            // 1. Link should have target="_blank" to open in new tab
            expect(link).toHaveAttribute('target', '_blank');

            // 2. Link should have rel="noopener noreferrer" for security
            expect(link).toHaveAttribute('rel', 'noopener noreferrer');

            // 3. Link should point to the correct URL
            expect(link).toHaveAttribute('href', evidenceItem.source.url);

            // 4. Link should have proper aria-label for accessibility
            const ariaLabel = link.getAttribute('aria-label');
            expect(ariaLabel).toBeTruthy();
            expect(ariaLabel).toContain(evidenceItem.source.title);

            // 5. Link should be keyboard accessible (has href)
            expect(link.getAttribute('href')).toBeTruthy();
          });

          unmount();
        }
      ),
      { numRuns: 20 }
    );
  });

  /**
   * Additional property: Empty evidence list should display appropriate message
   * 
   * For any empty evidence array, the component should display a message
   * indicating no evidence is available.
   */
  it('Property: should handle empty evidence list gracefully', () => {
    fc.assert(
      fc.property(
        fc.constant([]),
        (emptyEvidence) => {
          const { unmount } = render(<EvidencePanel evidence={emptyEvidence} />);

          // Should display empty message
          const emptyMessage = screen.getByText(/no evidence sources available/i);
          expect(emptyMessage).toBeInTheDocument();

          // Should not display evidence list
          const evidenceList = document.querySelector('.evidence-list');
          expect(evidenceList).not.toBeInTheDocument();

          unmount();
        }
      ),
      { numRuns: 10 }
    );
  });

  /**
   * Property: Credibility scores should be formatted as percentages
   * 
   * For any credibility score value (0-1), it should be displayed as a
   * percentage (0-100%) with proper formatting.
   */
  it('Property: should format credibility scores as percentages', () => {
    fc.assert(
      fc.property(
        evidenceListArbitrary,
        (evidence) => {
          const { unmount, container } = render(<EvidencePanel evidence={evidence} />);

          // Get all credibility score elements
          const credibilityElements = container.querySelectorAll('.evidence-credibility-score');
          
          expect(credibilityElements.length).toBe(evidence.length);

          credibilityElements.forEach((element, index) => {
            const text = element.textContent || '';
            
            // 1. Should contain "Credibility:" label
            expect(text).toMatch(/Credibility:/i);

            // 2. Should contain percentage symbol
            expect(text).toMatch(/%/);

            // 3. Extract percentage value
            const percentageMatch = text.match(/(\d+)%/);
            expect(percentageMatch).toBeTruthy();

            if (percentageMatch) {
              const percentage = parseInt(percentageMatch[1], 10);
              
              // 4. Percentage should be in valid range
              expect(percentage).toBeGreaterThanOrEqual(0);
              expect(percentage).toBeLessThanOrEqual(100);

              // 5. Percentage should match the source data
              const expectedScore = evidence[index].credibility_score || 0;
              const expectedPercentage = Math.round(expectedScore * 100);
              expect(percentage).toBe(expectedPercentage);
            }
          });

          unmount();
        }
      ),
      { numRuns: 20 }
    );
  });

  /**
   * Property: All evidence items should be displayed
   * 
   * For any evidence array, all items should be rendered in the list.
   */
  it('Property: should display all evidence items in the list', () => {
    fc.assert(
      fc.property(
        evidenceListArbitrary,
        (evidence) => {
          const { unmount, container } = render(<EvidencePanel evidence={evidence} />);

          // Get all evidence items
          const evidenceItems = container.querySelectorAll('.evidence-item');
          
          // Should have one item per evidence piece
          expect(evidenceItems.length).toBe(evidence.length);

          // Each item should have all required child elements
          evidenceItems.forEach((item) => {
            // Should have header
            const header = item.querySelector('.evidence-header');
            expect(header).toBeInTheDocument();

            // Should have title
            const title = item.querySelector('.evidence-title');
            expect(title).toBeInTheDocument();

            // Should have credibility score
            const credibility = item.querySelector('.evidence-credibility-score');
            expect(credibility).toBeInTheDocument();

            // Should have summary
            const summary = item.querySelector('.evidence-summary');
            expect(summary).toBeInTheDocument();

            // Should have link
            const link = item.querySelector('.evidence-link');
            expect(link).toBeInTheDocument();
          });

          unmount();
        }
      ),
      { numRuns: 20 }
    );
  });

  /**
   * Property: Component should have proper accessibility attributes
   * 
   * For any evidence list, the component should include proper ARIA attributes
   * and semantic HTML for accessibility.
   */
  it('Property: should have proper accessibility attributes', () => {
    fc.assert(
      fc.property(
        evidenceListArbitrary,
        (evidence) => {
          const { unmount } = render(<EvidencePanel evidence={evidence} />);

          // 1. Main container should have region role
          const panel = screen.getByRole('region', { name: /evidence sources/i });
          expect(panel).toBeInTheDocument();

          // 2. All links should be accessible
          const links = screen.getAllByRole('link');
          expect(links.length).toBe(evidence.length);

          links.forEach((link) => {
            // Each link should have aria-label
            expect(link).toHaveAttribute('aria-label');
            
            // Each link should be keyboard accessible
            expect(link).toHaveAttribute('href');
          });

          // 3. Headings should be present for structure
          const mainHeading = screen.getByRole('heading', { name: /evidence sources/i });
          expect(mainHeading).toBeInTheDocument();

          unmount();
        }
      ),
      { numRuns: 50 }
    );
  });

  /**
   * Property: Summary text should be displayed for all evidence
   * 
   * For any evidence piece with a summary, the summary text should be
   * visible and properly formatted.
   */
  it('Property: should display summary text for all evidence pieces', () => {
    fc.assert(
      fc.property(
        evidenceListArbitrary,
        (evidence) => {
          const { unmount } = render(<EvidencePanel evidence={evidence} />);

          // Verify summaries are displayed by checking DOM structure
          const { container } = render(<EvidencePanel evidence={evidence} />);
          
          const summaries = container.querySelectorAll('.evidence-summary');
          expect(summaries.length).toBe(evidence.length);
          
          summaries.forEach((summaryElement, index) => {
            // Summary should be visible
            expect(summaryElement).toBeVisible();

            // Summary should have correct class
            expect(summaryElement).toHaveClass('evidence-summary');

            // Summary should not be empty
            expect(evidence[index].summary.length).toBeGreaterThan(0);
            
            // Summary text should match
            expect(summaryElement.textContent).toBe(evidence[index].summary);
          });

          unmount();
        }
      ),
      { numRuns: 20 }
    );
  });

  /**
   * Property: Component structure should be consistent
   * 
   * For any valid evidence list, the component should maintain a consistent
   * DOM structure with all required sections.
   */
  it('Property: should maintain consistent structure for all inputs', () => {
    fc.assert(
      fc.property(
        evidenceListArbitrary,
        (evidence) => {
          const { unmount, container } = render(<EvidencePanel evidence={evidence} />);

          // 1. Main container
          const panel = container.querySelector('.evidence-panel');
          expect(panel).toBeInTheDocument();

          // 2. Panel title
          const title = container.querySelector('.evidence-panel-title');
          expect(title).toBeInTheDocument();

          // 3. Evidence list
          const list = container.querySelector('.evidence-list');
          expect(list).toBeInTheDocument();

          // 4. Each evidence item has consistent structure
          const items = container.querySelectorAll('.evidence-item');
          items.forEach((item) => {
            expect(item.querySelector('.evidence-header')).toBeInTheDocument();
            expect(item.querySelector('.evidence-title')).toBeInTheDocument();
            expect(item.querySelector('.evidence-credibility-score')).toBeInTheDocument();
            expect(item.querySelector('.evidence-summary')).toBeInTheDocument();
            expect(item.querySelector('.evidence-link')).toBeInTheDocument();
          });

          unmount();
        }
      ),
      { numRuns: 20 }
    );
  });

  /**
   * Property: Links should have proper text content
   * 
   * For any evidence link, it should have visible text indicating it's a link
   * to view the source.
   */
  it('Property: should display proper link text for all evidence sources', () => {
    fc.assert(
      fc.property(
        evidenceListArbitrary,
        (evidence) => {
          const { unmount, container } = render(<EvidencePanel evidence={evidence} />);

          const links = container.querySelectorAll('.evidence-link');
          
          links.forEach((link) => {
            const text = link.textContent || '';
            
            // Link should have visible text
            expect(text.length).toBeGreaterThan(0);
            
            // Link should indicate it's for viewing the source
            expect(text).toMatch(/view source/i);
            
            // Link should have the arrow indicator
            expect(text).toContain('→');
          });

          unmount();
        }
      ),
      { numRuns: 20 }
    );
  });
});
