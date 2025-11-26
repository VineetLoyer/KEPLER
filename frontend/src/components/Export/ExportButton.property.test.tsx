import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import * as fc from 'fast-check';
import { ExportButton } from './ExportButton';
import type { VerificationResult, VerdictType } from '../../types/verification';

/**
 * Property-Based Tests for ExportButton Component
 * 
 * Task 18.1: Write property tests for export
 * - Property 41: JSON export completeness
 * - Property 42: PDF export generation
 * 
 * Requirements: 14.3, 14.4, 14.5
 */

// Mock jsPDF
vi.mock('jspdf', () => {
  return {
    jsPDF: vi.fn().mockImplementation(() => ({
      internal: {
        pageSize: {
          getWidth: () => 210,
        },
      },
      setFontSize: vi.fn(),
      setFont: vi.fn(),
      splitTextToSize: vi.fn((text: string) => [text]),
      text: vi.fn(),
      addPage: vi.fn(),
      save: vi.fn(),
    })),
  };
});

// Arbitraries for generating test data

const verdictTypeArbitrary = fc.constantFrom<VerdictType>(
  'Supported',
  'Refuted',
  'Not Enough Information'
);

const verificationResultArbitrary: fc.Arbitrary<VerificationResult> = fc.record({
  session_id: fc.uuid(),
  original_input: fc.record({
    text: fc.string({ minLength: 10, maxLength: 200 }),
  }),
  atomic_claims: fc.array(
    fc.record({
      claim_text: fc.string({ minLength: 10, maxLength: 200 }),
      verification_status: verdictTypeArbitrary,
      evidence: fc.constant([]),
      reasoning: fc.string({ minLength: 20, maxLength: 200 }),
    }),
    { minLength: 0, maxLength: 5 }
  ),
  consensus_verdict: fc.record({
    final_classification: verdictTypeArbitrary,
    consensus_justification: fc.string({ minLength: 20, maxLength: 300 }),
    individual_verdicts: fc.constant([]),
    agreement_level: fc.double({ min: 0, max: 1, noNaN: true }),
  }),
  confidence_score: fc.record({
    overall_score: fc.double({ min: 0, max: 1, noNaN: true }),
    source_reliability: fc.double({ min: 0, max: 1, noNaN: true }),
    model_agreement: fc.double({ min: 0, max: 1, noNaN: true }),
    evidence_recency: fc.double({ min: 0, max: 1, noNaN: true }),
    structured_justification: fc.record({
      summary: fc.string({ minLength: 20, maxLength: 200 }),
      key_evidence: fc.constant([]),
      reasoning_chain: fc.record({
        steps: fc.array(
          fc.record({
            step_number: fc.integer({ min: 1, max: 10 }),
            description: fc.string({ minLength: 20, maxLength: 200 }),
            evidence_used: fc.array(fc.string(), { maxLength: 3 }),
            conclusion: fc.string({ minLength: 20, maxLength: 200 }),
          }),
          { minLength: 0, maxLength: 5 }
        ),
        agreements: fc.constant([]),
        conflicts: fc.constant([]),
        gaps: fc.constant([]),
      }),
      source_links: fc.array(
        fc.record({
          title: fc.string({ minLength: 5, maxLength: 100 }),
          url: fc.webUrl(),
          credibility_score: fc.double({ min: 0, max: 1, noNaN: true }),
        }),
        { minLength: 0, maxLength: 5 }
      ),
    }),
  }),
  processing_metadata: fc.constant({}),
  trace_log: fc.constant([]),
});

describe('ExportButton Property-Based Tests', () => {
  let createObjectURLSpy: ReturnType<typeof vi.spyOn>;
  let revokeObjectURLSpy: ReturnType<typeof vi.spyOn>;
  let createElementSpy: ReturnType<typeof vi.spyOn>;

  beforeEach(() => {
    // Mock URL.createObjectURL and URL.revokeObjectURL
    createObjectURLSpy = vi.spyOn(URL, 'createObjectURL').mockReturnValue('blob:mock-url');
    revokeObjectURLSpy = vi.spyOn(URL, 'revokeObjectURL').mockImplementation(() => {});

    // Mock document.createElement for download link
    const mockLink = {
      href: '',
      download: '',
      click: vi.fn(),
    } as unknown as HTMLAnchorElement;

    createElementSpy = vi.spyOn(document, 'createElement').mockReturnValue(mockLink);
  });

  afterEach(() => {
    createObjectURLSpy.mockRestore();
    revokeObjectURLSpy.mockRestore();
    createElementSpy.mockRestore();
  });

  /**
   * **Feature: kepler-web-interface, Property 41: JSON export completeness**
   * 
   * For any JSON export, the file should contain all verification details
   * including evidence sources and reasoning chain.
   * 
   * **Validates: Requirements 14.3, 14.5**
   */
  it('Property 41: should export complete verification data as JSON', () => {
    fc.assert(
      fc.property(
        verificationResultArbitrary,
        (results) => {
          const { unmount } = render(<ExportButton results={results} />);

          try {
            // Open dropdown
            const exportButton = screen.getByRole('button', { name: /Export verification results/i });
            fireEvent.click(exportButton);

            // Click JSON export option
            const jsonOption = screen.getByRole('menuitem', { name: /Export as JSON/i });
            fireEvent.click(jsonOption);

            // Verify that createObjectURL was called
            expect(createObjectURLSpy).toHaveBeenCalled();

            // Get the blob that was created
            const blobCall = createObjectURLSpy.mock.calls[0];
            const blob = blobCall[0] as Blob;

            // Verify blob type
            expect(blob.type).toBe('application/json');

            // Read blob content
            return new Promise<boolean>((resolve) => {
              const reader = new FileReader();
              reader.onload = () => {
                const jsonContent = reader.result as string;
                const exportedData = JSON.parse(jsonContent);

                // Verify all required fields are present
                expect(exportedData.session_id).toBe(results.session_id);
                expect(exportedData.consensus_verdict).toBeDefined();
                expect(exportedData.confidence_score).toBeDefined();
                expect(exportedData.atomic_claims).toBeDefined();
                expect(exportedData.processing_metadata).toBeDefined();
                expect(exportedData.trace_log).toBeDefined();

                // Verify evidence sources are included
                expect(exportedData.confidence_score.structured_justification).toBeDefined();
                expect(exportedData.confidence_score.structured_justification.source_links).toBeDefined();

                // Verify reasoning chain is included
                expect(exportedData.confidence_score.structured_justification.reasoning_chain).toBeDefined();
                expect(exportedData.confidence_score.structured_justification.reasoning_chain.steps).toBeDefined();

                // Verify data completeness
                expect(exportedData.confidence_score.structured_justification.source_links.length).toBe(
                  results.confidence_score.structured_justification.source_links.length
                );
                expect(exportedData.confidence_score.structured_justification.reasoning_chain.steps.length).toBe(
                  results.confidence_score.structured_justification.reasoning_chain.steps.length
                );

                unmount();
                resolve(true);
              };
              reader.readAsText(blob);
            });
          } catch (error) {
            unmount();
            throw error;
          }
        }
      ),
      { numRuns: 20 }
    );
  });

  /**
   * **Feature: kepler-web-interface, Property 42: PDF export generation**
   * 
   * For any PDF export request, a formatted PDF file should be generated and downloaded.
   * 
   * **Validates: Requirements 14.4**
   */
  it('Property 42: should generate and download PDF file', async () => {
    fc.assert(
      fc.property(
        verificationResultArbitrary,
        async (results) => {
          const { unmount } = render(<ExportButton results={results} />);

          try {
            // Open dropdown
            const exportButton = screen.getByRole('button', { name: /Export verification results/i });
            fireEvent.click(exportButton);

            // Click PDF export option
            const pdfOption = screen.getByRole('menuitem', { name: /Export as PDF/i });
            fireEvent.click(pdfOption);

            // Wait a bit for async PDF generation
            await new Promise(resolve => setTimeout(resolve, 100));

            // Verify that jsPDF was instantiated and save was called
            const { jsPDF } = await import('jspdf');
            expect(jsPDF).toHaveBeenCalled();

            // Get the mock PDF instance
            const mockPDFInstance = (jsPDF as unknown as ReturnType<typeof vi.fn>).mock.results[0].value;

            // Verify PDF methods were called
            expect(mockPDFInstance.setFontSize).toHaveBeenCalled();
            expect(mockPDFInstance.text).toHaveBeenCalled();
            expect(mockPDFInstance.save).toHaveBeenCalled();

            // Verify save was called with a filename
            const saveCall = mockPDFInstance.save.mock.calls[0];
            const filename = saveCall[0];
            expect(filename).toMatch(/^kepler-verification-.*\.pdf$/);
            expect(filename).toContain(results.session_id);

            unmount();
            return true;
          } catch (error) {
            unmount();
            throw error;
          }
        }
      ),
      { numRuns: 20 }
    );
  });

  /**
   * Additional property: Export button should be disabled when no results
   */
  it('Property: should disable export button when no results available', () => {
    const { unmount } = render(<ExportButton results={null} />);

    const exportButton = screen.getByRole('button', { name: /Export verification results/i });
    expect(exportButton).toBeDisabled();

    unmount();
  });

  /**
   * Additional property: Export should handle errors gracefully
   */
  it('Property: should display error message when export fails', () => {
    fc.assert(
      fc.property(
        verificationResultArbitrary,
        (results) => {
          // Mock createObjectURL to throw an error
          createObjectURLSpy.mockImplementation(() => {
            throw new Error('Export failed');
          });

          const { unmount } = render(<ExportButton results={results} />);

          try {
            // Open dropdown
            const exportButton = screen.getByRole('button', { name: /Export verification results/i });
            fireEvent.click(exportButton);

            // Click JSON export option
            const jsonOption = screen.getByRole('menuitem', { name: /Export as JSON/i });
            fireEvent.click(jsonOption);

            // Verify error message is displayed
            const errorMessage = screen.getByRole('alert');
            expect(errorMessage).toBeInTheDocument();
            expect(errorMessage.textContent).toContain('Export failed');

            unmount();
            return true;
          } catch (error) {
            unmount();
            throw error;
          }
        }
      ),
      { numRuns: 10 }
    );
  });

  /**
   * Additional property: Dropdown should close after export selection
   */
  it('Property: should close dropdown after selecting export format', () => {
    fc.assert(
      fc.property(
        verificationResultArbitrary,
        (results) => {
          const { unmount } = render(<ExportButton results={results} />);

          try {
            // Open dropdown
            const exportButton = screen.getByRole('button', { name: /Export verification results/i });
            fireEvent.click(exportButton);

            // Verify dropdown is open
            expect(screen.getByRole('menu')).toBeInTheDocument();

            // Click JSON export option
            const jsonOption = screen.getByRole('menuitem', { name: /Export as JSON/i });
            fireEvent.click(jsonOption);

            // Verify dropdown is closed
            expect(screen.queryByRole('menu')).not.toBeInTheDocument();

            unmount();
            return true;
          } catch (error) {
            unmount();
            throw error;
          }
        }
      ),
      { numRuns: 10 }
    );
  });

  /**
   * Additional property: Filename should include session ID and timestamp
   */
  it('Property: should generate filename with session ID and timestamp', () => {
    fc.assert(
      fc.property(
        verificationResultArbitrary,
        (results) => {
          const { unmount } = render(<ExportButton results={results} />);

          try {
            // Open dropdown
            const exportButton = screen.getByRole('button', { name: /Export verification results/i });
            fireEvent.click(exportButton);

            // Click JSON export option
            const jsonOption = screen.getByRole('menuitem', { name: /Export as JSON/i });
            fireEvent.click(jsonOption);

            // Verify createElement was called to create download link
            expect(createElementSpy).toHaveBeenCalledWith('a');

            // Get the mock link element
            const mockLink = createElementSpy.mock.results[0].value as HTMLAnchorElement;

            // Verify filename includes session ID
            expect(mockLink.download).toContain(results.session_id);
            expect(mockLink.download).toMatch(/^kepler-verification-.*\.json$/);

            // Verify filename includes timestamp (ISO format with dashes)
            expect(mockLink.download).toMatch(/\d{4}-\d{2}-\d{2}/);

            unmount();
            return true;
          } catch (error) {
            unmount();
            throw error;
          }
        }
      ),
      { numRuns: 10 }
    );
  });
});
