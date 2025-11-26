import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import App from './App';

/**
 * Tests for initial app rendering
 * 
 * Task 5.1: Write tests for initial app rendering
 * - Test main interface loads
 * - Test input form is displayed
 * 
 * Validates: Requirements 1.1, 1.2
 */

describe('App Component - Initial Rendering', () => {
  describe('Main interface loads', () => {
    it('should render the main application container', () => {
      render(<App />);
      
      // Check that the main app container is present
      const appElement = document.querySelector('.app');
      expect(appElement).toBeInTheDocument();
    });

    it('should display the application header with title', () => {
      render(<App />);
      
      // Check for the main heading
      const heading = screen.getByRole('heading', { name: /KEPLER Fact Checker/i });
      expect(heading).toBeInTheDocument();
    });

    it('should display the application subtitle', () => {
      render(<App />);
      
      // Check for the subtitle
      const subtitle = screen.getByText(/AI-Powered Fact Verification System/i);
      expect(subtitle).toBeInTheDocument();
    });

    it('should render the main content area', () => {
      render(<App />);
      
      // Check that the main element is present
      const mainElement = document.querySelector('.app-main');
      expect(mainElement).toBeInTheDocument();
    });

    it('should render the history sidebar', () => {
      render(<App />);
      
      // Check that the history sidebar is present
      const historyElement = document.querySelector('.history-sidebar');
      expect(historyElement).toBeInTheDocument();
      
      // Check for history heading
      const historyHeading = screen.getByRole('heading', { name: /History/i });
      expect(historyHeading).toBeInTheDocument();
    });
  });

  describe('Input form is displayed', () => {
    it('should display the input section', () => {
      render(<App />);
      
      // Check that the input section is present
      const inputSection = document.querySelector('.input-section');
      expect(inputSection).toBeInTheDocument();
    });

    it('should display the "Submit a Claim" heading', () => {
      render(<App />);
      
      // Check for the input section heading
      const heading = screen.getByRole('heading', { name: /Submit a Claim/i });
      expect(heading).toBeInTheDocument();
    });

    it('should display instructions for claim submission', () => {
      render(<App />);
      
      // Check for instruction text
      const instructions = screen.getByText(/Enter a claim to verify or upload an image/i);
      expect(instructions).toBeInTheDocument();
    });

    it('should display the claim input textarea', () => {
      render(<App />);
      
      // Check for the claim input textarea
      const textarea = screen.getByPlaceholderText(/Enter a claim to verify/i);
      expect(textarea).toBeInTheDocument();
    });

    it('should display the verify claim button', () => {
      render(<App />);
      
      // Check for the submit button
      const button = screen.getByRole('button', { name: /Verify Claim/i });
      expect(button).toBeInTheDocument();
    });
  });

  describe('Initial state', () => {
    it('should not display loading indicator initially', () => {
      render(<App />);
      
      // Loading section should not be present initially
      const loadingSection = document.querySelector('.loading-section');
      expect(loadingSection).not.toBeInTheDocument();
    });

    it('should not display error message initially', () => {
      render(<App />);
      
      // Error section should not be present initially
      const errorSection = document.querySelector('.error-section');
      expect(errorSection).not.toBeInTheDocument();
    });

    it('should not display results section initially', () => {
      render(<App />);
      
      // Results section should not be present initially
      const resultsSection = document.querySelector('.results-section');
      expect(resultsSection).not.toBeInTheDocument();
    });
  });
});
