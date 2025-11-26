/**
 * Tests for API Service Layer
 * 
 * Task 9.1: Write tests for API service
 * - Test API calls with mocked responses
 * - Test error handling for different status codes
 * - Test network failure scenarios
 * 
 * Requirements: 2.3
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import axios from 'axios';
import {
  verifyClaim,
  getAvailableModels,
  checkHealth,
  APIError,
  type VerificationResponse,
  type ModelInfo,
  type HealthResponse,
} from './api';

// Mock axios module
vi.mock('axios', () => {
  const mockAxiosInstance = {
    get: vi.fn(),
    post: vi.fn(),
  };

  return {
    default: {
      create: vi.fn(() => mockAxiosInstance),
      isAxiosError: vi.fn((error: any) => error && error.isAxiosError === true),
    },
    isAxiosError: vi.fn((error: any) => error && error.isAxiosError === true),
  };
});

describe('API Service', () => {
  // Get the mocked axios instance
  let mockAxiosInstance: any;

  beforeEach(async () => {
    // Reset all mocks before each test
    vi.clearAllMocks();
    
    // Re-import to get fresh instance
    const axiosModule = await import('axios');
    mockAxiosInstance = (axiosModule.default.create as any)();
  });

  describe('verifyClaim', () => {
    const mockVerificationResponse: VerificationResponse = {
      session_id: 'test-session-123',
      original_input: { text: 'Test claim' },
      atomic_claims: [{ id: 1, text: 'Test claim' }],
      consensus_verdict: { classification: 'Supported' },
      confidence_score: { overall_score: 0.85 },
      processing_metadata: { duration: 1000 },
      trace_log: [],
    };

    it('should successfully verify a text claim', async () => {
      mockAxiosInstance.post.mockResolvedValue({
        data: mockVerificationResponse,
      });

      const result = await verifyClaim('Test claim', null, ['model1']);

      expect(mockAxiosInstance.post).toHaveBeenCalledWith('/api/verify', {
        text: 'Test claim',
        selected_models: ['model1'],
      });
      expect(result).toEqual(mockVerificationResponse);
    });

    it('should successfully verify a claim with image', async () => {
      const base64Image = 'data:image/png;base64,iVBORw0KGgoAAAANS';
      mockAxiosInstance.post.mockResolvedValue({
        data: mockVerificationResponse,
      });

      const result = await verifyClaim('Test claim', base64Image, ['model1']);

      expect(mockAxiosInstance.post).toHaveBeenCalledWith('/api/verify', {
        text: 'Test claim',
        image: base64Image,
        selected_models: ['model1'],
      });
      expect(result).toEqual(mockVerificationResponse);
    });

    it('should verify with only image (no text)', async () => {
      const base64Image = 'data:image/png;base64,iVBORw0KGgoAAAANS';
      mockAxiosInstance.post.mockResolvedValue({
        data: mockVerificationResponse,
      });

      const result = await verifyClaim(undefined, base64Image, ['model1']);

      expect(mockAxiosInstance.post).toHaveBeenCalledWith('/api/verify', {
        image: base64Image,
        selected_models: ['model1'],
      });
      expect(result).toEqual(mockVerificationResponse);
    });

    it('should verify with multiple models', async () => {
      mockAxiosInstance.post.mockResolvedValue({
        data: mockVerificationResponse,
      });

      const result = await verifyClaim('Test claim', null, ['model1', 'model2', 'model3']);

      expect(mockAxiosInstance.post).toHaveBeenCalledWith('/api/verify', {
        text: 'Test claim',
        selected_models: ['model1', 'model2', 'model3'],
      });
      expect(result).toEqual(mockVerificationResponse);
    });

    it('should handle 400 Bad Request error', async () => {
      const errorResponse = {
        response: {
          status: 400,
          data: {
            detail: 'Invalid request: missing required fields',
          },
        },
        isAxiosError: true,
      };

      mockAxiosInstance.post.mockRejectedValue(errorResponse);

      await expect(verifyClaim('', null, [])).rejects.toThrow(APIError);
      await expect(verifyClaim('', null, [])).rejects.toThrow(
        'API Error: Invalid request: missing required fields'
      );

      try {
        await verifyClaim('', null, []);
      } catch (error) {
        expect(error).toBeInstanceOf(APIError);
        expect((error as APIError).statusCode).toBe(400);
        expect((error as APIError).detail).toBe('Invalid request: missing required fields');
      }
    });

    it('should handle 500 Internal Server Error', async () => {
      const errorResponse = {
        response: {
          status: 500,
          data: {
            detail: 'Pipeline execution failed',
          },
        },
        isAxiosError: true,
      };

      mockAxiosInstance.post.mockRejectedValue(errorResponse);

      await expect(verifyClaim('Test claim', null, ['model1'])).rejects.toThrow(APIError);
      await expect(verifyClaim('Test claim', null, ['model1'])).rejects.toThrow(
        'API Error: Pipeline execution failed'
      );

      try {
        await verifyClaim('Test claim', null, ['model1']);
      } catch (error) {
        expect(error).toBeInstanceOf(APIError);
        expect((error as APIError).statusCode).toBe(500);
        expect((error as APIError).detail).toBe('Pipeline execution failed');
      }
    });

    it('should handle 404 Not Found error', async () => {
      const errorResponse = {
        response: {
          status: 404,
          data: {
            detail: 'Endpoint not found',
          },
        },
        isAxiosError: true,
      };

      mockAxiosInstance.post.mockRejectedValue(errorResponse);

      await expect(verifyClaim('Test claim', null, ['model1'])).rejects.toThrow(APIError);

      try {
        await verifyClaim('Test claim', null, ['model1']);
      } catch (error) {
        expect(error).toBeInstanceOf(APIError);
        expect((error as APIError).statusCode).toBe(404);
      }
    });

    it('should handle error response with "error" field instead of "detail"', async () => {
      const errorResponse = {
        response: {
          status: 400,
          data: {
            error: 'Validation error',
          },
        },
        isAxiosError: true,
      };

      mockAxiosInstance.post.mockRejectedValue(errorResponse);

      await expect(verifyClaim('Test claim', null, ['model1'])).rejects.toThrow(
        'API Error: Validation error'
      );
    });

    it('should handle error response with no detail or error field', async () => {
      const errorResponse = {
        response: {
          status: 500,
          data: {},
        },
        isAxiosError: true,
      };

      mockAxiosInstance.post.mockRejectedValue(errorResponse);

      await expect(verifyClaim('Test claim', null, ['model1'])).rejects.toThrow(
        'API Error: An error occurred'
      );
    });

    it('should handle network failure (no response)', async () => {
      const errorResponse = {
        request: {},
        isAxiosError: true,
      };

      mockAxiosInstance.post.mockRejectedValue(errorResponse);

      await expect(verifyClaim('Test claim', null, ['model1'])).rejects.toThrow(APIError);
      await expect(verifyClaim('Test claim', null, ['model1'])).rejects.toThrow(
        'No response from server. Please check your connection.'
      );

      try {
        await verifyClaim('Test claim', null, ['model1']);
      } catch (error) {
        expect(error).toBeInstanceOf(APIError);
        expect((error as APIError).statusCode).toBeUndefined();
        expect((error as APIError).detail).toBe('Network error');
      }
    });

    it('should handle request setup failure', async () => {
      const errorResponse = {
        message: 'Request configuration error',
        isAxiosError: true,
      };

      mockAxiosInstance.post.mockRejectedValue(errorResponse);

      await expect(verifyClaim('Test claim', null, ['model1'])).rejects.toThrow(APIError);
      await expect(verifyClaim('Test claim', null, ['model1'])).rejects.toThrow(
        'Failed to send request'
      );

      try {
        await verifyClaim('Test claim', null, ['model1']);
      } catch (error) {
        expect(error).toBeInstanceOf(APIError);
        expect((error as APIError).detail).toBe('Request configuration error');
      }
    });

    it('should handle non-axios errors', async () => {
      const genericError = new Error('Something went wrong');
      mockAxiosInstance.post.mockRejectedValue(genericError);

      await expect(verifyClaim('Test claim', null, ['model1'])).rejects.toThrow(APIError);
      await expect(verifyClaim('Test claim', null, ['model1'])).rejects.toThrow(
        'An unexpected error occurred'
      );
    });

    it('should handle timeout errors', async () => {
      const timeoutError = {
        code: 'ECONNABORTED',
        message: 'timeout of 120000ms exceeded',
        isAxiosError: true,
        request: {},
      };

      mockAxiosInstance.post.mockRejectedValue(timeoutError);

      await expect(verifyClaim('Test claim', null, ['model1'])).rejects.toThrow(
        'No response from server. Please check your connection.'
      );
    });
  });

  describe('getAvailableModels', () => {
    const mockModels: ModelInfo[] = [
      {
        id: 'gpt-4',
        name: 'GPT-4',
        provider: 'OpenAI',
        version: '1.0',
      },
      {
        id: 'claude-3',
        name: 'Claude 3',
        provider: 'Anthropic',
        version: '3.0',
      },
    ];

    it('should successfully fetch available models', async () => {
      mockAxiosInstance.get.mockResolvedValue({
        data: { models: mockModels },
      });

      const result = await getAvailableModels();

      expect(mockAxiosInstance.get).toHaveBeenCalledWith('/api/models');
      expect(result).toEqual(mockModels);
    });

    it('should return empty array when no models available', async () => {
      mockAxiosInstance.get.mockResolvedValue({
        data: { models: [] },
      });

      const result = await getAvailableModels();

      expect(result).toEqual([]);
    });

    it('should handle 500 error when fetching models', async () => {
      const errorResponse = {
        response: {
          status: 500,
          data: {
            detail: 'Failed to load models',
          },
        },
        isAxiosError: true,
      };

      mockAxiosInstance.get.mockRejectedValue(errorResponse);

      await expect(getAvailableModels()).rejects.toThrow(APIError);
      await expect(getAvailableModels()).rejects.toThrow('API Error: Failed to load models');
    });

    it('should handle network failure when fetching models', async () => {
      const errorResponse = {
        request: {},
        isAxiosError: true,
      };

      mockAxiosInstance.get.mockRejectedValue(errorResponse);

      await expect(getAvailableModels()).rejects.toThrow(
        'No response from server. Please check your connection.'
      );
    });

    it('should handle 404 error when endpoint not found', async () => {
      const errorResponse = {
        response: {
          status: 404,
          data: {
            detail: 'Models endpoint not found',
          },
        },
        isAxiosError: true,
      };

      mockAxiosInstance.get.mockRejectedValue(errorResponse);

      await expect(getAvailableModels()).rejects.toThrow(APIError);

      try {
        await getAvailableModels();
      } catch (error) {
        expect(error).toBeInstanceOf(APIError);
        expect((error as APIError).statusCode).toBe(404);
      }
    });
  });

  describe('checkHealth', () => {
    const mockHealthResponse: HealthResponse = {
      status: 'healthy',
      version: '1.0.0',
    };

    it('should successfully check health status', async () => {
      mockAxiosInstance.get.mockResolvedValue({
        data: mockHealthResponse,
      });

      const result = await checkHealth();

      expect(mockAxiosInstance.get).toHaveBeenCalledWith('/api/health');
      expect(result).toEqual(mockHealthResponse);
    });

    it('should handle unhealthy status', async () => {
      const unhealthyResponse = {
        status: 'unhealthy',
        version: '1.0.0',
      };

      mockAxiosInstance.get.mockResolvedValue({
        data: unhealthyResponse,
      });

      const result = await checkHealth();

      expect(result.status).toBe('unhealthy');
    });

    it('should handle 503 Service Unavailable error', async () => {
      const errorResponse = {
        response: {
          status: 503,
          data: {
            detail: 'Service temporarily unavailable',
          },
        },
        isAxiosError: true,
      };

      mockAxiosInstance.get.mockRejectedValue(errorResponse);

      await expect(checkHealth()).rejects.toThrow(APIError);
      await expect(checkHealth()).rejects.toThrow(
        'API Error: Service temporarily unavailable'
      );

      try {
        await checkHealth();
      } catch (error) {
        expect(error).toBeInstanceOf(APIError);
        expect((error as APIError).statusCode).toBe(503);
      }
    });

    it('should handle network failure when checking health', async () => {
      const errorResponse = {
        request: {},
        isAxiosError: true,
      };

      mockAxiosInstance.get.mockRejectedValue(errorResponse);

      await expect(checkHealth()).rejects.toThrow(
        'No response from server. Please check your connection.'
      );
    });
  });

  describe('APIError class', () => {
    it('should create APIError with all parameters', () => {
      const error = new APIError('Test error', 400, 'Detailed message');

      expect(error).toBeInstanceOf(Error);
      expect(error).toBeInstanceOf(APIError);
      expect(error.message).toBe('Test error');
      expect(error.statusCode).toBe(400);
      expect(error.detail).toBe('Detailed message');
      expect(error.name).toBe('APIError');
    });

    it('should create APIError with only message', () => {
      const error = new APIError('Test error');

      expect(error.message).toBe('Test error');
      expect(error.statusCode).toBeUndefined();
      expect(error.detail).toBeUndefined();
    });

    it('should be throwable and catchable', () => {
      expect(() => {
        throw new APIError('Test error', 500);
      }).toThrow(APIError);

      try {
        throw new APIError('Test error', 500, 'Details');
      } catch (error) {
        expect(error).toBeInstanceOf(APIError);
        expect((error as APIError).statusCode).toBe(500);
      }
    });
  });

  describe('Error handling edge cases', () => {
    it('should handle null error response data', async () => {
      const errorResponse = {
        response: {
          status: 500,
          data: null,
        },
        isAxiosError: true,
      };

      mockAxiosInstance.post.mockRejectedValue(errorResponse);

      await expect(verifyClaim('Test claim', null, ['model1'])).rejects.toThrow(
        'API Error: An error occurred'
      );
    });

    it('should handle undefined error response data', async () => {
      const errorResponse = {
        response: {
          status: 500,
          data: undefined,
        },
        isAxiosError: true,
      };

      mockAxiosInstance.post.mockRejectedValue(errorResponse);

      await expect(verifyClaim('Test claim', null, ['model1'])).rejects.toThrow(
        'API Error: An error occurred'
      );
    });

    it('should handle string error response', async () => {
      const errorResponse = 'Network error occurred';
      mockAxiosInstance.post.mockRejectedValue(errorResponse);

      await expect(verifyClaim('Test claim', null, ['model1'])).rejects.toThrow(
        'An unexpected error occurred'
      );
    });

    it('should handle error with both request and response', async () => {
      // When both exist, response takes precedence
      const errorResponse = {
        response: {
          status: 400,
          data: {
            detail: 'Bad request',
          },
        },
        request: {},
        isAxiosError: true,
      };

      mockAxiosInstance.post.mockRejectedValue(errorResponse);

      await expect(verifyClaim('Test claim', null, ['model1'])).rejects.toThrow(
        'API Error: Bad request'
      );
    });
  });

  describe('Request payload construction', () => {
    it('should not include text field when text is undefined', async () => {
      mockAxiosInstance.post.mockResolvedValue({
        data: {} as VerificationResponse,
      });

      await verifyClaim(undefined, 'base64image', ['model1']);

      expect(mockAxiosInstance.post).toHaveBeenCalledWith('/api/verify', {
        image: 'base64image',
        selected_models: ['model1'],
      });

      const callArgs = mockAxiosInstance.post.mock.calls[0][1];
      expect(callArgs).not.toHaveProperty('text');
    });

    it('should not include image field when image is null', async () => {
      mockAxiosInstance.post.mockResolvedValue({
        data: {} as VerificationResponse,
      });

      await verifyClaim('Test claim', null, ['model1']);

      expect(mockAxiosInstance.post).toHaveBeenCalledWith('/api/verify', {
        text: 'Test claim',
        selected_models: ['model1'],
      });

      const callArgs = mockAxiosInstance.post.mock.calls[0][1];
      expect(callArgs).not.toHaveProperty('image');
    });

    it('should include both text and image when both provided', async () => {
      mockAxiosInstance.post.mockResolvedValue({
        data: {} as VerificationResponse,
      });

      await verifyClaim('Test claim', 'base64image', ['model1']);

      const callArgs = mockAxiosInstance.post.mock.calls[0][1];
      expect(callArgs).toHaveProperty('text', 'Test claim');
      expect(callArgs).toHaveProperty('image', 'base64image');
      expect(callArgs).toHaveProperty('selected_models', ['model1']);
    });
  });
});
