import Button from '../components/ui/Button';
import Card, { CardBody, CardHeader } from '../components/ui/Card';
import Input from '../components/ui/Input';

const TroubleshootingPage = () => {
  return (
    <div className="space-y-8">
      <div className="text-center mb-8">
        <h1 className="text-3xl font-bold text-gray-900 dark:text-white mb-2">
          Troubleshooting Advisor
        </h1>
        <p className="text-gray-600 dark:text-gray-400 max-w-3xl mx-auto">
          Diagnose aircraft system issues and receive step-by-step troubleshooting guidance.
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Problem Description */}
        <div className="lg:col-span-1">
          <Card>
            <CardHeader>
              <h2 className="text-lg font-semibold">Problem Description</h2>
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
                    System
                  </label>
                  <select className="w-full px-4 py-2 border border-gray-300 dark:border-gray-700 rounded-md bg-white dark:bg-gray-800">
                    <option>Select System</option>
                    <option>Electrical</option>
                    <option>Hydraulic</option>
                    <option>Fuel</option>
                    <option>Landing Gear</option>
                    <option>Avionics</option>
                    <option>Environmental Control</option>
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    Symptoms
                  </label>
                  <div className="space-y-2">
                    <div className="flex items-center">
                      <input
                        type="checkbox"
                        id="symptom1"
                        className="h-4 w-4 text-primary-600 focus:ring-primary-500 border-gray-300 rounded"
                      />
                      <label
                        htmlFor="symptom1"
                        className="ml-2 block text-sm text-gray-700 dark:text-gray-300"
                      >
                        Warning light illuminated
                      </label>
                    </div>
                    <div className="flex items-center">
                      <input
                        type="checkbox"
                        id="symptom2"
                        className="h-4 w-4 text-primary-600 focus:ring-primary-500 border-gray-300 rounded"
                      />
                      <label
                        htmlFor="symptom2"
                        className="ml-2 block text-sm text-gray-700 dark:text-gray-300"
                      >
                        Unusual noise
                      </label>
                    </div>
                    <div className="flex items-center">
                      <input
                        type="checkbox"
                        id="symptom3"
                        className="h-4 w-4 text-primary-600 focus:ring-primary-500 border-gray-300 rounded"
                      />
                      <label
                        htmlFor="symptom3"
                        className="ml-2 block text-sm text-gray-700 dark:text-gray-300"
                      >
                        System not responding
                      </label>
                    </div>
                    <div className="flex items-center">
                      <input
                        type="checkbox"
                        id="symptom4"
                        className="h-4 w-4 text-primary-600 focus:ring-primary-500 border-gray-300 rounded"
                      />
                      <label
                        htmlFor="symptom4"
                        className="ml-2 block text-sm text-gray-700 dark:text-gray-300"
                      >
                        Fluid leakage
                      </label>
                    </div>
                  </div>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    Additional Details
                  </label>
                  <textarea
                    rows={4}
                    className="w-full px-4 py-2 border border-gray-300 dark:border-gray-700 rounded-md bg-white dark:bg-gray-800"
                    placeholder="Describe the issue in detail..."
                  ></textarea>
                </div>

                <Button variant="primary" fullWidth>
                  Diagnose Problem
                </Button>
              </div>
            </CardBody>
          </Card>
        </div>

        {/* Troubleshooting Results */}
        <div className="lg:col-span-2">
          <Card>
            <CardHeader>
              <h2 className="text-lg font-semibold">Troubleshooting Results</h2>
            </CardHeader>
            <CardBody>
              <div className="bg-gray-50 dark:bg-gray-800 p-4 rounded-lg mb-6">
                <p className="text-gray-600 dark:text-gray-400 text-center">
                  Fill out the problem description form and click "Diagnose Problem" to receive
                  troubleshooting guidance.
                </p>
              </div>

              <div className="space-y-6">
                <div className="border-l-4 border-yellow-500 pl-4 py-2">
                  <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-2">
                    Potential Causes
                  </h3>
                  <p className="text-gray-600 dark:text-gray-400">
                    Your diagnostic results will appear here, showing potential causes of the
                    reported issue.
                  </p>
                </div>

                <div>
                  <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-2">
                    Recommended Troubleshooting Steps
                  </h3>
                  <div className="space-y-4">
                    <p className="text-gray-600 dark:text-gray-400">
                      Step-by-step troubleshooting procedures will be displayed here after diagnosis.
                    </p>
                  </div>
                </div>

                <div>
                  <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-2">
                    Required Tools and Parts
                  </h3>
                  <p className="text-gray-600 dark:text-gray-400">
                    A list of tools and parts needed for troubleshooting will appear here.
                  </p>
                </div>

                <div>
                  <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-2">
                    Related Documentation
                  </h3>
                  <p className="text-gray-600 dark:text-gray-400">
                    Links to relevant technical documentation will be provided here.
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

export default TroubleshootingPage;
