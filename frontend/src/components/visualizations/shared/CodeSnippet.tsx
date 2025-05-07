'use client';

import React, { useState } from 'react';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { 
  vscDarkPlus, 
  vs 
} from 'react-syntax-highlighter/dist/esm/styles/prism';
import { 
  ClipboardIcon, 
  ClipboardDocumentCheckIcon,
  ChevronDownIcon,
  ChevronUpIcon
} from '@heroicons/react/24/outline';

interface CodeSnippetProps {
  code: string;
  language?: string;
  fileName?: string;
  showLineNumbers?: boolean;
  highlightedLines?: number[];
  maxHeight?: string;
  darkMode?: boolean;
  className?: string;
}

/**
 * A component for displaying code snippets with syntax highlighting
 */
export default function CodeSnippet({
  code,
  language = 'javascript',
  fileName,
  showLineNumbers = true,
  highlightedLines = [],
  maxHeight = '400px',
  darkMode = true,
  className = '',
}: CodeSnippetProps) {
  const [copied, setCopied] = useState(false);
  const [collapsed, setCollapsed] = useState(false);

  // Handle copy to clipboard
  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(code);
      setCopied(true);
      
      // Reset copied state after 2 seconds
      setTimeout(() => {
        setCopied(false);
      }, 2000);
    } catch (err) {
      console.error('Failed to copy code:', err);
    }
  };

  // Get style based on dark mode
  const codeStyle = darkMode ? vscDarkPlus : vs;

  // Create line highlighting props
  const lineProps = (lineNumber: number) => {
    const style: React.CSSProperties = {};
    if (highlightedLines.includes(lineNumber)) {
      style.backgroundColor = darkMode 
        ? 'rgba(255, 255, 255, 0.1)' 
        : 'rgba(0, 0, 0, 0.05)';
      style.display = 'block';
      style.width = '100%';
    }
    return { style };
  };

  return (
    <div className={`rounded-lg overflow-hidden border ${darkMode ? 'border-gray-700' : 'border-gray-300'} ${className}`}>
      {/* Header with filename and actions */}
      <div className={`flex items-center justify-between px-4 py-2 ${darkMode ? 'bg-gray-800 text-gray-200' : 'bg-gray-100 text-gray-700'}`}>
        <div className="flex items-center">
          {fileName && (
            <span className="text-sm font-mono mr-2">{fileName}</span>
          )}
          <span className="text-xs px-2 py-1 rounded-md bg-opacity-20 uppercase font-semibold tracking-wider bg-blue-500 text-blue-700 dark:text-blue-300">
            {language}
          </span>
        </div>
        <div className="flex items-center space-x-2">
          <button
            onClick={handleCopy}
            className={`p-1.5 rounded-md ${darkMode ? 'hover:bg-gray-700' : 'hover:bg-gray-200'} transition-colors`}
            title={copied ? 'Copied!' : 'Copy to clipboard'}
          >
            {copied ? (
              <ClipboardDocumentCheckIcon className="h-4 w-4 text-green-500" />
            ) : (
              <ClipboardIcon className="h-4 w-4" />
            )}
          </button>
          <button
            onClick={() => setCollapsed(!collapsed)}
            className={`p-1.5 rounded-md ${darkMode ? 'hover:bg-gray-700' : 'hover:bg-gray-200'} transition-colors`}
            title={collapsed ? 'Expand' : 'Collapse'}
          >
            {collapsed ? (
              <ChevronDownIcon className="h-4 w-4" />
            ) : (
              <ChevronUpIcon className="h-4 w-4" />
            )}
          </button>
        </div>
      </div>

      {/* Code content */}
      {!collapsed && (
        <div style={{ maxHeight, overflow: 'auto' }}>
          <SyntaxHighlighter
            language={language}
            style={codeStyle}
            showLineNumbers={showLineNumbers}
            wrapLines={true}
            lineProps={lineProps}
            customStyle={{
              margin: 0,
              borderRadius: 0,
              fontSize: '0.9rem',
            }}
          >
            {code}
          </SyntaxHighlighter>
        </div>
      )}
    </div>
  );
}
