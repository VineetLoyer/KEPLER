/**
 * ExportButton Component
 * 
 * Task 18: Implement Export functionality
 * - Create ExportButton component with format dropdown
 * - Implement JSON export with complete verification data
 * - Implement PDF export using library (jsPDF or similar)
 * - Format PDF with sections for verdict, evidence, reasoning
 * - Trigger file downloads with appropriate filenames
 * - Handle export errors gracefully
 * 
 * Requirements: 14.1, 14.2, 14.3, 14.4, 14.5
 */

import React, { useState } from 'react';
import { jsPDF } from 'jspdf';
import type { VerificationResult } from '../../types/verification';
import './ExportButton.css';

interface ExportButtonProps {
  results: VerificationResult | null;
  disabled?: boolean;
}

type ExportFormat = 'json' | 'pdf';

/**
 * ExportButton Component
 * 
 * Provides export functionality for verification results in JSON and PDF formats.
 * 
 * Requirements: 14.1, 14.2, 14.3, 14.4, 14.5
 */
export const ExportButton: React.FC<ExportButtonProps> = ({ results, disabled = false }) => {
  const [isOpen, setIsOpen] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleToggleDropdown = () => {
    setIsOpen(!isOpen);
  };

  const handleExport = async (format: ExportFormat) => {
    setIsOpen(false);
    setError(null);

    if (!results) {
      setError('No results available to export');
      return;
    }

    try {
      if (format === 'json') {
        exportAsJSON(results);
      } else if (format === 'pdf') {
        await exportAsPDF(results);
      }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Export failed';
      setError(errorMessage);
      console.error('Export error:', err);
    }
  };

  /**
   * Export results as JSON file
   * Requirements: 14.3, 14.5
   */
  const exportAsJSON = (data: VerificationResult) => {
    // Create complete JSON with all verification details
    const jsonData = JSON.stringify(data, null, 2);
    const blob = new Blob([jsonData], { type: 'application/json' });
    const url = URL.createObjectURL(blob);

    // Generate filename with timestamp
    const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
    const filename = `kepler-verification-${data.session_id}-${timestamp}.json`;

    // Trigger download
    const link = document.createElement('a');
    link.href = url;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  };

  /**
   * Export results as PDF file
   * Requirements: 14.4, 14.5
   */
  const exportAsPDF = async (data: VerificationResult) => {
    const doc = new jsPDF();
    let yPosition = 20;
    const pageWidth = doc.internal.pageSize.getWidth();
    const margin = 20;
    const maxWidth = pageWidth - 2 * margin;

    // Helper function to add text with word wrap
    const addText = (text: string, fontSize: number = 12, isBold: boolean = false) => {
      doc.setFontSize(fontSize);
      if (isBold) {
        doc.setFont('helvetica', 'bold');
      } else {
        doc.setFont('helvetica', 'normal');
      }

      const lines = doc.splitTextToSize(text, maxWidth);
      lines.forEach((line: string) => {
        if (yPosition > 270) {
          doc.addPage();
          yPosition = 20;
        }
        doc.text(line, margin, yPosition);
        yPosition += fontSize * 0.5;
      });
      yPosition += 5;
    };

    // Title
    addText('KEPLER Fact Verification Report', 18, true);
    yPosition += 5;

    // Session ID
    addText(`Session ID: ${data.session_id}`, 10);
    yPosition += 5;

    // Verdict Section
    addText('Verdict', 16, true);
    addText(`Classification: ${data.consensus_verdict.final_classification}`, 12);
    addText(`Confidence: ${(data.confidence_score.overall_score * 100).toFixed(1)}%`, 12);
    addText(`Justification: ${data.consensus_verdict.consensus_justification}`, 12);
    yPosition += 10;

    // Confidence Breakdown
    addText('Confidence Breakdown', 14, true);
    addText(`Source Reliability: ${(data.confidence_score.source_reliability * 100).toFixed(1)}%`, 12);
    addText(`Model Agreement: ${(data.confidence_score.model_agreement * 100).toFixed(1)}%`, 12);
    addText(`Evidence Recency: ${(data.confidence_score.evidence_recency * 100).toFixed(1)}%`, 12);
    yPosition += 10;

    // Evidence Sources
    if (data.confidence_score.structured_justification.source_links.length > 0) {
      addText('Evidence Sources', 14, true);
      data.confidence_score.structured_justification.source_links.forEach((source, index) => {
        addText(`${index + 1}. ${source.title || 'Untitled'}`, 12);
        addText(`   URL: ${source.url}`, 10);
        if (source.credibility_score !== undefined) {
          addText(`   Credibility: ${(source.credibility_score * 100).toFixed(0)}%`, 10);
        }
      });
      yPosition += 10;
    }

    // Reasoning Chain
    if (data.confidence_score.structured_justification.reasoning_chain.steps.length > 0) {
      addText('Reasoning Chain', 14, true);
      data.confidence_score.structured_justification.reasoning_chain.steps.forEach((step) => {
        addText(`Step ${step.step_number}: ${step.description}`, 12);
        addText(`Conclusion: ${step.conclusion}`, 10);
        yPosition += 5;
      });
      yPosition += 10;
    }

    // Atomic Claims
    if (data.atomic_claims.length > 0) {
      addText('Atomic Claims', 14, true);
      data.atomic_claims.forEach((claim, index) => {
        addText(`${index + 1}. ${claim.claim_text}`, 12);
        addText(`   Status: ${claim.verification_status}`, 10);
        yPosition += 5;
      });
    }

    // Generate filename with timestamp
    const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
    const filename = `kepler-verification-${data.session_id}-${timestamp}.pdf`;

    // Save PDF
    doc.save(filename);
  };

  return (
    <div className="export-button-container">
      <div className="export-dropdown">
        <button
          className="export-button"
          onClick={handleToggleDropdown}
          disabled={disabled || !results}
          aria-label="Export verification results"
          aria-haspopup="true"
          aria-expanded={isOpen}
        >
          Export Results
          <span className="export-arrow">{isOpen ? '▲' : '▼'}</span>
        </button>

        {isOpen && (
          <div className="export-dropdown-menu" role="menu">
            <button
              className="export-option"
              onClick={() => handleExport('json')}
              role="menuitem"
            >
              Export as JSON
            </button>
            <button
              className="export-option"
              onClick={() => handleExport('pdf')}
              role="menuitem"
            >
              Export as PDF
            </button>
          </div>
        )}
      </div>

      {error && (
        <div className="export-error" role="alert">
          {error}
        </div>
      )}
    </div>
  );
};

export default ExportButton;
