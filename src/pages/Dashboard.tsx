import { Link } from 'react-router-dom';

import Card, { CardBody } from '../components/ui/Card';

const Dashboard = () => {
  return (
    <div className="space-y-8">
      <div className="text-center mb-12">
        <h1 className="text-4xl font-bold text-gray-900 dark:text-white mb-4">
          Welcome to MAGPIE Platform
        </h1>
        <p className="text-xl text-gray-600 dark:text-gray-400 max-w-3xl mx-auto">
          MAG Platform for Intelligent Execution - Enhancing aircraft maintenance with AI
          capabilities.
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <Link to="/documentation" className="block">
          <Card className="h-full transition-transform hover:scale-105">
            <CardBody>
              <div className="flex flex-col items-center text-center">
                <div className="w-16 h-16 bg-primary-100 dark:bg-primary-900 rounded-full flex items-center justify-center mb-4">
                  <svg
                    xmlns="http://www.w3.org/2000/svg"
                    className="h-8 w-8 text-primary-600 dark:text-primary-400"
                    fill="none"
                    viewBox="0 0 24 24"
                    stroke="currentColor"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
                    />
                  </svg>
                </div>
                <h2 className="text-xl font-bold text-gray-900 dark:text-white mb-2">
                  Technical Documentation Assistant
                </h2>
                <p className="text-gray-600 dark:text-gray-400">
                  Access, search, and understand technical aircraft documentation with AI-powered
                  assistance.
                </p>
              </div>
            </CardBody>
          </Card>
        </Link>

        <Link to="/troubleshooting" className="block">
          <Card className="h-full transition-transform hover:scale-105">
            <CardBody>
              <div className="flex flex-col items-center text-center">
                <div className="w-16 h-16 bg-secondary-100 dark:bg-secondary-900 rounded-full flex items-center justify-center mb-4">
                  <svg
                    xmlns="http://www.w3.org/2000/svg"
                    className="h-8 w-8 text-secondary-600 dark:text-secondary-400"
                    fill="none"
                    viewBox="0 0 24 24"
                    stroke="currentColor"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z"
                    />
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"
                    />
                  </svg>
                </div>
                <h2 className="text-xl font-bold text-gray-900 dark:text-white mb-2">
                  Troubleshooting Advisor
                </h2>
                <p className="text-gray-600 dark:text-gray-400">
                  Diagnose aircraft system issues and receive step-by-step troubleshooting guidance.
                </p>
              </div>
            </CardBody>
          </Card>
        </Link>

        <Link to="/maintenance" className="block">
          <Card className="h-full transition-transform hover:scale-105">
            <CardBody>
              <div className="flex flex-col items-center text-center">
                <div className="w-16 h-16 bg-green-100 dark:bg-green-900 rounded-full flex items-center justify-center mb-4">
                  <svg
                    xmlns="http://www.w3.org/2000/svg"
                    className="h-8 w-8 text-green-600 dark:text-green-400"
                    fill="none"
                    viewBox="0 0 24 24"
                    stroke="currentColor"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-3 7h3m-3 4h3m-6-4h.01M9 16h.01"
                    />
                  </svg>
                </div>
                <h2 className="text-xl font-bold text-gray-900 dark:text-white mb-2">
                  Maintenance Procedure Generator
                </h2>
                <p className="text-gray-600 dark:text-gray-400">
                  Generate customized maintenance procedures based on aircraft configuration and
                  regulatory requirements.
                </p>
              </div>
            </CardBody>
          </Card>
        </Link>
      </div>

      <div className="mt-12 bg-gray-50 dark:bg-gray-800 rounded-lg p-8">
        <div className="text-center mb-8">
          <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-2">
            How MAGPIE Can Help You
          </h2>
          <p className="text-gray-600 dark:text-gray-400">
            Our AI-powered platform streamlines aircraft maintenance operations
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          <div className="flex flex-col items-center text-center">
            <div className="w-12 h-12 bg-blue-100 dark:bg-blue-900 rounded-full flex items-center justify-center mb-4">
              <span className="text-xl font-bold text-blue-600 dark:text-blue-400">1</span>
            </div>
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">
              Faster Access to Information
            </h3>
            <p className="text-gray-600 dark:text-gray-400">
              Quickly find relevant technical documentation and procedures
            </p>
          </div>

          <div className="flex flex-col items-center text-center">
            <div className="w-12 h-12 bg-blue-100 dark:bg-blue-900 rounded-full flex items-center justify-center mb-4">
              <span className="text-xl font-bold text-blue-600 dark:text-blue-400">2</span>
            </div>
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">
              Improved Troubleshooting
            </h3>
            <p className="text-gray-600 dark:text-gray-400">
              Diagnose issues more accurately with AI-assisted analysis
            </p>
          </div>

          <div className="flex flex-col items-center text-center">
            <div className="w-12 h-12 bg-blue-100 dark:bg-blue-900 rounded-full flex items-center justify-center mb-4">
              <span className="text-xl font-bold text-blue-600 dark:text-blue-400">3</span>
            </div>
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">
              Customized Procedures
            </h3>
            <p className="text-gray-600 dark:text-gray-400">
              Generate maintenance procedures tailored to specific aircraft configurations
            </p>
          </div>

          <div className="flex flex-col items-center text-center">
            <div className="w-12 h-12 bg-blue-100 dark:bg-blue-900 rounded-full flex items-center justify-center mb-4">
              <span className="text-xl font-bold text-blue-600 dark:text-blue-400">4</span>
            </div>
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">
              Regulatory Compliance
            </h3>
            <p className="text-gray-600 dark:text-gray-400">
              Stay compliant with the latest aviation regulations and requirements
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;
