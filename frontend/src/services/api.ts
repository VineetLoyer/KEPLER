/**
 * API Service Layer
 * 
 * This module provides functions for communicating with the KEPLER REST API.
 * It handles request/response formatting, error handling, and retry logic.
 * 
 * Requirements: 2.3, 10.2, 10.3
 */

import axios, { AxiosError } from 'axios';

// Get API base URL from environment variable
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

// Create axios instance with default configuration
const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 120000, // 2 minutes timeout for verification requests
});

/**
 * Verification request payload
 */
export type VerificationRequest = {
  text?: string;
  image?: string; // Base64 encoded
  selected_models: string[];
}

/**
 * Verification response from API
 */
export type VerificationResponse = {
  session_id: string;
  original_input: unknown;
  atomic_claims: unknown[];
  consensus_verdict: unknown;
  confidence_score: unknown;
  processing_metadata: unknown;
  trace_log: unknown[];
}

/**
 * Model information
 */
export type ModelInfo = {
  id: string;
  name: string;
  provider: string;
  version: string;
}

/**
 * Models list response
 */
export type ModelsResponse = {
  models: ModelInfo[];
}

/**
 * Health check response
 */
export type HealthResponse = {
  status: string;
  version: string;
}

/**
 * API Error class
 */
export class APIError extends Error {
  statusCode?: number;
  detail?: string;
  
  constructor(
    message: string,
    statusCode?: number,
    detail?: string
  ) {
    super(message);
    this.name = 'APIError';
    this.statusCode = statusCode;
    this.detail = detail;
  }
}

/**
 * Handle API errors and convert to APIError
 */
function handleAPIError(error: unknown): never {
  if (axios.isAxiosError(error)) {
    const axiosError = error as AxiosError<{
      detail?: string;
      error?: string;
    }>;
    
    if (axiosError.response) {
      // Server responded with error
      const statusCode = axiosError.response.status;
      const data = axiosError.response.data;
      const detail = data?.detail || data?.error || 'An error occurred';
      
      throw new APIError(
        `API Error: ${detail}`,
        statusCode,
        detail
      );
    } else if (axiosError.request) {
      // Request made but no response
      throw new APIError(
        'No response from server. Please check your connection.',
        undefined,
        'Network error'
      );
    } else {
      // Something else happened
      throw new APIError(
        'Failed to send request',
        undefined,
        axiosError.message
      );
    }
  }
  
  // Unknown error type
  throw new APIError(
    'An unexpected error occurred',
    undefined,
    String(error)
  );
}

/**
 * Verify a claim using the KEPLER pipeline
 * 
 * @param text - Claim text (optional if image provided)
 * @param image - Base64 encoded image (optional if text provided)
 * @param selectedModels - Array of model IDs to use for verification
 * @returns Verification results
 */
export async function verifyClaim(
  text: string | undefined,
  image: string | null,
  selectedModels: string[]
): Promise<VerificationResponse> {
  try {
    const payload: VerificationRequest = {
      selected_models: selectedModels,
    };
    
    if (text) {
      payload.text = text;
    }
    
    if (image) {
      payload.image = image;
    }
    
    const response = await api.post<VerificationResponse>('/api/verify', payload);
    return response.data;
  } catch (error) {
    handleAPIError(error);
  }
}

/**
 * Get list of available LLM models
 * 
 * @returns List of available models
 */
export async function getAvailableModels(): Promise<ModelInfo[]> {
  try {
    const response = await api.get<ModelsResponse>('/api/models');
    return response.data.models;
  } catch (error) {
    handleAPIError(error);
  }
}

/**
 * Check API health status
 * 
 * @returns Health status and version
 */
export async function checkHealth(): Promise<HealthResponse> {
  try {
    const response = await api.get<HealthResponse>('/api/health');
    return response.data;
  } catch (error) {
    handleAPIError(error);
  }
}

export default {
  verifyClaim,
  getAvailableModels,
  checkHealth,
};
