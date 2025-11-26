import { useState, useEffect } from 'react';
import { getAvailableModels, type ModelInfo, APIError } from '../../services/api';
import './ModelSelector.css';

/**
 * ModelSelector Component
 * 
 * A component for selecting which language models to use for verification.
 * Fetches available models from the API and manages selection state.
 * 
 * Requirements: 4.1, 4.2, 4.3, 4.4, 4.5
 */

interface ModelSelectorProps {
  selectedModels: string[];
  onSelectionChange: (modelIds: string[]) => void;
  disabled?: boolean;
}

export const ModelSelector = ({ 
  selectedModels, 
  onSelectionChange, 
  disabled = false 
}: ModelSelectorProps) => {
  const [models, setModels] = useState<ModelInfo[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string>('');

  useEffect(() => {
    loadModels();
  }, []);

  const loadModels = async () => {
    try {
      setLoading(true);
      setError('');
      const modelsList = await getAvailableModels();
      setModels(modelsList);
      
      // If no models are selected yet and we have models, select the first one
      if (selectedModels.length === 0 && modelsList.length > 0) {
        onSelectionChange([modelsList[0].id]);
      }
    } catch (err) {
      const errorMessage = err instanceof APIError 
        ? err.detail || err.message 
        : 'Failed to load available models';
      setError(errorMessage);
      console.error('Failed to load models:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleToggle = (modelId: string) => {
    if (selectedModels.includes(modelId)) {
      // Don't allow deselecting if it's the last one (Requirement 4.3)
      if (selectedModels.length > 1) {
        onSelectionChange(selectedModels.filter(id => id !== modelId));
      }
    } else {
      // Allow multiple model selection (Requirement 4.4)
      onSelectionChange([...selectedModels, modelId]);
    }
  };

  const handleRetry = () => {
    loadModels();
  };

  // Loading state (Requirement 4.1)
  if (loading) {
    return (
      <div className="model-selector">
        <h3>Select Language Models</h3>
        <div className="model-selector-loading" role="status" aria-live="polite">
          <div className="loading-spinner"></div>
          <p>Loading available models...</p>
        </div>
      </div>
    );
  }

  // Error state (Requirement 4.1 - handle errors gracefully)
  if (error) {
    return (
      <div className="model-selector">
        <h3>Select Language Models</h3>
        <div className="model-selector-error" role="alert">
          <p className="error-message">{error}</p>
          <button 
            onClick={handleRetry} 
            className="retry-button"
            type="button"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  // No models available
  if (models.length === 0) {
    return (
      <div className="model-selector">
        <h3>Select Language Models</h3>
        <div className="model-selector-empty">
          <p>No models available</p>
        </div>
      </div>
    );
  }

  return (
    <div className="model-selector">
      <h3>Select Language Models</h3>
      <p className="model-selector-description">
        Choose one or more models for verification. At least one model must be selected.
      </p>
      <div className="model-list" role="group" aria-label="Available language models">
        {models.map(model => {
          const isSelected = selectedModels.includes(model.id);
          const isLastSelected = isSelected && selectedModels.length === 1;
          
          return (
            <label 
              key={model.id} 
              className={`model-option ${isSelected ? 'selected' : ''} ${isLastSelected ? 'last-selected' : ''}`}
            >
              <input
                type="checkbox"
                checked={isSelected}
                onChange={() => handleToggle(model.id)}
                disabled={disabled || isLastSelected}
                aria-label={`${model.name} from ${model.provider}`}
                aria-describedby={isLastSelected ? 'last-model-hint' : undefined}
              />
              <div className="model-info">
                <span className="model-name">{model.name}</span>
                <span className="model-provider">({model.provider})</span>
              </div>
            </label>
          );
        })}
      </div>
      <p id="last-model-hint" className="model-selector-hint">
        At least one model must remain selected
      </p>
    </div>
  );
};
