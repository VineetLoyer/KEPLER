import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { ModelSelector } from './ModelSelector';
import * as api from '../../services/api';
import type { ModelInfo } from '../../services/api';

/**
 * Unit Tests for ModelSelector Component
 * 
 * These tests verify specific examples and edge cases for the ModelSelector component.
 */

const mockModels: ModelInfo[] = [
  { id: 'gpt-4', name: 'GPT-4', provider: 'OpenAI', version: '1.0.0' },
  { id: 'claude-3', name: 'Claude 3', provider: 'Anthropic', version: '1.0.0' },
  { id: 'gemini-pro', name: 'Gemini Pro', provider: 'Google', version: '1.0.0' },
];

describe('ModelSelector Component', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('should display loading state initially', () => {
    vi.spyOn(api, 'getAvailableModels').mockImplementation(
      () => new Promise(() => {}) // Never resolves
    );

    render(
      <ModelSelector
        selectedModels={[]}
        onSelectionChange={vi.fn()}
      />
    );

    expect(screen.getByText(/Loading available models/i)).toBeInTheDocument();
    expect(screen.getByRole('status')).toBeInTheDocument();
  });

  it('should fetch and display models on mount', async () => {
    vi.spyOn(api, 'getAvailableModels').mockResolvedValue(mockModels);

    render(
      <ModelSelector
        selectedModels={[]}
        onSelectionChange={vi.fn()}
      />
    );

    await waitFor(() => {
      expect(screen.getByText('GPT-4')).toBeInTheDocument();
    });

    expect(screen.getByText('Claude 3')).toBeInTheDocument();
    expect(screen.getByText('Gemini Pro')).toBeInTheDocument();
    expect(screen.getByText('(OpenAI)')).toBeInTheDocument();
    expect(screen.getByText('(Anthropic)')).toBeInTheDocument();
    expect(screen.getByText('(Google)')).toBeInTheDocument();
  });

  it('should auto-select first model if none selected', async () => {
    vi.spyOn(api, 'getAvailableModels').mockResolvedValue(mockModels);
    const mockOnSelectionChange = vi.fn();

    render(
      <ModelSelector
        selectedModels={[]}
        onSelectionChange={mockOnSelectionChange}
      />
    );

    await waitFor(() => {
      expect(mockOnSelectionChange).toHaveBeenCalledWith(['gpt-4']);
    });
  });

  it('should show selected models as checked', async () => {
    vi.spyOn(api, 'getAvailableModels').mockResolvedValue(mockModels);

    render(
      <ModelSelector
        selectedModels={['gpt-4', 'claude-3']}
        onSelectionChange={vi.fn()}
      />
    );

    await waitFor(() => {
      expect(screen.getByText('GPT-4')).toBeInTheDocument();
    });

    const gpt4Checkbox = screen.getByLabelText(/GPT-4/i) as HTMLInputElement;
    const claude3Checkbox = screen.getByLabelText(/Claude 3/i) as HTMLInputElement;
    const geminiCheckbox = screen.getByLabelText(/Gemini Pro/i) as HTMLInputElement;

    expect(gpt4Checkbox).toBeChecked();
    expect(claude3Checkbox).toBeChecked();
    expect(geminiCheckbox).not.toBeChecked();
  });

  it('should allow selecting additional models', async () => {
    vi.spyOn(api, 'getAvailableModels').mockResolvedValue(mockModels);
    const mockOnSelectionChange = vi.fn();
    const user = userEvent.setup();

    render(
      <ModelSelector
        selectedModels={['gpt-4']}
        onSelectionChange={mockOnSelectionChange}
      />
    );

    await waitFor(() => {
      expect(screen.getByText('Claude 3')).toBeInTheDocument();
    });

    const claude3Checkbox = screen.getByLabelText(/Claude 3/i);
    await user.click(claude3Checkbox);

    expect(mockOnSelectionChange).toHaveBeenCalledWith(['gpt-4', 'claude-3']);
  });

  it('should allow deselecting models when multiple are selected', async () => {
    vi.spyOn(api, 'getAvailableModels').mockResolvedValue(mockModels);
    const mockOnSelectionChange = vi.fn();
    const user = userEvent.setup();

    render(
      <ModelSelector
        selectedModels={['gpt-4', 'claude-3']}
        onSelectionChange={mockOnSelectionChange}
      />
    );

    await waitFor(() => {
      expect(screen.getByText('GPT-4')).toBeInTheDocument();
    });

    const gpt4Checkbox = screen.getByLabelText(/GPT-4/i);
    await user.click(gpt4Checkbox);

    expect(mockOnSelectionChange).toHaveBeenCalledWith(['claude-3']);
  });

  it('should prevent deselecting the last selected model', async () => {
    vi.spyOn(api, 'getAvailableModels').mockResolvedValue(mockModels);
    const mockOnSelectionChange = vi.fn();
    const user = userEvent.setup();

    render(
      <ModelSelector
        selectedModels={['gpt-4']}
        onSelectionChange={mockOnSelectionChange}
      />
    );

    await waitFor(() => {
      expect(screen.getByText('GPT-4')).toBeInTheDocument();
    });

    const gpt4Checkbox = screen.getByLabelText(/GPT-4/i) as HTMLInputElement;
    
    // Checkbox should be disabled
    expect(gpt4Checkbox).toBeDisabled();

    // Try to click it
    await user.click(gpt4Checkbox);

    // onSelectionChange should not be called
    expect(mockOnSelectionChange).not.toHaveBeenCalled();
  });

  it('should display error message on API failure', async () => {
    vi.spyOn(api, 'getAvailableModels').mockRejectedValue(
      new api.APIError('Network error', 500, 'Failed to fetch')
    );

    render(
      <ModelSelector
        selectedModels={[]}
        onSelectionChange={vi.fn()}
      />
    );

    await waitFor(() => {
      expect(screen.getByRole('alert')).toBeInTheDocument();
    });

    expect(screen.getByText(/Failed to fetch/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /Retry/i })).toBeInTheDocument();
  });

  it('should retry fetching models when retry button is clicked', async () => {
    const getModelsSpy = vi.spyOn(api, 'getAvailableModels');
    
    // First call fails
    getModelsSpy.mockRejectedValueOnce(
      new api.APIError('Network error', 500, 'Failed to fetch')
    );
    
    // Second call succeeds
    getModelsSpy.mockResolvedValueOnce(mockModels);

    const user = userEvent.setup();

    render(
      <ModelSelector
        selectedModels={[]}
        onSelectionChange={vi.fn()}
      />
    );

    // Wait for error
    await waitFor(() => {
      expect(screen.getByRole('alert')).toBeInTheDocument();
    });

    // Click retry
    const retryButton = screen.getByRole('button', { name: /Retry/i });
    await user.click(retryButton);

    // Wait for models to load
    await waitFor(() => {
      expect(screen.getByText('GPT-4')).toBeInTheDocument();
    });

    expect(getModelsSpy).toHaveBeenCalledTimes(2);
  });

  it('should handle empty model list', async () => {
    vi.spyOn(api, 'getAvailableModels').mockResolvedValue([]);

    render(
      <ModelSelector
        selectedModels={[]}
        onSelectionChange={vi.fn()}
      />
    );

    await waitFor(() => {
      expect(screen.getByText(/No models available/i)).toBeInTheDocument();
    });
  });

  it('should disable all checkboxes when disabled prop is true', async () => {
    vi.spyOn(api, 'getAvailableModels').mockResolvedValue(mockModels);

    render(
      <ModelSelector
        selectedModels={['gpt-4', 'claude-3']}
        onSelectionChange={vi.fn()}
        disabled={true}
      />
    );

    await waitFor(() => {
      expect(screen.getByText('GPT-4')).toBeInTheDocument();
    });

    const checkboxes = screen.getAllByRole('checkbox');
    checkboxes.forEach(checkbox => {
      expect(checkbox).toBeDisabled();
    });
  });

  it('should display hint about minimum selection', async () => {
    vi.spyOn(api, 'getAvailableModels').mockResolvedValue(mockModels);

    render(
      <ModelSelector
        selectedModels={['gpt-4']}
        onSelectionChange={vi.fn()}
      />
    );

    await waitFor(() => {
      expect(screen.getByText(/At least one model must remain selected/i)).toBeInTheDocument();
    });
  });

  it('should apply special styling to last selected model', async () => {
    vi.spyOn(api, 'getAvailableModels').mockResolvedValue(mockModels);

    render(
      <ModelSelector
        selectedModels={['gpt-4']}
        onSelectionChange={vi.fn()}
      />
    );

    await waitFor(() => {
      expect(screen.getByText('GPT-4')).toBeInTheDocument();
    });

    const gpt4Label = screen.getByLabelText(/GPT-4/i).closest('label');
    expect(gpt4Label).toHaveClass('last-selected');
  });
});
