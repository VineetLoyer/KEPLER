/**
 * Tests for LoadingIndicator Component
 * 
 * Task 10: Implement LoadingIndicator component
 * - Create animated loading spinner (CSS or SVG)
 * - Accept current stage as prop
 * - Display stage-specific progress messages
 * - Add "This may take a moment..." helper text
 * - Style with appropriate spacing and centering
 * 
 * Requirements: 2.4, 12.1, 12.2
 */

import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { LoadingIndicator, type VerificationStage } from './LoadingIndicator';

describe('LoadingIndicator Component', () => {
  describe('Rendering', () => {
    it('should render loading indicator', () => {
      render(<LoadingIndicator />);

      const indicator = screen.getByRole('status');
      expect(indicator).toBeInTheDocument();
    });

    it('should render SVG spinner', () => {
      const { container } = render(<LoadingIndicator />);

      const svg = container.querySelector('.loading-spinner');
      expect(svg).toBeInTheDocument();
      expect(svg?.tagName).toBe('svg');
    });

    it('should render helper text', () => {
      render(<LoadingIndicator />);

      const helperText = screen.getByText(/This may take a moment\.\.\./i);
      expect(helperText).toBeInTheDocument();
    });

    it('should have proper ARIA attributes', () => {
      render(<LoadingIndicator />);

      const indicator = screen.getByRole('status');
      expect(indicator).toHaveAttribute('aria-live', 'polite');
    });

    it('should have screen reader text', () => {
      render(<LoadingIndicator />);

      const srText = screen.getByText(/Loading:/);
      expect(srText).toBeInTheDocument();
      expect(srText).toHaveClass('sr-only');
    });
  });

  describe('Stage Messages', () => {
    it('should display initializing message by default', () => {
      const { container } = render(<LoadingIndicator />);

      const message = container.querySelector('.loading-stage-message');
      expect(message).toHaveTextContent(/Initializing verification process\.\.\./i);
    });

    it('should display decomposing stage message', () => {
      const { container } = render(<LoadingIndicator currentStage="decomposing" />);

      const message = container.querySelector('.loading-stage-message');
      expect(message).toHaveTextContent(/Breaking down claim into atomic components\.\.\./i);
    });

    it('should display retrieving stage message', () => {
      const { container } = render(<LoadingIndicator currentStage="retrieving" />);

      const message = container.querySelector('.loading-stage-message');
      expect(message).toHaveTextContent(/Retrieving evidence from sources\.\.\./i);
    });

    it('should display reranking stage message', () => {
      const { container } = render(<LoadingIndicator currentStage="reranking" />);

      const message = container.querySelector('.loading-stage-message');
      expect(message).toHaveTextContent(/Ranking evidence by relevance\.\.\./i);
    });

    it('should display verifying stage message', () => {
      const { container } = render(<LoadingIndicator currentStage="verifying" />);

      const message = container.querySelector('.loading-stage-message');
      expect(message).toHaveTextContent(/Verifying claim against evidence\.\.\./i);
    });

    it('should display aggregating stage message', () => {
      const { container } = render(<LoadingIndicator currentStage="aggregating" />);

      const message = container.querySelector('.loading-stage-message');
      expect(message).toHaveTextContent(/Aggregating results from multiple models\.\.\./i);
    });

    it('should display scoring stage message', () => {
      const { container } = render(<LoadingIndicator currentStage="scoring" />);

      const message = container.querySelector('.loading-stage-message');
      expect(message).toHaveTextContent(/Calculating confidence scores\.\.\./i);
    });

    it('should display finalizing stage message', () => {
      const { container } = render(<LoadingIndicator currentStage="finalizing" />);

      const message = container.querySelector('.loading-stage-message');
      expect(message).toHaveTextContent(/Finalizing verification results\.\.\./i);
    });
  });

  describe('Stage Updates', () => {
    it('should update message when stage changes', () => {
      const { rerender, container } = render(<LoadingIndicator currentStage="initializing" />);

      let message = container.querySelector('.loading-stage-message');
      expect(message).toHaveTextContent(/Initializing verification process\.\.\./i);

      rerender(<LoadingIndicator currentStage="verifying" />);

      message = container.querySelector('.loading-stage-message');
      expect(message).toHaveTextContent(/Verifying claim against evidence\.\.\./i);
    });

    it('should update screen reader text when stage changes', () => {
      const { rerender } = render(<LoadingIndicator currentStage="retrieving" />);

      let srText = screen.getByText(/Loading: Retrieving evidence from sources\.\.\./i);
      expect(srText).toBeInTheDocument();

      rerender(<LoadingIndicator currentStage="scoring" />);

      srText = screen.getByText(/Loading: Calculating confidence scores\.\.\./i);
      expect(srText).toBeInTheDocument();
    });
  });

  describe('Styling', () => {
    it('should have loading-indicator class', () => {
      render(<LoadingIndicator />);

      const indicator = screen.getByRole('status');
      expect(indicator).toHaveClass('loading-indicator');
    });

    it('should have loading-stage-message class on message', () => {
      const { container } = render(<LoadingIndicator />);

      const message = container.querySelector('.loading-stage-message');
      expect(message).toBeInTheDocument();
      expect(message).toHaveClass('loading-stage-message');
    });

    it('should have loading-helper-text class on helper text', () => {
      render(<LoadingIndicator />);

      const helperText = screen.getByText(/This may take a moment\.\.\./i);
      expect(helperText).toHaveClass('loading-helper-text');
    });

    it('should have loading-spinner class on SVG', () => {
      const { container } = render(<LoadingIndicator />);

      const spinner = container.querySelector('.loading-spinner');
      expect(spinner).toBeInTheDocument();
    });
  });

  describe('SVG Structure', () => {
    it('should have two circles in SVG (track and path)', () => {
      const { container } = render(<LoadingIndicator />);

      const circles = container.querySelectorAll('.loading-spinner circle');
      expect(circles).toHaveLength(2);
    });

    it('should have loading-spinner-track class on first circle', () => {
      const { container } = render(<LoadingIndicator />);

      const track = container.querySelector('.loading-spinner-track');
      expect(track).toBeInTheDocument();
      expect(track?.tagName).toBe('circle');
    });

    it('should have loading-spinner-path class on second circle', () => {
      const { container } = render(<LoadingIndicator />);

      const path = container.querySelector('.loading-spinner-path');
      expect(path).toBeInTheDocument();
      expect(path?.tagName).toBe('circle');
    });

    it('should have aria-hidden on SVG', () => {
      const { container } = render(<LoadingIndicator />);

      const svg = container.querySelector('.loading-spinner');
      expect(svg).toHaveAttribute('aria-hidden', 'true');
    });
  });

  describe('Accessibility', () => {
    it('should be accessible to screen readers via role="status"', () => {
      render(<LoadingIndicator />);

      const status = screen.getByRole('status');
      expect(status).toBeInTheDocument();
    });

    it('should announce changes with aria-live="polite"', () => {
      render(<LoadingIndicator />);

      const indicator = screen.getByRole('status');
      expect(indicator).toHaveAttribute('aria-live', 'polite');
    });

    it('should provide descriptive text for screen readers', () => {
      render(<LoadingIndicator currentStage="verifying" />);

      const srText = screen.getByText(/Loading: Verifying claim against evidence\.\.\./i);
      expect(srText).toBeInTheDocument();
    });

    it('should hide decorative SVG from screen readers', () => {
      const { container } = render(<LoadingIndicator />);

      const svg = container.querySelector('.loading-spinner');
      expect(svg).toHaveAttribute('aria-hidden', 'true');
    });
  });

  describe('Content Structure', () => {
    it('should have loading-content container', () => {
      const { container } = render(<LoadingIndicator />);

      const content = container.querySelector('.loading-content');
      expect(content).toBeInTheDocument();
    });

    it('should have loading-spinner-container', () => {
      const { container } = render(<LoadingIndicator />);

      const spinnerContainer = container.querySelector('.loading-spinner-container');
      expect(spinnerContainer).toBeInTheDocument();
    });

    it('should render stage message and helper text in correct order', () => {
      const { container } = render(<LoadingIndicator />);

      const content = container.querySelector('.loading-content');
      const children = content?.children;

      expect(children?.[0]).toHaveClass('loading-stage-message');
      expect(children?.[1]).toHaveClass('loading-helper-text');
    });
  });

  describe('All Stages Coverage', () => {
    const stages: VerificationStage[] = [
      'initializing',
      'decomposing',
      'retrieving',
      'reranking',
      'verifying',
      'aggregating',
      'scoring',
      'finalizing',
    ];

    stages.forEach((stage) => {
      it(`should render ${stage} stage without errors`, () => {
        const { container } = render(<LoadingIndicator currentStage={stage} />);

        const indicator = screen.getByRole('status');
        expect(indicator).toBeInTheDocument();

        const message = container.querySelector('.loading-stage-message');
        expect(message).toBeInTheDocument();
        expect(message?.textContent).toBeTruthy();
      });
    });
  });
});
