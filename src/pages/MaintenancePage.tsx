import Button from '../components/ui/Button';
import Card, { CardBody, CardHeader } from '../components/ui/Card';

const MaintenancePage = () => {
  return (
    <div className="space-y-8">
      <div className="text-center mb-8">
        <h1 className="text-3xl font-bold text-gray-900 dark:text-white mb-2">
          Maintenance Procedure Generator
        </h1>
        <p className="text-gray-600 dark:text-gray-400 max-w-3xl mx-auto">
          Generate customized maintenance procedures based on aircraft configuration and regulatory
          requirements.
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Configuration Panel */}
        <div className="lg:col-span-1">
          <Card>
            <CardHeader>
              <h2 className="text-lg font-semibold">Procedure Configuration</h2>
            </CardHeader>
            <CardBody>
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    Aircraft Type
                  </label>
                  <select className="w-full px-4 py-2 border border-gray-300 dark:border-gray-700 rounded-md bg-white dark:bg-gray-800">
                    <option>Select Aircraft Type</option>
                    <option>Boeing 737</option>
                    <option>Airbus A320</option>
                    <option>Embraer E190</option>
                    <option>Bombardier CRJ900</option>
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    Maintenance Type
                  </label>
                  <select className="w-full px-4 py-2 border border-gray-300 dark:border-gray-700 rounded-md bg-white dark:bg-gray-800">
                    <option>Select Maintenance Type</option>
                    <option>Line Maintenance</option>
                    <option>A Check</option>
                    <option>B Check</option>
                    <option>C Check</option>
                    <option>D Check</option>
                    <option>Component Replacement</option>
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    System/Component
                  </label>
                  <select className="w-full px-4 py-2 border border-gray-300 dark:border-gray-700 rounded-md bg-white dark:bg-gray-800">
                    <option>Select System/Component</option>
                    <option>Engine</option>
                    <option>Landing Gear</option>
                    <option>Flight Controls</option>
                    <option>Fuel System</option>
                    <option>Hydraulic System</option>
                    <option>Electrical System</option>
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    Regulatory Framework
                  </label>
                  <select className="w-full px-4 py-2 border border-gray-300 dark:border-gray-700 rounded-md bg-white dark:bg-gray-800">
                    <option>Select Regulatory Framework</option>
                    <option>FAA</option>
                    <option>EASA</option>
                    <option>Transport Canada</option>
                    <option>CASA (Australia)</option>
                    <option>CAAC (China)</option>
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    Aircraft Configuration
                  </label>
                  <div className="space-y-2">
                    <div className="flex items-center">
                      <input
                        type="checkbox"
                        id="config1"
                        className="h-4 w-4 text-primary-600 focus:ring-primary-500 border-gray-300 rounded"
                      />
                      <label
                        htmlFor="config1"
                        className="ml-2 block text-sm text-gray-700 dark:text-gray-300"
                      >
                        Extended Range Operations
                      </label>
                    </div>
                    <div className="flex items-center">
                      <input
                        type="checkbox"
                        id="config2"
                        className="h-4 w-4 text-primary-600 focus:ring-primary-500 border-gray-300 rounded"
                      />
                      <label
                        htmlFor="config2"
                        className="ml-2 block text-sm text-gray-700 dark:text-gray-300"
                      >
                        Cold Weather Package
                      </label>
                    </div>
                    <div className="flex items-center">
                      <input
                        type="checkbox"
                        id="config3"
                        className="h-4 w-4 text-primary-600 focus:ring-primary-500 border-gray-300 rounded"
                      />
                      <label
                        htmlFor="config3"
                        className="ml-2 block text-sm text-gray-700 dark:text-gray-300"
                      >
                        High Altitude Operations
                      </label>
                    </div>
                  </div>
                </div>

                <Button variant="primary" fullWidth>
                  Generate Procedure
                </Button>
              </div>
            </CardBody>
          </Card>
        </div>

        {/* Generated Procedure */}
        <div className="lg:col-span-2">
          <Card>
            <CardHeader>
              <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
                <h2 className="text-lg font-semibold">Generated Maintenance Procedure</h2>
                <div className="flex items-center space-x-2">
                  <Button variant="outline" size="sm">
                    <svg
                      xmlns="http://www.w3.org/2000/svg"
                      className="h-4 w-4 mr-1"
                      fill="none"
                      viewBox="0 0 24 24"
                      stroke="currentColor"
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4"
                      />
                    </svg>
                    Export PDF
                  </Button>
                  <Button variant="outline" size="sm">
                    <svg
                      xmlns="http://www.w3.org/2000/svg"
                      className="h-4 w-4 mr-1"
                      fill="none"
                      viewBox="0 0 24 24"
                      stroke="currentColor"
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M8 7v8a2 2 0 002 2h6M8 7V5a2 2 0 012-2h4.586a1 1 0 01.707.293l4.414 4.414a1 1 0 01.293.707V15a2 2 0 01-2 2h-2M8 7H6a2 2 0 00-2 2v10a2 2 0 002 2h8a2 2 0 002-2v-2"
                      />
                    </svg>
                    Copy
                  </Button>
                </div>
              </div>
            </CardHeader>
            <CardBody>
              <div className="bg-gray-50 dark:bg-gray-800 p-4 rounded-lg mb-6">
                <p className="text-gray-600 dark:text-gray-400 text-center">
                  Configure the maintenance procedure parameters and click "Generate Procedure" to
                  create a customized maintenance procedure.
                </p>
              </div>

              <div className="space-y-6">
                <div>
                  <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-2">
                    Procedure Overview
                  </h3>
                  <p className="text-gray-600 dark:text-gray-400">
                    The generated procedure overview will appear here.
                  </p>
                </div>

                <div>
                  <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-2">
                    Safety Precautions
                  </h3>
                  <p className="text-gray-600 dark:text-gray-400">
                    Safety warnings and precautions will be listed here.
                  </p>
                </div>

                <div>
                  <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-2">
                    Required Tools and Equipment
                  </h3>
                  <p className="text-gray-600 dark:text-gray-400">
                    A list of required tools and equipment will appear here.
                  </p>
                </div>

                <div>
                  <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-2">
                    Procedure Steps
                  </h3>
                  <div className="space-y-4">
                    <p className="text-gray-600 dark:text-gray-400">
                      Detailed step-by-step maintenance procedures will be displayed here.
                    </p>
                  </div>
                </div>

                <div>
                  <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-2">
                    Regulatory References
                  </h3>
                  <p className="text-gray-600 dark:text-gray-400">
                    References to relevant regulatory requirements will be listed here.
                  </p>
                </div>
              </div>
            </CardBody>
          </Card>
        </div>
      </div>
    </div>
  );
};

export default MaintenancePage;
