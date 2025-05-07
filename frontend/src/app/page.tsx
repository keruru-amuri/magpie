'use client';

import React from 'react';
import { ChatBubbleLeftRightIcon, DocumentTextIcon, WrenchScrewdriverIcon, ClipboardDocumentCheckIcon } from '@heroicons/react/24/outline';
import Layout from '../components/layout/Layout';
import ChatInterface from '../components/chat/ChatInterface';
import Card from '../components/common/Card';

export default function Home() {
  // Force scroll to top on component mount and prevent auto-scrolling
  React.useEffect(() => {
    // Store original scroll position
    const originalScrollPosition = window.scrollY;

    // Function to force scroll to top
    const forceScrollTop = () => {
      if (window.scrollY !== 0) {
        window.scrollTo(0, 0);
      }
    };

    // Apply immediately
    forceScrollTop();

    // Apply multiple times to catch any layout shifts
    const intervals = [10, 50, 100, 200, 500, 1000];
    const timers = intervals.map(delay => setTimeout(forceScrollTop, delay));

    // Also add a scroll event listener to prevent scrolling for the first second
    const handleScroll = () => {
      if (Date.now() - mountTime < 1000) {
        window.scrollTo(0, 0);
      }
    };

    const mountTime = Date.now();
    window.addEventListener('scroll', handleScroll);

    return () => {
      // Clean up all timers
      timers.forEach(timer => clearTimeout(timer));
      window.removeEventListener('scroll', handleScroll);
    };
  }, []);

  return (
    <Layout>
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Hero Section */}
        <div className="text-center mb-8">
          <h1 className="text-4xl font-bold text-gray-900 dark:text-white sm:text-5xl md:text-6xl">
            <span className="block">MAGPIE Platform</span>
            <span className="block text-primary-600 dark:text-primary-500">Intelligent Aircraft Maintenance</span>
          </h1>
          <p className="mt-3 max-w-md mx-auto text-base text-gray-500 dark:text-gray-400 sm:text-lg md:mt-5 md:text-xl md:max-w-3xl">
            MAG Platform for Intelligent Execution - Enhancing aircraft maintenance, repair, and overhaul operations with AI-powered assistance.
          </p>

          {/* Test Navigation */}
          <div className="mt-6 flex justify-center space-x-4">
            <a
              href="/test-visualizations"
              className="inline-flex items-center px-4 py-2 border border-transparent text-base font-medium rounded-md shadow-sm text-white bg-primary-600 hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500"
            >
              Test Visualizations
            </a>
            <a
              href="/test-history"
              className="inline-flex items-center px-4 py-2 border border-transparent text-base font-medium rounded-md shadow-sm text-white bg-secondary-600 hover:bg-secondary-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-secondary-500"
            >
              Test Conversation History
            </a>
          </div>
        </div>

        {/* Main Content */}
        <div className="mb-8">
          {/* Chat Interface */}
          <div className="h-[600px]">
            <ChatInterface />
          </div>
        </div>

        {/* How It Works Section */}
        <div className="mb-12">
          <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-6 text-center">How MAGPIE Works</h2>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            <div className="bg-white dark:bg-gray-800 p-6 rounded-lg shadow-md border border-gray-200 dark:border-gray-700">
              <div className="flex flex-col items-center text-center mb-4">
                <div className="h-16 w-16 rounded-full bg-primary-100 dark:bg-primary-900 flex items-center justify-center text-primary-600 dark:text-primary-300 mb-4">
                  <span className="text-2xl font-bold">1</span>
                </div>
                <h3 className="text-lg font-semibold text-gray-900 dark:text-white">Ask Your Question</h3>
              </div>
              <p className="text-gray-600 dark:text-gray-400 text-center">
                Simply type your aircraft maintenance question in natural language. No need to select which agent to use.
              </p>
            </div>

            <div className="bg-white dark:bg-gray-800 p-6 rounded-lg shadow-md border border-gray-200 dark:border-gray-700">
              <div className="flex flex-col items-center text-center mb-4">
                <div className="h-16 w-16 rounded-full bg-primary-100 dark:bg-primary-900 flex items-center justify-center text-primary-600 dark:text-primary-300 mb-4">
                  <span className="text-2xl font-bold">2</span>
                </div>
                <h3 className="text-lg font-semibold text-gray-900 dark:text-white">Intelligent Routing</h3>
              </div>
              <p className="text-gray-600 dark:text-gray-400 text-center">
                Our orchestrator analyzes your query and automatically routes it to the most appropriate specialized agent.
              </p>
            </div>

            <div className="bg-white dark:bg-gray-800 p-6 rounded-lg shadow-md border border-gray-200 dark:border-gray-700">
              <div className="flex flex-col items-center text-center mb-4">
                <div className="h-16 w-16 rounded-full bg-primary-100 dark:bg-primary-900 flex items-center justify-center text-primary-600 dark:text-primary-300 mb-4">
                  <span className="text-2xl font-bold">3</span>
                </div>
                <h3 className="text-lg font-semibold text-gray-900 dark:text-white">Dynamic Context</h3>
              </div>
              <p className="text-gray-600 dark:text-gray-400 text-center">
                Relevant context panels appear automatically based on your query type, providing specialized tools and information.
              </p>
            </div>
          </div>
        </div>

        {/* Features Section */}
        <div>
          <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-6">Platform Features</h2>

          <div className="grid grid-cols-1 gap-8 sm:grid-cols-2 lg:grid-cols-3">
            <div className="bg-white dark:bg-gray-800 shadow-sm rounded-lg p-6 border border-gray-200 dark:border-gray-700">
              <div className="flex items-center mb-4">
                <div className="h-10 w-10 rounded-md bg-blue-100 dark:bg-blue-900 flex items-center justify-center text-blue-600 dark:text-blue-300 mr-3">
                  <DocumentTextIcon className="h-6 w-6" />
                </div>
                <h3 className="text-lg font-medium text-gray-900 dark:text-white">Comprehensive Documentation</h3>
              </div>
              <p className="text-gray-600 dark:text-gray-400">
                Access and search through all technical documentation with intelligent cross-referencing and context-aware results.
              </p>
            </div>

            <div className="bg-white dark:bg-gray-800 shadow-sm rounded-lg p-6 border border-gray-200 dark:border-gray-700">
              <div className="flex items-center mb-4">
                <div className="h-10 w-10 rounded-md bg-amber-100 dark:bg-amber-900 flex items-center justify-center text-amber-600 dark:text-amber-300 mr-3">
                  <WrenchScrewdriverIcon className="h-6 w-6" />
                </div>
                <h3 className="text-lg font-medium text-gray-900 dark:text-white">Intelligent Troubleshooting</h3>
              </div>
              <p className="text-gray-600 dark:text-gray-400">
                Get step-by-step guidance for diagnosing and resolving issues with aircraft systems and components.
              </p>
            </div>

            <div className="bg-white dark:bg-gray-800 shadow-sm rounded-lg p-6 border border-gray-200 dark:border-gray-700">
              <div className="flex items-center mb-4">
                <div className="h-10 w-10 rounded-md bg-green-100 dark:bg-green-900 flex items-center justify-center text-green-600 dark:text-green-300 mr-3">
                  <ClipboardDocumentCheckIcon className="h-6 w-6" />
                </div>
                <h3 className="text-lg font-medium text-gray-900 dark:text-white">Procedure Generation</h3>
              </div>
              <p className="text-gray-600 dark:text-gray-400">
                Generate customized maintenance procedures with safety precautions, required tools, and step-by-step instructions.
              </p>
            </div>
          </div>
        </div>
      </div>
    </Layout>
  );
}
