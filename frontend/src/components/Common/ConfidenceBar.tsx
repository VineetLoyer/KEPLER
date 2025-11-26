/**
 * ConfidenceBar Component
 * 
 * A visual indicator for confidence scores.
 * Displays a progress bar with percentage label.
 */

import React from 'react';
import './ConfidenceBar.css';

interface ConfidenceBarProps {
  score: number; // 0-1 range
  label?: string;
  showPercentage?: boolean;
}

export const ConfidenceBar: React.FC<ConfidenceBarProps> = ({
  score,
  label,
  showPercentage = true,
}) => {
  const percentage = Math.round(score * 100);
  
  // Determine color based on confidence level
  const getColorClass = () => {
    if (percentage >= 80) return 'confidence-high';
    if (percentage >= 50) return 'confidence-medium';
    return 'confidence-low';
  };

  return (
    <div className="confidence-bar-container">
      {label && <span className="confidence-bar-label">{label}</span>}
      <div className="confidence-bar-track">
        <div
          className={`confidence-bar-fill ${getColorClass()}`}
          style={{ width: `${percentage}%` }}
          role="progressbar"
          aria-valuenow={percentage}
          aria-valuemin={0}
          aria-valuemax={100}
          aria-label={label || 'Confidence score'}
        />
      </div>
      {showPercentage && (
        <span className="confidence-bar-percentage">{percentage}%</span>
      )}
    </div>
  );
};

export default ConfidenceBar;
