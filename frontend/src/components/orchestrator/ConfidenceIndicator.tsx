'use client';

import React, { useState } from 'react';
import { useOrchestrator } from './OrchestratorContext';

interface ConfidenceIndicatorProps {
  confidence: number;
  size?: 'sm' | 'md' | 'lg';
  showPercentage?: boolean;
  showTooltip?: boolean;
  className?: string;
  label?: string;
  thresholds?: {
    low: number;
    medium: number;
    high: number;
  };
}

/**
 * Component to visualize agent confidence level
 */
export default function ConfidenceIndicator({
  confidence,
  size = 'md',
  showPercentage = false,
  showTooltip: initialShowTooltip = true,
  className = '',
  label = 'Confidence',
  thresholds,
}: ConfidenceIndicatorProps) {
  const [showTooltip, setShowTooltip] = useState(false);
  const { confidenceThresholds } = useOrchestrator();

  // Use provided thresholds or default to the ones from OrchestratorContext
  const effectiveThresholds = thresholds || {
    low: confidenceThresholds.minimum,
    medium: confidenceThresholds.transition,
    high: confidenceThresholds.high
  };

  // Determine color based on confidence level
  const getColorClasses = () => {
    if (confidence >= effectiveThresholds.high) {
      return 'bg-green-500 dark:bg-green-600';
    } else if (confidence >= effectiveThresholds.medium) {
      return 'bg-yellow-500 dark:bg-yellow-600';
    } else if (confidence >= effectiveThresholds.low) {
      return 'bg-orange-500 dark:bg-orange-600';
    } else {
      return 'bg-red-500 dark:bg-red-600';
    }
  };

  // Determine size classes
  const getSizeClasses = () => {
    switch (size) {
      case 'sm':
        return 'h-1.5 w-16';
      case 'lg':
        return 'h-3 w-32';
      case 'md':
      default:
        return 'h-2 w-24';
    }
  };

  // Calculate width percentage
  const widthPercentage = Math.round(confidence * 100);

  // Format confidence for display
  const formattedConfidence = `${widthPercentage}%`;

  // Get confidence level description
  const getConfidenceLevel = () => {
    if (confidence >= effectiveThresholds.high) return 'High';
    if (confidence >= effectiveThresholds.medium) return 'Medium';
    if (confidence >= effectiveThresholds.low) return 'Low';
    return 'Very Low';
  };

  return (
    <div
      className={`inline-flex items-center relative ${className}`}
      onMouseEnter={() => initialShowTooltip && setShowTooltip(true)}
      onMouseLeave={() => initialShowTooltip && setShowTooltip(false)}
    >
      <div
        className={`relative rounded-full bg-gray-200 dark:bg-gray-700 overflow-hidden ${getSizeClasses()}`}
        role="progressbar"
        aria-valuenow={widthPercentage}
        aria-valuemin={0}
        aria-valuemax={100}
        aria-label={`${label}: ${formattedConfidence}`}
      >
        <div
          className={`absolute left-0 top-0 bottom-0 ${getColorClasses()}`}
          style={{ width: formattedConfidence }}
        ></div>
      </div>
      {showPercentage && (
        <span className="ml-2 text-xs text-gray-600 dark:text-gray-400">
          {formattedConfidence}
        </span>
      )}

      {showTooltip && (
        <div className="absolute bottom-full mb-1 left-1/2 transform -translate-x-1/2 z-10 px-2 py-1 text-xs font-medium text-white bg-gray-900 rounded-md shadow-sm whitespace-nowrap">
          {label}: {formattedConfidence} ({getConfidenceLevel()})
        </div>
      )}
    </div>
  );
}
