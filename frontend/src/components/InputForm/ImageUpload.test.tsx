import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { ImageUpload } from './ImageUpload';

/**
 * Unit Tests for ImageUpload Component
 * 
 * These tests verify specific examples and edge cases for the ImageUpload component.
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

describe('ImageUpload Component', () => {
  beforeEach(() => {
    // Mock FileReader
    global.FileReader = class MockFileReader {
      result: string | ArrayBuffer | null = null;
      onloadend: ((this: FileReader, ev: ProgressEvent<FileReader>) => any) | null = null;
      onerror: ((this: FileReader, ev: ProgressEvent<FileReader>) => any) | null = null;

      readAsDataURL(_blob: Blob) {
        this.result = createDataURL('image/png', 'mock-content');
        setTimeout(() => {
          if (this.onloadend) {
            this.onloadend.call(this as any, {} as any);
          }
        }, 0);
      }
    } as any;
  });

  it('should render the upload button', () => {
    const mockOnImageSelect = vi.fn();
    render(<ImageUpload onImageSelect={mockOnImageSelect} />);

    expect(screen.getByText(/Choose Image/i)).toBeInTheDocument();
  });

  it('should show error for invalid file type (PDF)', () => {
    const mockOnImageSelect = vi.fn();
    render(<ImageUpload onImageSelect={mockOnImageSelect} />);

    const file = createMockFile('document.pdf', 1024, 'application/pdf');
    const input = screen.getByLabelText(/Upload Image/i) as HTMLInputElement;

    Object.defineProperty(input, 'files', {
      value: [file],
      writable: false,
      configurable: true,
    });
    fireEvent.change(input);

    expect(screen.getByText(/Invalid file type/i)).toBeInTheDocument();
  });

  it('should show error for file exceeding 10MB', () => {
    const mockOnImageSelect = vi.fn();
    render(<ImageUpload onImageSelect={mockOnImageSelect} />);

    const file = createMockFile('large.jpg', 11 * 1024 * 1024, 'image/jpeg');
    const input = screen.getByLabelText(/Upload Image/i) as HTMLInputElement;

    Object.defineProperty(input, 'files', {
      value: [file],
      writable: false,
      configurable: true,
    });
    fireEvent.change(input);

    expect(screen.getByText(/exceeds 10MB limit/i)).toBeInTheDocument();
  });

  it('should accept valid JPEG file', async () => {
    const mockOnImageSelect = vi.fn();
    render(<ImageUpload onImageSelect={mockOnImageSelect} />);

    const file = createMockFile('photo.jpg', 1024 * 1024, 'image/jpeg');
    const input = screen.getByLabelText(/Upload Image/i) as HTMLInputElement;

    Object.defineProperty(input, 'files', {
      value: [file],
      writable: false,
      configurable: true,
    });
    fireEvent.change(input);

    await waitFor(() => {
      expect(screen.queryByRole('alert')).not.toBeInTheDocument();
      expect(screen.getByAltText('Preview')).toBeInTheDocument();
    });
  });

  it('should accept valid PNG file', async () => {
    const mockOnImageSelect = vi.fn();
    render(<ImageUpload onImageSelect={mockOnImageSelect} />);

    const file = createMockFile('image.png', 512 * 1024, 'image/png');
    const input = screen.getByLabelText(/Upload Image/i) as HTMLInputElement;

    Object.defineProperty(input, 'files', {
      value: [file],
      writable: false,
      configurable: true,
    });
    fireEvent.change(input);

    await waitFor(() => {
      expect(screen.getByAltText('Preview')).toBeInTheDocument();
    });
  });

  it('should accept valid GIF file', async () => {
    const mockOnImageSelect = vi.fn();
    render(<ImageUpload onImageSelect={mockOnImageSelect} />);

    const file = createMockFile('animation.gif', 256 * 1024, 'image/gif');
    const input = screen.getByLabelText(/Upload Image/i) as HTMLInputElement;

    Object.defineProperty(input, 'files', {
      value: [file],
      writable: false,
      configurable: true,
    });
    fireEvent.change(input);

    await waitFor(() => {
      expect(screen.getByAltText('Preview')).toBeInTheDocument();
    });
  });

  it('should accept valid WebP file', async () => {
    const mockOnImageSelect = vi.fn();
    render(<ImageUpload onImageSelect={mockOnImageSelect} />);

    const file = createMockFile('modern.webp', 128 * 1024, 'image/webp');
    const input = screen.getByLabelText(/Upload Image/i) as HTMLInputElement;

    Object.defineProperty(input, 'files', {
      value: [file],
      writable: false,
      configurable: true,
    });
    fireEvent.change(input);

    await waitFor(() => {
      expect(screen.getByAltText('Preview')).toBeInTheDocument();
    });
  });

  it('should display filename after upload', async () => {
    const mockOnImageSelect = vi.fn();
    render(<ImageUpload onImageSelect={mockOnImageSelect} />);

    const filename = 'my-photo.jpg';
    const file = createMockFile(filename, 1024, 'image/jpeg');
    const input = screen.getByLabelText(/Upload Image/i) as HTMLInputElement;

    Object.defineProperty(input, 'files', {
      value: [file],
      writable: false,
      configurable: true,
    });
    fireEvent.change(input);

    await waitFor(() => {
      expect(screen.getByText(filename)).toBeInTheDocument();
    });
  });

  it('should show remove button after upload', async () => {
    const mockOnImageSelect = vi.fn();
    render(<ImageUpload onImageSelect={mockOnImageSelect} />);

    const file = createMockFile('photo.jpg', 1024, 'image/jpeg');
    const input = screen.getByLabelText(/Upload Image/i) as HTMLInputElement;

    Object.defineProperty(input, 'files', {
      value: [file],
      writable: false,
      configurable: true,
    });
    fireEvent.change(input);

    await waitFor(() => {
      expect(screen.getByRole('button', { name: /Remove image/i })).toBeInTheDocument();
    });
  });

  it('should clear image when remove button is clicked', async () => {
    const mockOnImageSelect = vi.fn();
    render(<ImageUpload onImageSelect={mockOnImageSelect} />);

    const file = createMockFile('photo.jpg', 1024, 'image/jpeg');
    const input = screen.getByLabelText(/Upload Image/i) as HTMLInputElement;

    Object.defineProperty(input, 'files', {
      value: [file],
      writable: false,
      configurable: true,
    });
    fireEvent.change(input);

    await waitFor(() => {
      expect(screen.getByAltText('Preview')).toBeInTheDocument();
    });

    const removeButton = screen.getByRole('button', { name: /Remove image/i });
    fireEvent.click(removeButton);

    expect(screen.queryByAltText('Preview')).not.toBeInTheDocument();
    expect(mockOnImageSelect).toHaveBeenCalledWith(null);
  });

  it('should change button text after image is selected', async () => {
    const mockOnImageSelect = vi.fn();
    render(<ImageUpload onImageSelect={mockOnImageSelect} />);

    expect(screen.getByText(/Choose Image/i)).toBeInTheDocument();

    const file = createMockFile('photo.jpg', 1024, 'image/jpeg');
    const input = screen.getByLabelText(/Upload Image/i) as HTMLInputElement;

    Object.defineProperty(input, 'files', {
      value: [file],
      writable: false,
      configurable: true,
    });
    fireEvent.change(input);

    await waitFor(() => {
      expect(screen.getByText(/Change Image/i)).toBeInTheDocument();
    });
  });

  it('should be disabled when disabled prop is true', () => {
    const mockOnImageSelect = vi.fn();
    render(<ImageUpload onImageSelect={mockOnImageSelect} disabled={true} />);

    const input = screen.getByLabelText(/Upload Image/i) as HTMLInputElement;
    expect(input).toBeDisabled();
  });

  it('should call onImageSelect with base64 string for valid image', async () => {
    const mockOnImageSelect = vi.fn();
    render(<ImageUpload onImageSelect={mockOnImageSelect} />);

    const file = createMockFile('photo.jpg', 1024, 'image/jpeg');
    const input = screen.getByLabelText(/Upload Image/i) as HTMLInputElement;

    Object.defineProperty(input, 'files', {
      value: [file],
      writable: false,
      configurable: true,
    });
    fireEvent.change(input);

    await waitFor(() => {
      expect(mockOnImageSelect).toHaveBeenCalled();
      const callArg = mockOnImageSelect.mock.calls[0]?.[0];
      expect(typeof callArg).toBe('string');
      expect(callArg).toMatch(/^[A-Za-z0-9+/=]*$/);
    });
  });

  it('should handle edge case: exactly 10MB file', async () => {
    const mockOnImageSelect = vi.fn();
    render(<ImageUpload onImageSelect={mockOnImageSelect} />);

    const file = createMockFile('exact.jpg', 10 * 1024 * 1024, 'image/jpeg');
    const input = screen.getByLabelText(/Upload Image/i) as HTMLInputElement;

    Object.defineProperty(input, 'files', {
      value: [file],
      writable: false,
      configurable: true,
    });
    fireEvent.change(input);

    await waitFor(() => {
      expect(screen.queryByRole('alert')).not.toBeInTheDocument();
      expect(screen.getByAltText('Preview')).toBeInTheDocument();
    });
  });

  it('should handle edge case: 1 byte over 10MB', () => {
    const mockOnImageSelect = vi.fn();
    render(<ImageUpload onImageSelect={mockOnImageSelect} />);

    const file = createMockFile('over.jpg', 10 * 1024 * 1024 + 1, 'image/jpeg');
    const input = screen.getByLabelText(/Upload Image/i) as HTMLInputElement;

    Object.defineProperty(input, 'files', {
      value: [file],
      writable: false,
      configurable: true,
    });
    fireEvent.change(input);

    expect(screen.getByText(/exceeds 10MB limit/i)).toBeInTheDocument();
  });

  it('should handle no file selected (user cancels)', () => {
    const mockOnImageSelect = vi.fn();
    render(<ImageUpload onImageSelect={mockOnImageSelect} />);

    const input = screen.getByLabelText(/Upload Image/i) as HTMLInputElement;

    // Simulate user canceling file selection
    Object.defineProperty(input, 'files', {
      value: [],
      writable: false,
      configurable: true,
    });
    fireEvent.change(input);

    // Should not show any error or preview
    expect(screen.queryByRole('alert')).not.toBeInTheDocument();
    expect(screen.queryByAltText('Preview')).not.toBeInTheDocument();
  });
});
