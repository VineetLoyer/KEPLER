/**
 * Input Validation Utilities
 * 
 * This module provides validation functions for user input.
 */

/**
 * Validate that text is not empty or whitespace-only
 * 
 * @param text - Text to validate
 * @returns True if valid, false otherwise
 */
export function isValidText(text: string | undefined): boolean {
  if (!text) return false;
  return text.trim().length > 0;
}

/**
 * Validate image file type
 * 
 * @param file - File to validate
 * @returns True if valid image type, false otherwise
 */
export function isValidImageType(file: File): boolean {
  const allowedTypes = ['image/jpeg', 'image/png', 'image/gif', 'image/webp'];
  return allowedTypes.includes(file.type);
}

/**
 * Validate image file size
 * 
 * @param file - File to validate
 * @param maxSizeMB - Maximum size in megabytes (default: 10)
 * @returns True if within size limit, false otherwise
 */
export function isValidImageSize(file: File, maxSizeMB: number = 10): boolean {
  const maxSizeBytes = maxSizeMB * 1024 * 1024;
  return file.size <= maxSizeBytes;
}

/**
 * Validate that at least one model is selected
 * 
 * @param models - Array of selected model IDs
 * @returns True if at least one model selected, false otherwise
 */
export function hasMinimumModels(models: string[]): boolean {
  return models.length >= 1;
}

/**
 * Convert file to base64 string
 * 
 * @param file - File to convert
 * @returns Promise resolving to base64 string
 */
export function fileToBase64(file: File): Promise<string> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    
    reader.onloadend = () => {
      if (typeof reader.result === 'string') {
        // Remove data URL prefix (e.g., "data:image/png;base64,")
        const base64 = reader.result.split(',')[1];
        resolve(base64);
      } else {
        reject(new Error('Failed to read file as base64'));
      }
    };
    
    reader.onerror = () => {
      reject(new Error('Failed to read file'));
    };
    
    reader.readAsDataURL(file);
  });
}
