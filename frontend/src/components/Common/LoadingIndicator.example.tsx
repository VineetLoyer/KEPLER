/**
 * LoadingIndicator Usage Examples
 * 
 * This file demonstrates how to use the LoadingIndicator component
 * in different scenarios.
 */

import React, { useState, useEffect } from 'react';
import { LoadingIndicator, type VerificationStage } from './LoadingIndicator';

/**
 * Example 1: Basic usage with default stage
 */
export const BasicExample: React.FC = () => {
  return (
    <div>
      <h2>Basic Loading Indicator</h2>
      <LoadingIndicator />
    </div>
  );
};

/**
 * Example 2: With specific stage
 */
export const StageExample: React.FC = () => {
  return (
    <div>
      <h2>Loading with Specific Stage</h2>
      <LoadingIndicator currentStage="verifying" />
    </div>
  );
};

/**
 * Example 3: Simulating stage progression
 */
export const ProgressionExample: React.FC = () => {
  const stages: VerificationStage[] = [
    'initializing',
    'decomposing',
    'retrieving',
    'reranking',
    'verifying',
    'aggregating',
    'scoring',
    'finalizing',
  ];

  const [currentStageIndex, setCurrentStageIndex] = useState(0);

  useEffect(() => {
    const interval = setInterval(() => {
      setCurrentStageIndex((prev) => {
        if (prev < stages.length - 1) {
          return prev + 1;
        }
        return 0; // Loop back to start
      });
    }, 2000); // Change stage every 2 seconds

    return () => clearInterval(interval);
  }, []);

  return (
    <div>
      <h2>Stage Progression Demo</h2>
      <LoadingIndicator currentStage={stages[currentStageIndex]} />
    </div>
  );
};

/**
 * Example 4: In a verification workflow
 */
export const WorkflowExample: React.FC = () => {
  const [isLoading, setIsLoading] = useState(false);
  const [stage, setStage] = useState<VerificationStage>('initializing');

  const startVerification = async () => {
    setIsLoading(true);
    
    // Simulate verification stages
    const stages: VerificationStage[] = [
      'initializing',
      'decomposing',
      'retrieving',
      'reranking',
      'verifying',
      'aggregating',
      'scoring',
      'finalizing',
    ];

    for (const currentStage of stages) {
      setStage(currentStage);
      await new Promise(resolve => setTimeout(resolve, 1500));
    }

    setIsLoading(false);
  };

  return (
    <div>
      <h2>Verification Workflow</h2>
      {!isLoading ? (
        <button onClick={startVerification}>
          Start Verification
        </button>
      ) : (
        <LoadingIndicator currentStage={stage} />
      )}
    </div>
  );
};

export default {
  BasicExample,
  StageExample,
  ProgressionExample,
  WorkflowExample,
};
