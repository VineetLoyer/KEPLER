/**
 * Data Formatting Utilities
 * 
 * This module provides functions for formatting data for display.
 */

/**
 * Format confidence score as percentage
 * 
 * @param score - Score between 0 and 1
 * @param decimals - Number of decimal places (default: 1)
 * @returns Formatted percentage string
 */
export function formatPercentage(score: number, decimals: number = 1): string {
  return `${(score * 100).toFixed(decimals)}%`;
}

/**
 * Format timestamp to human-readable string
 * 
 * @param timestamp - ISO timestamp string
 * @returns Formatted date/time string
 */
export function formatTimestamp(timestamp: string): string {
  const date = new Date(timestamp);
  
  // Format as "Nov 20, 2025 at 3:45 PM"
  return date.toLocaleString('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
    hour: 'numeric',
    minute: '2-digit',
    hour12: true,
  });
}

/**
 * Truncate text to specified length
 * 
 * @param text - Text to truncate
 * @param maxLength - Maximum length
 * @returns Truncated text with ellipsis if needed
 */
export function truncateText(text: string, maxLength: number): string {
  if (text.length <= maxLength) return text;
  return text.substring(0, maxLength - 3) + '...';
}

/**
 * Get verdict color class
 * 
 * @param verdict - Verdict classification
 * @returns CSS class name for verdict color
 */
export function getVerdictColorClass(verdict: string): string {
  switch (verdict) {
    case 'Supported':
      return 'verdict-supported';
    case 'Refuted':
      return 'verdict-refuted';
    case 'Not Enough Information':
      return 'verdict-nei';
    default:
      return 'verdict-unknown';
  }
}

/**
 * Format file size to human-readable string
 * 
 * @param bytes - File size in bytes
 * @returns Formatted size string (e.g., "2.5 MB")
 */
export function formatFileSize(bytes: number): string {
  if (bytes === 0) return '0 Bytes';
  
  const k = 1024;
  const sizes = ['Bytes', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  
  return `${parseFloat((bytes / Math.pow(k, i)).toFixed(2))} ${sizes[i]}`;
}
