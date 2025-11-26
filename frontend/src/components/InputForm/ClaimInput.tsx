import { useState } from 'react';
import type { FormEvent, ChangeEvent } from 'react';
import { isValidText } from '../../utils/validation';
import './ClaimInput.css';

/**
 * ClaimInput Component
 * 
 * A textarea component for entering claims to verify.
 * Includes client-side validation and error display.
 * 
 * Requirements: 2.1, 2.2, 2.3
 */

interface ClaimInputProps {
  value: string;
  onChange: (value: string) => void;
  onSubmit: () => void;
  disabled?: boolean;
}

export const ClaimInput = ({ value, onChange, onSubmit, disabled = false }: ClaimInputProps) => {
  const [error, setError] = useState<string>('');

  const handleChange = (e: ChangeEvent<HTMLTextAreaElement>) => {
    onChange(e.target.value);
    // Clear error when user starts typing
    if (error) {
      setError('');
    }
  };

  const handleSubmit = (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault();

    // Validate input (non-empty, non-whitespace)
    if (!isValidText(value)) {
      setError('Claim cannot be empty or whitespace-only');
      return;
    }

    // Clear error and submit
    setError('');
    onSubmit();
  };

  return (
    <form onSubmit={handleSubmit} className="claim-input-form">
      <div className="claim-input-container">
        <label htmlFor="claim-input" className="claim-input-label">
          Enter Claim
        </label>
        <textarea
          id="claim-input"
          value={value}
          onChange={handleChange}
          placeholder="Enter a claim to verify... (e.g., 'The Earth orbits the Sun')"
          disabled={disabled}
          rows={4}
          className={`claim-input ${error ? 'claim-input-error' : ''}`}
          aria-invalid={!!error}
          aria-describedby={error ? 'claim-input-error' : undefined}
        />
        {error && (
          <div id="claim-input-error" className="error-message" role="alert">
            {error}
          </div>
        )}
      </div>
      <button 
        type="submit" 
        disabled={disabled}
        className="claim-submit-button"
      >
        {disabled ? 'Verifying...' : 'Verify Claim'}
      </button>
    </form>
  );
};
