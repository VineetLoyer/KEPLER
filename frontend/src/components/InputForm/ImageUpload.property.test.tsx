import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import * as fc from 'fast-check';
import { ImageUpload } from './ImageUpload';

/**
 * Property-Based Tests for ImageUpload Component
 * 
 * Task 7.1: Write property tests for image upload
 * - Property 6: Image file type validation
 * - Property 7: Image file size validation
 * - Property 8: Image preview display
 * - Property 9: Multimodal data transmission
 * 
 * Requirements: 3.2, 3.3, 3.4, 3.5
 * 
 * These tests use fast-check to generate random inputs and verify
 * that the component behaves correctly across all possible inputs.
 */

// Helper to create a mock File object
function createMockFile(
  name: string,
  size: number,
  type: string,
  content: string = 'mock-image-content'
): File {
  // Create content that matches the desired size
  const paddedContent = content.padEnd(size, '0');
  const blob = new Blob([paddedContent], { type });
  const file = new File([blob], name, { type });
  
  // Ensure the size property is correctly set
  Object.defineProperty(file, 'size', {
    value: size,
    writable: false,
    configurable: true,
  });
  
  return file;
}

// Helper to create a data URL for testing
function createDataURL(type: string, content: string = 'test'): string {
  return `data:${type};base64,${btoa(content)}`;
}

describe('ImageUpload Property-Based Tests', () => {
  beforeEach(() => {
    // Mock FileReader
    (global as any).FileReader = class MockFileReader {
      result: string | ArrayBuffer | null = null;
      onloadend: ((this: FileReader, ev: ProgressEvent<FileReader>) => any) | null = null;
      onerror: ((this: FileReader, ev: ProgressEvent<FileReader>) => any) | null = null;

      readAsDataURL(_blob: Blob) {
        // Simulate successful read
        this.result = createDataURL('image/png', 'mock-content');
        setTimeout(() => {
          if (this.onloadend) {
            this.onloadend.call(this as any, {} as any);
          }
        }, 0);
      }
    } as any;
  });

  /**
   * **Feature: kepler-web-interface, Property 6: Image file type validation**
   * 
   * For any selected file, if the file type is not a supported image format 
   * (JPEG, PNG, GIF, WebP), the frontend should reject it and display an error.
   * 
   * **Validates: Requirements 3.2**
   */
  it('Property 6: should reject all unsupported file types', () => {
    fc.assert(
      fc.property(
        // Generate invalid MIME types (not image/jpeg, image/png, image/gif, image/webp)
        fc.oneof(
          fc.constant('application/pdf'),
          fc.constant('text/plain'),
          fc.constant('video/mp4'),
          fc.constant('audio/mp3'),
          fc.constant('application/zip'),
          fc.constant('image/bmp'),
          fc.constant('image/svg+xml'),
          fc.constant('image/tiff'),
          fc.stringMatching(/^(text|application|video|audio)\/[a-z]+$/)
            .filter(type => !type.startsWith('image/'))
        ),
        fc.string({ minLength: 1, maxLength: 50 }).map(s => s + '.txt'), // filename
        fc.integer({ min: 1, max: 1024 * 1024 }), // size in bytes (under 10MB)
        (invalidType, filename, size) => {
          const mockOnImageSelect = vi.fn();

          const { unmount } = render(
            <ImageUpload onImageSelect={mockOnImageSelect} />
          );

          // Create a file with invalid type
          const file = createMockFile(filename, size, invalidType);

          // Get the file input
          const input = screen.getByLabelText(/Upload Image/i) as HTMLInputElement;

          // Simulate file selection
          Object.defineProperty(input, 'files', {
            value: [file],
            writable: false,
            configurable: true,
          });
          fireEvent.change(input);

          // Verify that:
          // 1. An error message is displayed
          const errorMessage = screen.queryByText(/Invalid file type/i);
          expect(errorMessage).toBeInTheDocument();

          // 2. onImageSelect was NOT called with valid data
          expect(mockOnImageSelect).not.toHaveBeenCalledWith(expect.stringMatching(/^[A-Za-z0-9+/=]+$/));

          // 3. No preview is shown
          const preview = screen.queryByAltText('Preview');
          expect(preview).not.toBeInTheDocument();

          unmount();
        }
      ),
      { numRuns: 100 }
    );
  });

  /**
   * **Feature: kepler-web-interface, Property 7: Image file size validation**
   * 
   * For any selected image file, if the file size exceeds the maximum limit,
   * the frontend should reject it and display an error.
   * 
   * **Validates: Requirements 3.3**
   */
  it('Property 7: should reject all files exceeding 10MB size limit', () => {
    fc.assert(
      fc.property(
        // Generate valid image types
        fc.constantFrom('image/jpeg', 'image/png', 'image/gif', 'image/webp'),
        // Generate file sizes exceeding 10MB (10 * 1024 * 1024 bytes)
        // Use smaller range for performance
        fc.integer({ min: 10 * 1024 * 1024 + 1, max: 15 * 1024 * 1024 }),
        fc.string({ minLength: 1, maxLength: 50 }).map(s => s.replace(/[^a-zA-Z0-9]/g, '_') + '.jpg'), // filename
        (validType, oversizedBytes, filename) => {
          const mockOnImageSelect = vi.fn();

          const { unmount } = render(
            <ImageUpload onImageSelect={mockOnImageSelect} />
          );

          // Create a file with valid type but excessive size
          // Don't actually create the full content to avoid memory issues
          const file = new File([''], filename, { type: validType });
          Object.defineProperty(file, 'size', {
            value: oversizedBytes,
            writable: false,
            configurable: true,
          });

          // Get the file input
          const input = screen.getByLabelText(/Upload Image/i) as HTMLInputElement;

          // Simulate file selection - use configurable property to avoid redefine error
          Object.defineProperty(input, 'files', {
            value: [file],
            writable: false,
            configurable: true,
          });
          fireEvent.change(input);

          // Verify that:
          // 1. An error message about size is displayed
          const errorMessage = screen.queryByText(/exceeds 10MB limit/i);
          expect(errorMessage).toBeInTheDocument();

          // 2. onImageSelect was NOT called with valid data
          expect(mockOnImageSelect).not.toHaveBeenCalledWith(expect.stringMatching(/^[A-Za-z0-9+/=]+$/));

          // 3. No preview is shown
          const preview = screen.queryByAltText('Preview');
          expect(preview).not.toBeInTheDocument();

          unmount();
        }
      ),
      { numRuns: 100 }
    );
  });

  /**
   * **Feature: kepler-web-interface, Property 8: Image preview display**
   * 
   * For any valid image selection, the frontend should display a preview of the image.
   * 
   * **Validates: Requirements 3.4**
   */
  it('Property 8: should display preview for all valid image files', async () => {
    await fc.assert(
      fc.asyncProperty(
        // Generate valid image types
        fc.constantFrom('image/jpeg', 'image/png', 'image/gif', 'image/webp'),
        // Generate valid file sizes (under 10MB) - use smaller range for performance
        fc.integer({ min: 100, max: 1024 * 1024 }),
        fc.string({ minLength: 1, maxLength: 50 }).map(s => s.replace(/[^a-zA-Z0-9]/g, '_') + '.jpg'), // safe filename
        async (validType, validSize, filename) => {
          const mockOnImageSelect = vi.fn();

          const { unmount } = render(
            <ImageUpload onImageSelect={mockOnImageSelect} />
          );

          // Create a valid file - don't create full content for performance
          const file = new File(['mock'], filename, { type: validType });
          Object.defineProperty(file, 'size', {
            value: validSize,
            writable: false,
            configurable: true,
          });

          // Get the file input
          const input = screen.getByLabelText(/Upload Image/i) as HTMLInputElement;

          // Simulate file selection
          Object.defineProperty(input, 'files', {
            value: [file],
            writable: false,
            configurable: true,
          });
          fireEvent.change(input);

          // Wait for async operations (FileReader)
          await waitFor(() => {
            // Verify that:
            // 1. No error message is displayed
            const errorMessage = screen.queryByRole('alert');
            expect(errorMessage).not.toBeInTheDocument();

            // 2. Preview image is displayed
            const preview = screen.queryByAltText('Preview');
            expect(preview).toBeInTheDocument();

            // 3. Filename is displayed
            const filenameDisplay = screen.queryByText(filename);
            expect(filenameDisplay).toBeInTheDocument();
          }, { timeout: 1000 });

          unmount();
        }
      ),
      { numRuns: 100 }
    );
  });

  /**
   * **Feature: kepler-web-interface, Property 9: Multimodal data transmission**
   * 
   * For any submission with both text and image, the API request should include 
   * both data types. This test verifies that the ImageUpload component correctly
   * converts images to base64 and calls onImageSelect with the base64 string.
   * 
   * **Validates: Requirements 3.5**
   */
  it('Property 9: should convert all valid images to base64 for transmission', async () => {
    await fc.assert(
      fc.asyncProperty(
        // Generate valid image types
        fc.constantFrom('image/jpeg', 'image/png', 'image/gif', 'image/webp'),
        // Generate valid file sizes - smaller range for performance
        fc.integer({ min: 100, max: 100 * 1024 }), // 100 bytes to 100KB
        fc.string({ minLength: 1, maxLength: 30 }).map(s => s.replace(/[^a-zA-Z0-9]/g, '_') + '.jpg'),
        async (validType, validSize, filename) => {
          const mockOnImageSelect = vi.fn();

          const { unmount } = render(
            <ImageUpload onImageSelect={mockOnImageSelect} />
          );

          // Create a valid file - don't create full content for performance
          const file = new File(['mock'], filename, { type: validType });
          Object.defineProperty(file, 'size', {
            value: validSize,
            writable: false,
            configurable: true,
          });

          // Get the file input
          const input = screen.getByLabelText(/Upload Image/i) as HTMLInputElement;

          // Simulate file selection
          Object.defineProperty(input, 'files', {
            value: [file],
            writable: false,
            configurable: true,
          });
          fireEvent.change(input);

          // Wait for async operations
          await waitFor(() => {
            // Verify that onImageSelect was called with a base64 string
            expect(mockOnImageSelect).toHaveBeenCalled();
            
            // Get the argument passed to onImageSelect
            const callArg = mockOnImageSelect.mock.calls[0]?.[0];
            
            // Verify it's a string (base64)
            expect(typeof callArg).toBe('string');
            
            // Verify it's not null
            expect(callArg).not.toBeNull();
            
            // Base64 strings should only contain valid base64 characters
            if (callArg) {
              expect(callArg).toMatch(/^[A-Za-z0-9+/=]*$/);
            }
          }, { timeout: 1000 });

          unmount();
        }
      ),
      { numRuns: 100 }
    );
  });

  /**
   * Additional property: Remove functionality should clear all state
   * 
   * For any valid image that has been uploaded, clicking remove should
   * clear the preview and call onImageSelect with null.
   */
  it('Property: should clear image state when remove is clicked', async () => {
    await fc.assert(
      fc.asyncProperty(
        fc.constantFrom('image/jpeg', 'image/png', 'image/gif', 'image/webp'),
        fc.integer({ min: 100, max: 100 * 1024 }),
        fc.string({ minLength: 1, maxLength: 30 }).map(s => s.replace(/[^a-zA-Z0-9]/g, '_') + '.jpg'),
        async (validType, validSize, filename) => {
          const mockOnImageSelect = vi.fn();

          const { unmount } = render(
            <ImageUpload onImageSelect={mockOnImageSelect} />
          );

          // Upload a valid file - don't create full content for performance
          const file = new File(['mock'], filename, { type: validType });
          Object.defineProperty(file, 'size', {
            value: validSize,
            writable: false,
            configurable: true,
          });
          const input = screen.getByLabelText(/Upload Image/i) as HTMLInputElement;
          Object.defineProperty(input, 'files', {
            value: [file],
            writable: false,
            configurable: true,
          });
          fireEvent.change(input);

          // Wait for upload to complete
          await waitFor(() => {
            expect(screen.queryByAltText('Preview')).toBeInTheDocument();
          }, { timeout: 1000 });

          // Clear the mock to check the remove call
          mockOnImageSelect.mockClear();

          // Click remove button
          const removeButton = screen.getByRole('button', { name: /Remove image/i });
          fireEvent.click(removeButton);

          // Verify that:
          // 1. Preview is removed
          expect(screen.queryByAltText('Preview')).not.toBeInTheDocument();

          // 2. onImageSelect was called with null
          expect(mockOnImageSelect).toHaveBeenCalledWith(null);

          // 3. Remove button is no longer visible
          expect(screen.queryByRole('button', { name: /Remove image/i })).not.toBeInTheDocument();

          unmount();
        }
      ),
      { numRuns: 100 }
    );
  });

  /**
   * Property: Component should handle disabled state correctly
   * 
   * For any disabled state, the component should prevent file selection
   * and button interactions.
   */
  it('Property: should prevent interactions when disabled', () => {
    fc.assert(
      fc.property(
        fc.boolean(), // disabled state
        (isDisabled) => {
          const mockOnImageSelect = vi.fn();

          const { unmount } = render(
            <ImageUpload onImageSelect={mockOnImageSelect} disabled={isDisabled} />
          );

          // Get the file input
          const input = screen.getByLabelText(/Upload Image/i) as HTMLInputElement;

          // Verify disabled state matches
          if (isDisabled) {
            expect(input).toBeDisabled();
          } else {
            expect(input).not.toBeDisabled();
          }

          unmount();
        }
      ),
      { numRuns: 100 }
    );
  });
});
