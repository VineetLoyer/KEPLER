import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { ClaimInput } from './ClaimInput';

/**
 * Tests for ClaimInput Component
 * 
 * Task 6: Implement ClaimInput component
 * - Create textarea for claim input with placeholder text
 * - Add client-side validation (non-empty, non-whitespace)
 * - Display inline validation error messages
 * - Handle form submission event
 * - Disable input during verification (controlled by parent state)
 * - Style component with appropriate spacing and focus states
 * 
 * Requirements: 2.1, 2.2, 2.3
 */

describe('ClaimInput Component', () => {
  const mockOnChange = vi.fn();
  const mockOnSubmit = vi.fn();

  beforeEach(() => {
    mockOnChange.mockClear();
    mockOnSubmit.mockClear();
  });

  describe('Rendering', () => {
    it('should render textarea with placeholder text', () => {
      render(
        <ClaimInput
          value=""
          onChange={mockOnChange}
          onSubmit={mockOnSubmit}
        />
      );

      const textarea = screen.getByPlaceholderText(/Enter a claim to verify/i);
      expect(textarea).toBeInTheDocument();
    });

    it('should render submit button', () => {
      render(
        <ClaimInput
          value=""
          onChange={mockOnChange}
          onSubmit={mockOnSubmit}
        />
      );

      const button = screen.getByRole('button', { name: /Verify Claim/i });
      expect(button).toBeInTheDocument();
    });

    it('should render label for textarea', () => {
      render(
        <ClaimInput
          value=""
          onChange={mockOnChange}
          onSubmit={mockOnSubmit}
        />
      );

      const label = screen.getByText(/Enter Claim/i);
      expect(label).toBeInTheDocument();
    });

    it('should display the provided value in textarea', () => {
      const testValue = 'Test claim';
      render(
        <ClaimInput
          value={testValue}
          onChange={mockOnChange}
          onSubmit={mockOnSubmit}
        />
      );

      const textarea = screen.getByRole('textbox') as HTMLTextAreaElement;
      expect(textarea.value).toBe(testValue);
    });
  });

  describe('User Interaction', () => {
    it('should call onChange when user types', async () => {
      const user = userEvent.setup();
      render(
        <ClaimInput
          value=""
          onChange={mockOnChange}
          onSubmit={mockOnSubmit}
        />
      );

      const textarea = screen.getByRole('textbox');
      await user.type(textarea, 'Test');

      expect(mockOnChange).toHaveBeenCalled();
    });

    it('should update textarea value through onChange', () => {
      const { rerender } = render(
        <ClaimInput
          value=""
          onChange={mockOnChange}
          onSubmit={mockOnSubmit}
        />
      );

      const textarea = screen.getByRole('textbox') as HTMLTextAreaElement;
      fireEvent.change(textarea, { target: { value: 'New value' } });

      expect(mockOnChange).toHaveBeenCalledWith('New value');
    });
  });

  describe('Validation', () => {
    it('should show error when submitting empty claim', () => {
      render(
        <ClaimInput
          value=""
          onChange={mockOnChange}
          onSubmit={mockOnSubmit}
        />
      );

      const button = screen.getByRole('button', { name: /Verify Claim/i });
      fireEvent.click(button);

      const errorMessage = screen.getByText(/Claim cannot be empty or whitespace-only/i);
      expect(errorMessage).toBeInTheDocument();
      expect(mockOnSubmit).not.toHaveBeenCalled();
    });

    it('should show error when submitting whitespace-only claim', () => {
      render(
        <ClaimInput
          value="   "
          onChange={mockOnChange}
          onSubmit={mockOnSubmit}
        />
      );

      const button = screen.getByRole('button', { name: /Verify Claim/i });
      fireEvent.click(button);

      const errorMessage = screen.getByText(/Claim cannot be empty or whitespace-only/i);
      expect(errorMessage).toBeInTheDocument();
      expect(mockOnSubmit).not.toHaveBeenCalled();
    });

    it('should call onSubmit when submitting valid claim', () => {
      render(
        <ClaimInput
          value="Valid claim"
          onChange={mockOnChange}
          onSubmit={mockOnSubmit}
        />
      );

      const button = screen.getByRole('button', { name: /Verify Claim/i });
      fireEvent.click(button);

      expect(mockOnSubmit).toHaveBeenCalled();
    });

    it('should not show error initially', () => {
      render(
        <ClaimInput
          value=""
          onChange={mockOnChange}
          onSubmit={mockOnSubmit}
        />
      );

      const errorMessage = screen.queryByText(/Claim cannot be empty or whitespace-only/i);
      expect(errorMessage).not.toBeInTheDocument();
    });

    it('should clear error when user starts typing', async () => {
      const user = userEvent.setup();
      render(
        <ClaimInput
          value=""
          onChange={mockOnChange}
          onSubmit={mockOnSubmit}
        />
      );

      // Trigger error
      const button = screen.getByRole('button', { name: /Verify Claim/i });
      fireEvent.click(button);

      let errorMessage = screen.getByText(/Claim cannot be empty or whitespace-only/i);
      expect(errorMessage).toBeInTheDocument();

      // Start typing
      const textarea = screen.getByRole('textbox');
      await user.type(textarea, 'T');

      // Error should be cleared
      errorMessage = screen.queryByText(/Claim cannot be empty or whitespace-only/i);
      expect(errorMessage).not.toBeInTheDocument();
    });

    it('should add error styling to textarea when error is present', () => {
      render(
        <ClaimInput
          value=""
          onChange={mockOnChange}
          onSubmit={mockOnSubmit}
        />
      );

      const button = screen.getByRole('button', { name: /Verify Claim/i });
      fireEvent.click(button);

      const textarea = screen.getByRole('textbox');
      expect(textarea).toHaveClass('claim-input-error');
    });

    it('should set aria-invalid when error is present', () => {
      render(
        <ClaimInput
          value=""
          onChange={mockOnChange}
          onSubmit={mockOnSubmit}
        />
      );

      const textarea = screen.getByRole('textbox');
      expect(textarea).toHaveAttribute('aria-invalid', 'false');

      const button = screen.getByRole('button', { name: /Verify Claim/i });
      fireEvent.click(button);

      expect(textarea).toHaveAttribute('aria-invalid', 'true');
    });
  });

  describe('Disabled State', () => {
    it('should disable textarea when disabled prop is true', () => {
      render(
        <ClaimInput
          value=""
          onChange={mockOnChange}
          onSubmit={mockOnSubmit}
          disabled={true}
        />
      );

      const textarea = screen.getByRole('textbox');
      expect(textarea).toBeDisabled();
    });

    it('should disable button when disabled prop is true', () => {
      render(
        <ClaimInput
          value=""
          onChange={mockOnChange}
          onSubmit={mockOnSubmit}
          disabled={true}
        />
      );

      const button = screen.getByRole('button');
      expect(button).toBeDisabled();
    });

    it('should change button text when disabled', () => {
      render(
        <ClaimInput
          value=""
          onChange={mockOnChange}
          onSubmit={mockOnSubmit}
          disabled={true}
        />
      );

      const button = screen.getByRole('button', { name: /Verifying.../i });
      expect(button).toBeInTheDocument();
    });

    it('should not call onSubmit when disabled', () => {
      render(
        <ClaimInput
          value="Valid claim"
          onChange={mockOnChange}
          onSubmit={mockOnSubmit}
          disabled={true}
        />
      );

      const button = screen.getByRole('button');
      fireEvent.click(button);

      expect(mockOnSubmit).not.toHaveBeenCalled();
    });
  });

  describe('Form Submission', () => {
    it('should submit on Enter key in textarea', () => {
      render(
        <ClaimInput
          value="Valid claim"
          onChange={mockOnChange}
          onSubmit={mockOnSubmit}
        />
      );

      const form = screen.getByRole('textbox').closest('form');
      if (form) {
        fireEvent.submit(form);
      }

      expect(mockOnSubmit).toHaveBeenCalled();
    });

    it('should prevent default form submission', () => {
      render(
        <ClaimInput
          value="Valid claim"
          onChange={mockOnChange}
          onSubmit={mockOnSubmit}
        />
      );

      const form = screen.getByRole('textbox').closest('form');
      const submitEvent = new Event('submit', { bubbles: true, cancelable: true });
      const preventDefaultSpy = vi.spyOn(submitEvent, 'preventDefault');

      if (form) {
        form.dispatchEvent(submitEvent);
      }

      expect(preventDefaultSpy).toHaveBeenCalled();
    });
  });

  describe('Accessibility', () => {
    it('should have proper label association', () => {
      render(
        <ClaimInput
          value=""
          onChange={mockOnChange}
          onSubmit={mockOnSubmit}
        />
      );

      const textarea = screen.getByRole('textbox');
      const label = screen.getByText(/Enter Claim/i);

      expect(textarea).toHaveAttribute('id', 'claim-input');
      expect(label).toHaveAttribute('for', 'claim-input');
    });

    it('should have aria-describedby when error is present', () => {
      render(
        <ClaimInput
          value=""
          onChange={mockOnChange}
          onSubmit={mockOnSubmit}
        />
      );

      const button = screen.getByRole('button', { name: /Verify Claim/i });
      fireEvent.click(button);

      const textarea = screen.getByRole('textbox');
      expect(textarea).toHaveAttribute('aria-describedby', 'claim-input-error');
    });

    it('should have role="alert" on error message', () => {
      render(
        <ClaimInput
          value=""
          onChange={mockOnChange}
          onSubmit={mockOnSubmit}
        />
      );

      const button = screen.getByRole('button', { name: /Verify Claim/i });
      fireEvent.click(button);

      const errorMessage = screen.getByRole('alert');
      expect(errorMessage).toBeInTheDocument();
    });
  });
});
