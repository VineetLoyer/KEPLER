import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import * as fc from 'fast-check';
import { ModelSelector } from './ModelSelector';
import * as api from '../../services/api';
import type { ModelInfo } from '../../services/api';

/**
 * Property-Based Tests for ModelSelector Component
 * 
 * Task 8.1: Write property tests for model selector
 * - Property 10: Model information display
 * - Property 11: Minimum model selection
 * - Property 12: Multiple model selection
 * - Property 13: Selected models in request
 * 
 * Requirements: 4.2, 4.3, 4.4, 4.5
 * 
 * These tests use fast-check to generate random inputs and verify
 * that the component behaves correctly across all possible inputs.
 */

// Helper to create mock model data
function createMockModel(id: string, name: string, provider: string): ModelInfo {
  return {
    id,
    name,
    provider,
    version: '1.0.0',
  };
}

// Helper to escape regex special characters
function escapeRegex(str: string): string {
  return str.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
}

describe('ModelSelector Property-Based Tests', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  /**
   * **Feature: kepler-web-interface, Property 10: Model information display**
   * 
   * For any available model in the list, the frontend should display both 
   * the model name and provider.
   * 
   * **Validates: Requirements 4.2**
   */
  it('Property 10: should display name and provider for all models', async () => {
    await fc.assert(
      fc.asyncProperty(
        // Generate a list of models with random names and providers
        fc.array(
          fc.record({
            id: fc.string({ minLength: 1, maxLength: 20 }).map(s => s.replace(/[^a-zA-Z0-9-]/g, '_')),
            // Generate valid model names (alphanumeric with spaces, but not whitespace-only)
            name: fc.string({ minLength: 3, maxLength: 30 })
              .filter(s => s.trim().length >= 3)
              .map(s => s.trim()),
            provider: fc.constantFrom('OpenAI', 'Anthropic', 'Google', 'Meta', 'Cohere'),
          }),
          { minLength: 1, maxLength: 10 }
        ),
        async (modelData) => {
          // Create unique models by both ID and name to avoid duplicates
          const uniqueModels = Array.from(
            new Map(modelData.map((m, idx) => [`${m.id}-${idx}`, { ...m, id: `${m.id}-${idx}`, name: `${m.name}-${idx}` }])).values()
          );
          
          if (uniqueModels.length === 0) return;

          const models = uniqueModels.map(m => 
            createMockModel(m.id, m.name, m.provider)
          );

          // Mock the API call
          vi.spyOn(api, 'getAvailableModels').mockResolvedValue(models);

          const mockOnSelectionChange = vi.fn();

          const { unmount } = render(
            <ModelSelector
              selectedModels={[]}
              onSelectionChange={mockOnSelectionChange}
            />
          );

          // Wait for models to load
          await waitFor(() => {
            expect(screen.queryByText(/Loading/i)).not.toBeInTheDocument();
          });

          // Verify that for each model:
          // 1. Model name is displayed
          // 2. Model provider is displayed (check using aria-label which combines both)
          for (const model of models) {
            expect(screen.getByText(model.name)).toBeInTheDocument();
            // Check that the checkbox with this model's name and provider exists
            expect(screen.getByLabelText(new RegExp(`${escapeRegex(model.name)} from ${model.provider}`, 'i'))).toBeInTheDocument();
          }

          unmount();
        }
      ),
      { numRuns: 50 } // Reduced runs for async tests
    );
  });

  /**
   * **Feature: kepler-web-interface, Property 11: Minimum model selection**
   * 
   * For any model selection state, at least one model should be selected.
   * 
   * **Validates: Requirements 4.3**
   */
  it('Property 11: should prevent deselecting the last selected model', async () => {
    await fc.assert(
      fc.asyncProperty(
        // Generate a list of models
        fc.array(
          fc.record({
            id: fc.string({ minLength: 1, maxLength: 20 }).map(s => s.replace(/[^a-zA-Z0-9-]/g, '_')),
            // Generate valid model names
            name: fc.string({ minLength: 3, maxLength: 30 })
              .filter(s => s.trim().length >= 3)
              .map(s => s.trim()),
            provider: fc.constantFrom('OpenAI', 'Anthropic', 'Google'),
          }),
          { minLength: 2, maxLength: 5 } // Need at least 2 models to test deselection
        ),
        async (modelData) => {
          // Create unique models by both ID and name
          const uniqueModels = Array.from(
            new Map(modelData.map((m, idx) => [`${m.id}-${idx}`, { ...m, id: `${m.id}-${idx}`, name: `${m.name}-${idx}` }])).values()
          );
          
          if (uniqueModels.length < 2) return;

          const models = uniqueModels.map(m => 
            createMockModel(m.id, m.name, m.provider)
          );

          vi.spyOn(api, 'getAvailableModels').mockResolvedValue(models);

          const mockOnSelectionChange = vi.fn();
          const user = userEvent.setup();

          // Start with only one model selected
          const { unmount } = render(
            <ModelSelector
              selectedModels={[models[0].id]}
              onSelectionChange={mockOnSelectionChange}
            />
          );

          await waitFor(() => {
            expect(screen.queryByText(/Loading/i)).not.toBeInTheDocument();
          });

          // Try to deselect the last selected model (escape regex special chars)
          const checkbox = screen.getByLabelText(new RegExp(escapeRegex(models[0].name), 'i')) as HTMLInputElement;
          
          // Verify checkbox is checked
          expect(checkbox).toBeChecked();
          
          // Verify checkbox is disabled (can't deselect last one)
          expect(checkbox).toBeDisabled();

          // Try to click it anyway
          await user.click(checkbox);

          // Verify onSelectionChange was NOT called
          expect(mockOnSelectionChange).not.toHaveBeenCalled();

          unmount();
        }
      ),
      { numRuns: 50 }
    );
  });

  /**
   * **Feature: kepler-web-interface, Property 12: Multiple model selection**
   * 
   * For any model selection interaction, the frontend should allow selecting 
   * more than one model simultaneously.
   * 
   * **Validates: Requirements 4.4**
   */
  it('Property 12: should allow selecting multiple models', async () => {
    await fc.assert(
      fc.asyncProperty(
        // Generate a list of models
        fc.array(
          fc.record({
            id: fc.string({ minLength: 1, maxLength: 20 }).map(s => s.replace(/[^a-zA-Z0-9-]/g, '_')),
            // Generate valid model names
            name: fc.string({ minLength: 3, maxLength: 30 })
              .filter(s => s.trim().length >= 3)
              .map(s => s.trim()),
            provider: fc.constantFrom('OpenAI', 'Anthropic', 'Google'),
          }),
          { minLength: 3, maxLength: 6 }
        ),
        // Generate number of models to select (at least 2)
        fc.integer({ min: 2, max: 5 }),
        async (modelData, numToSelect) => {
          // Create unique models by both ID and name
          const uniqueModels = Array.from(
            new Map(modelData.map((m, idx) => [`${m.id}-${idx}`, { ...m, id: `${m.id}-${idx}`, name: `${m.name}-${idx}` }])).values()
          );
          
          if (uniqueModels.length < numToSelect) return;

          const models = uniqueModels.map(m => 
            createMockModel(m.id, m.name, m.provider)
          );

          vi.spyOn(api, 'getAvailableModels').mockResolvedValue(models);

          const mockOnSelectionChange = vi.fn();
          const user = userEvent.setup();

          // Start with one model selected
          const { unmount } = render(
            <ModelSelector
              selectedModels={[models[0].id]}
              onSelectionChange={mockOnSelectionChange}
            />
          );

          await waitFor(() => {
            expect(screen.queryByText(/Loading/i)).not.toBeInTheDocument();
          });

          // Select additional models (escape regex special chars)
          for (let i = 1; i < Math.min(numToSelect, models.length); i++) {
            const checkbox = screen.getByLabelText(new RegExp(escapeRegex(models[i].name), 'i'));
            await user.click(checkbox);
          }

          // Verify onSelectionChange was called multiple times
          expect(mockOnSelectionChange.mock.calls.length).toBeGreaterThanOrEqual(numToSelect - 1);

          // Verify the last call includes multiple models
          const lastCall = mockOnSelectionChange.mock.calls[mockOnSelectionChange.mock.calls.length - 1];
          if (lastCall) {
            expect(lastCall[0].length).toBeGreaterThanOrEqual(2);
          }

          unmount();
        }
      ),
      { numRuns: 20 } // Reduced for performance
    );
  }, 10000); // 10 second timeout

  /**
   * **Feature: kepler-web-interface, Property 13: Selected models in request**
   * 
   * For any verification request, the API payload should include all selected 
   * model identifiers.
   * 
   * **Validates: Requirements 4.5**
   */
  it('Property 13: should pass all selected model IDs to parent', async () => {
    await fc.assert(
      fc.asyncProperty(
        // Generate a list of models
        fc.array(
          fc.record({
            id: fc.string({ minLength: 1, maxLength: 20 }).map(s => s.replace(/[^a-zA-Z0-9-]/g, '_')),
            // Generate valid model names
            name: fc.string({ minLength: 3, maxLength: 30 })
              .filter(s => s.trim().length >= 3)
              .map(s => s.trim()),
            provider: fc.constantFrom('OpenAI', 'Anthropic'),
          }),
          { minLength: 2, maxLength: 5 }
        ),
        async (modelData) => {
          // Create unique models by both ID and name
          const uniqueModels = Array.from(
            new Map(modelData.map((m, idx) => [`${m.id}-${idx}`, { ...m, id: `${m.id}-${idx}`, name: `${m.name}-${idx}` }])).values()
          );
          
          if (uniqueModels.length < 2) return;

          const models = uniqueModels.map(m => 
            createMockModel(m.id, m.name, m.provider)
          );

          vi.spyOn(api, 'getAvailableModels').mockResolvedValue(models);

          const mockOnSelectionChange = vi.fn();
          const user = userEvent.setup();

          const { unmount } = render(
            <ModelSelector
              selectedModels={[models[0].id]}
              onSelectionChange={mockOnSelectionChange}
            />
          );

          await waitFor(() => {
            expect(screen.queryByText(/Loading/i)).not.toBeInTheDocument();
          });

          // Select the second model (escape regex special chars)
          const checkbox = screen.getByLabelText(new RegExp(escapeRegex(models[1].name), 'i'));
          await user.click(checkbox);

          // Verify onSelectionChange was called with both model IDs
          expect(mockOnSelectionChange).toHaveBeenCalled();
          const lastCall = mockOnSelectionChange.mock.calls[mockOnSelectionChange.mock.calls.length - 1];
          
          if (lastCall) {
            const selectedIds = lastCall[0];
            expect(selectedIds).toContain(models[0].id);
            expect(selectedIds).toContain(models[1].id);
            expect(selectedIds.length).toBe(2);
          }

          unmount();
        }
      ),
      { numRuns: 20 } // Reduced for performance
    );
  }, 10000); // 10 second timeout

  /**
   * Additional property: Component should handle API errors gracefully
   * 
   * For any API error, the component should display an error message
   * and provide a retry option.
   */
  it('Property: should handle API errors gracefully', async () => {
    await fc.assert(
      fc.asyncProperty(
        fc.string({ minLength: 10, maxLength: 100 }), // Error message
        async (errorMessage) => {
          // Mock API to reject
          vi.spyOn(api, 'getAvailableModels').mockRejectedValue(
            new api.APIError(errorMessage, 500, errorMessage)
          );

          const mockOnSelectionChange = vi.fn();

          const { unmount } = render(
            <ModelSelector
              selectedModels={[]}
              onSelectionChange={mockOnSelectionChange}
            />
          );

          // Wait for error to appear
          await waitFor(() => {
            expect(screen.queryByText(/Loading/i)).not.toBeInTheDocument();
          });

          // Verify error message is displayed
          expect(screen.getByRole('alert')).toBeInTheDocument();

          // Verify retry button is present
          expect(screen.getByRole('button', { name: /Retry/i })).toBeInTheDocument();

          unmount();
        }
      ),
      { numRuns: 50 }
    );
  });
});
