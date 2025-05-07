'use client';

import React, { useState } from 'react';
import { 
  ChevronRightIcon, 
  ChevronDownIcon,
  DocumentTextIcon,
  FolderIcon,
  FolderOpenIcon,
  MagnifyingGlassIcon,
  XMarkIcon
} from '@heroicons/react/24/outline';

// Define document node types
export type DocumentNodeType = 'folder' | 'document' | 'section';

// Define document node
export interface DocumentNode {
  id: string;
  name: string;
  type: DocumentNodeType;
  children?: DocumentNode[];
  content?: string;
  metadata?: Record<string, any>;
}

interface DocumentTreeProps {
  data: DocumentNode[];
  onSelectNode?: (node: DocumentNode) => void;
  selectedNodeId?: string;
  searchTerm?: string;
  onSearch?: (term: string) => void;
  className?: string;
}

/**
 * A component for displaying a hierarchical document tree
 */
export default function DocumentTree({
  data,
  onSelectNode,
  selectedNodeId,
  searchTerm: externalSearchTerm,
  onSearch,
  className = '',
}: DocumentTreeProps) {
  const [expandedNodes, setExpandedNodes] = useState<Record<string, boolean>>({});
  const [internalSearchTerm, setInternalSearchTerm] = useState('');
  
  // Use external search term if provided, otherwise use internal
  const searchTerm = externalSearchTerm !== undefined ? externalSearchTerm : internalSearchTerm;
  
  // Toggle node expansion
  const toggleNode = (nodeId: string) => {
    setExpandedNodes((prev) => ({
      ...prev,
      [nodeId]: !prev[nodeId],
    }));
  };
  
  // Handle node selection
  const handleSelectNode = (node: DocumentNode) => {
    if (onSelectNode) {
      onSelectNode(node);
    }
  };
  
  // Handle search input change
  const handleSearchChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = e.target.value;
    setInternalSearchTerm(value);
    
    if (onSearch) {
      onSearch(value);
    }
  };
  
  // Clear search
  const clearSearch = () => {
    setInternalSearchTerm('');
    
    if (onSearch) {
      onSearch('');
    }
  };
  
  // Check if node or its children match search term
  const nodeMatchesSearch = (node: DocumentNode, term: string): boolean => {
    if (!term) return true;
    
    const normalizedTerm = term.toLowerCase();
    
    // Check if node name matches
    if (node.name.toLowerCase().includes(normalizedTerm)) {
      return true;
    }
    
    // Check if node content matches
    if (node.content && node.content.toLowerCase().includes(normalizedTerm)) {
      return true;
    }
    
    // Check if any children match
    if (node.children) {
      return node.children.some((child) => nodeMatchesSearch(child, term));
    }
    
    return false;
  };
  
  // Expand nodes that match search term
  const expandMatchingNodes = (nodes: DocumentNode[], term: string): Record<string, boolean> => {
    const expanded: Record<string, boolean> = {};
    
    const traverse = (node: DocumentNode) => {
      if (nodeMatchesSearch(node, term)) {
        if (node.children && node.children.length > 0) {
          expanded[node.id] = true;
          node.children.forEach(traverse);
        }
      }
    };
    
    nodes.forEach(traverse);
    
    return expanded;
  };
  
  // Update expanded nodes when search term changes
  React.useEffect(() => {
    if (searchTerm) {
      const newExpandedNodes = expandMatchingNodes(data, searchTerm);
      setExpandedNodes((prev) => ({
        ...prev,
        ...newExpandedNodes,
      }));
    }
  }, [searchTerm, data]);
  
  // Render a document node
  const renderNode = (node: DocumentNode, level = 0) => {
    // Skip nodes that don't match search term
    if (searchTerm && !nodeMatchesSearch(node, searchTerm)) {
      return null;
    }
    
    const isExpanded = expandedNodes[node.id] || false;
    const isSelected = node.id === selectedNodeId;
    const hasChildren = node.children && node.children.length > 0;
    
    // Determine icon based on node type and state
    const getNodeIcon = () => {
      switch (node.type) {
        case 'folder':
          return isExpanded ? (
            <FolderOpenIcon className="h-5 w-5 text-amber-500" />
          ) : (
            <FolderIcon className="h-5 w-5 text-amber-500" />
          );
        case 'document':
          return <DocumentTextIcon className="h-5 w-5 text-blue-500" />;
        case 'section':
          return (
            <svg className="h-5 w-5 text-gray-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 8h10M7 12h10M7 16h10" />
            </svg>
          );
        default:
          return <DocumentTextIcon className="h-5 w-5 text-gray-500" />;
      }
    };
    
    // Highlight matching text in node name
    const highlightMatchingText = (text: string, term: string) => {
      if (!term) return text;
      
      const normalizedTerm = term.toLowerCase();
      const normalizedText = text.toLowerCase();
      const index = normalizedText.indexOf(normalizedTerm);
      
      if (index === -1) return text;
      
      const before = text.substring(0, index);
      const match = text.substring(index, index + term.length);
      const after = text.substring(index + term.length);
      
      return (
        <>
          {before}
          <span className="bg-yellow-200 dark:bg-yellow-800">{match}</span>
          {after}
        </>
      );
    };
    
    return (
      <div key={node.id}>
        <div
          className={`flex items-center py-1 px-2 rounded-md cursor-pointer ${
            isSelected
              ? 'bg-blue-100 dark:bg-blue-900/50 text-blue-800 dark:text-blue-200'
              : 'hover:bg-gray-100 dark:hover:bg-gray-800'
          }`}
          style={{ paddingLeft: `${level * 16 + 8}px` }}
          onClick={() => handleSelectNode(node)}
        >
          {hasChildren && (
            <button
              onClick={(e) => {
                e.stopPropagation();
                toggleNode(node.id);
              }}
              className="mr-1 p-1 rounded-md hover:bg-gray-200 dark:hover:bg-gray-700"
            >
              {isExpanded ? (
                <ChevronDownIcon className="h-4 w-4" />
              ) : (
                <ChevronRightIcon className="h-4 w-4" />
              )}
            </button>
          )}
          
          {!hasChildren && <div className="w-6" />}
          
          <div className="mr-2">{getNodeIcon()}</div>
          
          <div className="truncate">
            {searchTerm ? highlightMatchingText(node.name, searchTerm) : node.name}
          </div>
        </div>
        
        {hasChildren && isExpanded && (
          <div>
            {node.children!.map((child) => renderNode(child, level + 1))}
          </div>
        )}
      </div>
    );
  };

  return (
    <div className={`border border-gray-200 dark:border-gray-700 rounded-lg overflow-hidden ${className}`}>
      {/* Search bar */}
      <div className="p-2 border-b border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800">
        <div className="relative">
          <input
            type="text"
            placeholder="Search documentation..."
            value={searchTerm}
            onChange={handleSearchChange}
            className="w-full px-3 py-2 pl-10 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm placeholder-gray-400 dark:placeholder-gray-500 dark:bg-gray-700 dark:text-white focus:outline-none focus:ring-primary-500 focus:border-primary-500 text-sm"
          />
          <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
            <MagnifyingGlassIcon className="h-5 w-5 text-gray-400" />
          </div>
          {searchTerm && (
            <button
              onClick={clearSearch}
              className="absolute inset-y-0 right-0 pr-3 flex items-center"
            >
              <XMarkIcon className="h-5 w-5 text-gray-400 hover:text-gray-500" />
            </button>
          )}
        </div>
      </div>
      
      {/* Tree content */}
      <div className="bg-white dark:bg-gray-900 overflow-y-auto max-h-[500px] p-2">
        {data.length === 0 ? (
          <div className="p-4 text-center text-gray-500 dark:text-gray-400">
            No documentation available
          </div>
        ) : (
          <div>{data.map((node) => renderNode(node))}</div>
        )}
      </div>
    </div>
  );
}
