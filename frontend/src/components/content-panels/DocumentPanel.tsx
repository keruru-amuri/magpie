'use client';

import React, { useState } from 'react';
import { DocumentTextIcon, DocumentDuplicateIcon, MagnifyingGlassIcon } from '@heroicons/react/24/outline';
import { ChevronRightIcon } from '@heroicons/react/24/solid';

interface Document {
  id: string;
  title: string;
  type: 'manual' | 'guide' | 'reference';
  sections: DocumentSection[];
}

interface DocumentSection {
  id: string;
  title: string;
  content?: string;
  subsections?: DocumentSection[];
}

interface DocumentPanelProps {
  documents?: Document[];
  activeDocumentId?: string;
  onDocumentSelect?: (documentId: string) => void;
  onSectionSelect?: (documentId: string, sectionId: string) => void;
  className?: string;
}

export default function DocumentPanel({
  documents = [],
  activeDocumentId,
  onDocumentSelect,
  onSectionSelect,
  className = '',
}: DocumentPanelProps) {
  const [searchQuery, setSearchQuery] = useState('');

  // Mock documents if none provided
  const displayDocuments = documents.length > 0 ? documents : [
    {
      id: 'aircraft-manual-1',
      title: 'Boeing 737 MAX Maintenance Manual',
      type: 'manual',
      sections: [
        {
          id: 'section-1',
          title: 'General Information',
          subsections: [
            { id: 'subsection-1-1', title: 'Aircraft Specifications', content: 'Detailed specifications of the Boeing 737 MAX aircraft...' },
            { id: 'subsection-1-2', title: 'System Overview', content: 'Overview of major aircraft systems...' },
          ]
        },
        {
          id: 'section-2',
          title: 'Maintenance Procedures',
          subsections: [
            { id: 'subsection-2-1', title: 'Routine Inspections', content: 'Procedures for routine maintenance inspections...' },
            { id: 'subsection-2-2', title: 'Component Replacement', content: 'Guidelines for replacing aircraft components...' },
          ]
        },
      ]
    },
    {
      id: 'troubleshooting-guide-1',
      title: 'Avionics Troubleshooting Guide',
      type: 'guide',
      sections: [
        {
          id: 'section-1',
          title: 'Navigation Systems',
          subsections: [
            { id: 'subsection-1-1', title: 'GPS Issues', content: 'Troubleshooting common GPS system issues...' },
            { id: 'subsection-1-2', title: 'Radar Calibration', content: 'Procedures for radar system calibration...' },
          ]
        },
      ]
    },
  ];

  // Filter documents based on search query
  const filteredDocuments = searchQuery.trim() === ''
    ? displayDocuments
    : displayDocuments.filter(doc =>
        doc.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
        doc.sections.some(section =>
          section.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
          section.subsections?.some(subsection =>
            subsection.title.toLowerCase().includes(searchQuery.toLowerCase())
          )
        )
      );

  // Track open sections
  const [openSections, setOpenSections] = useState<Record<string, boolean>>({});

  // Toggle section open/closed
  const toggleSection = (sectionId: string) => {
    setOpenSections(prev => ({
      ...prev,
      [sectionId]: !prev[sectionId]
    }));
  };

  // Render document tree
  const renderSections = (sections: DocumentSection[], documentId: string, level = 0) => {
    return sections.map(section => (
      <div key={section.id} className={`ml-${level * 4}`}>
        {section.subsections && section.subsections.length > 0 ? (
          <div>
            <button
              onClick={() => toggleSection(section.id)}
              className="flex w-full items-center justify-between py-2 text-left text-sm font-medium hover:bg-gray-100 dark:hover:bg-gray-800 rounded px-2"
            >
              <span>{section.title}</span>
              <ChevronRightIcon
                className={`${
                  openSections[section.id] ? 'transform rotate-90' : ''
                } h-4 w-4 text-gray-500 transition-transform duration-200`}
              />
            </button>

            {openSections[section.id] && (
              <div className="pl-4 pt-1 pb-2 transition-all duration-200">
                {section.subsections && renderSections(section.subsections, documentId, level + 1)}
              </div>
            )}
          </div>
        ) : (
          <button
            className="w-full text-left py-2 px-2 text-sm hover:bg-gray-100 dark:hover:bg-gray-800 rounded"
            onClick={() => onSectionSelect && onSectionSelect(documentId, section.id)}
          >
            {section.title}
          </button>
        )}
      </div>
    ));
  };

  return (
    <div className={`bg-white dark:bg-gray-900 rounded-lg shadow-md border border-gray-200 dark:border-gray-700 overflow-hidden ${className}`}>
      <div className="p-4 border-b border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-800">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white flex items-center">
          <DocumentTextIcon className="h-5 w-5 mr-2 text-blue-500" />
          Technical Documentation
        </h3>
        <div className="mt-2 relative">
          <input
            type="text"
            placeholder="Search documentation..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full pl-10 pr-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent dark:bg-gray-800 dark:text-white"
          />
          <MagnifyingGlassIcon className="absolute left-3 top-2.5 h-5 w-5 text-gray-400" />
        </div>
      </div>

      <div className="p-4 max-h-[500px] overflow-y-auto">
        {filteredDocuments.length === 0 ? (
          <div className="text-center py-8 text-gray-500 dark:text-gray-400">
            No documents found matching your search.
          </div>
        ) : (
          <div className="space-y-4">
            {filteredDocuments.map(document => (
              <div key={document.id} className="border border-gray-200 dark:border-gray-700 rounded-lg overflow-hidden">
                <button
                  className={`w-full flex items-center justify-between p-3 text-left ${
                    activeDocumentId === document.id
                      ? 'bg-primary-50 dark:bg-primary-900/20 text-primary-700 dark:text-primary-300'
                      : 'bg-white dark:bg-gray-800 hover:bg-gray-50 dark:hover:bg-gray-750'
                  }`}
                  onClick={() => onDocumentSelect && onDocumentSelect(document.id)}
                >
                  <div className="flex items-center">
                    <DocumentDuplicateIcon className="h-5 w-5 mr-2 text-gray-500 dark:text-gray-400" />
                    <span className="font-medium">{document.title}</span>
                  </div>
                  <span className="text-xs px-2 py-1 rounded-full bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-300">
                    {document.type}
                  </span>
                </button>

                {activeDocumentId === document.id && (
                  <div className="p-3 border-t border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-850">
                    {renderSections(document.sections, document.id)}
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
