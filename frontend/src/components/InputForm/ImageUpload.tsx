import { useState, useRef } from 'react';
import type { ChangeEvent } from 'react';
import { isValidImageType, isValidImageSize, fileToBase64 } from '../../utils/validation';
import './ImageUpload.css';

/**
 * ImageUpload Component
 * 
 * A file input component for uploading images for multimodal verification.
 * Includes validation, preview, and base64 conversion.
 * 
 * Requirements: 3.1, 3.2, 3.3, 3.4, 3.5
 */

interface ImageUploadProps {
  onImageSelect: (base64Image: string | null) => void;
  disabled?: boolean;
}

export const ImageUpload = ({ onImageSelect, disabled = false }: ImageUploadProps) => {
  const [preview, setPreview] = useState<string | null>(null);
  const [error, setError] = useState<string>('');
  const [fileName, setFileName] = useState<string>('');
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleFileSelect = async (e: ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    
    if (!file) {
      return;
    }

    // Clear previous error
    setError('');

    // Validate file type (Requirement 3.2)
    if (!isValidImageType(file)) {
      setError('Invalid file type. Please upload a JPEG, PNG, GIF, or WebP image.');
      clearImage();
      return;
    }

    // Validate file size (Requirement 3.3)
    if (!isValidImageSize(file)) {
      setError('File size exceeds 10MB limit. Please choose a smaller image.');
      clearImage();
      return;
    }

    try {
      // Create preview (Requirement 3.4)
      const reader = new FileReader();
      reader.onloadend = () => {
        if (typeof reader.result === 'string') {
          setPreview(reader.result);
        }
      };
      reader.readAsDataURL(file);

      // Convert to base64 for API transmission (Requirement 3.5)
      const base64 = await fileToBase64(file);
      setFileName(file.name);
      onImageSelect(base64);
    } catch (err) {
      setError('Failed to process image. Please try again.');
      clearImage();
    }
  };

  const clearImage = () => {
    setPreview(null);
    setFileName('');
    onImageSelect(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  const handleRemove = () => {
    clearImage();
    setError('');
  };

  return (
    <div className="image-upload">
      <div className="image-upload-header">
        <label htmlFor="image-upload-input" className="image-upload-label">
          Upload Image (Optional)
        </label>
      </div>

      <div className="image-upload-controls">
        <input
          ref={fileInputRef}
          type="file"
          accept="image/jpeg,image/png,image/gif,image/webp"
          onChange={handleFileSelect}
          disabled={disabled}
          id="image-upload-input"
          className="image-upload-input"
          aria-invalid={!!error}
          aria-describedby={error ? 'image-upload-error' : undefined}
        />
        <label 
          htmlFor="image-upload-input" 
          className={`image-upload-button ${disabled ? 'disabled' : ''}`}
        >
          {preview ? 'Change Image' : 'Choose Image'}
        </label>

        {preview && (
          <button
            type="button"
            onClick={handleRemove}
            disabled={disabled}
            className="image-remove-button"
            aria-label="Remove image"
          >
            Remove
          </button>
        )}
      </div>

      {error && (
        <div id="image-upload-error" className="error-message" role="alert">
          {error}
        </div>
      )}

      {preview && (
        <div className="image-preview">
          <img src={preview} alt="Preview" />
          <p className="image-filename">{fileName}</p>
        </div>
      )}
    </div>
  );
};
