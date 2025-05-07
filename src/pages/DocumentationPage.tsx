import Card, { CardBody, CardHeader } from '../components/ui/Card';
import Input from '../components/ui/Input';

const DocumentationPage = () => {
  return (
    <div className="space-y-8">
      <div className="text-center mb-8">
        <h1 className="text-3xl font-bold text-gray-900 dark:text-white mb-2">
          Technical Documentation Assistant
        </h1>
        <p className="text-gray-600 dark:text-gray-400 max-w-3xl mx-auto">
          Access, search, and understand technical aircraft documentation with AI-powered assistance.
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        {/* Sidebar */}
        <div className="lg:col-span-1">
          <Card>
            <CardHeader>
              <h2 className="text-lg font-semibold">Document Categories</h2>
            </CardHeader>
            <CardBody className="p-0">
              <nav className="space-y-1">
                <a
                  href="#"
                  className="block px-4 py-2 text-primary-600 dark:text-primary-400 bg-primary-50 dark:bg-primary-900/20 border-l-4 border-primary-600 dark:border-primary-400"
                >
                  Aircraft Manuals
                </a>
                <a
                  href="#"
                  className="block px-4 py-2 text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-800 border-l-4 border-transparent"
                >
                  Service Bulletins
                </a>
                <a
                  href="#"
                  className="block px-4 py-2 text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-800 border-l-4 border-transparent"
                >
                  Component Manuals
                </a>
                <a
                  href="#"
                  className="block px-4 py-2 text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-800 border-l-4 border-transparent"
                >
                  Regulatory Documents
                </a>
                <a
                  href="#"
                  className="block px-4 py-2 text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-800 border-l-4 border-transparent"
                >
                  Wiring Diagrams
                </a>
                <a
                  href="#"
                  className="block px-4 py-2 text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-800 border-l-4 border-transparent"
                >
                  Illustrated Parts Catalog
                </a>
              </nav>
            </CardBody>
          </Card>

          <Card className="mt-6">
            <CardHeader>
              <h2 className="text-lg font-semibold">Recent Searches</h2>
            </CardHeader>
            <CardBody className="p-0">
              <nav className="space-y-1">
                <a
                  href="#"
                  className="block px-4 py-2 text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-800"
                >
                  Engine start procedure
                </a>
                <a
                  href="#"
                  className="block px-4 py-2 text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-800"
                >
                  Landing gear inspection
                </a>
                <a
                  href="#"
                  className="block px-4 py-2 text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-800"
                >
                  Fuel system components
                </a>
              </nav>
            </CardBody>
          </Card>
        </div>

        {/* Main Content */}
        <div className="lg:col-span-3">
          <Card>
            <CardHeader>
              <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
                <h2 className="text-xl font-semibold">Documentation Search</h2>
                <div className="flex items-center space-x-2">
                  <select className="px-3 py-2 border border-gray-300 dark:border-gray-700 rounded-md bg-white dark:bg-gray-800">
                    <option>All Documents</option>
                    <option>Aircraft Manuals</option>
                    <option>Service Bulletins</option>
                    <option>Component Manuals</option>
                  </select>
                </div>
              </div>
            </CardHeader>
            <CardBody>
              <div className="mb-6">
                <Input
                  type="text"
                  placeholder="Ask a question or search for documentation..."
                  fullWidth
                />
              </div>

              <div className="bg-gray-50 dark:bg-gray-800 p-4 rounded-lg mb-6">
                <p className="text-gray-600 dark:text-gray-400 text-center">
                  Ask questions like:
                  <span className="block mt-2 font-medium text-gray-900 dark:text-white">
                    "What are the inspection intervals for the landing gear?"
                  </span>
                  <span className="block mt-1 font-medium text-gray-900 dark:text-white">
                    "Show me the engine start procedure for Boeing 737"
                  </span>
                  <span className="block mt-1 font-medium text-gray-900 dark:text-white">
                    "Summarize the latest service bulletin for the fuel system"
                  </span>
                </p>
              </div>

              <div className="space-y-4">
                <div className="p-4 bg-gray-50 dark:bg-gray-800 rounded-lg">
                  <p className="text-gray-900 dark:text-white">
                    Your documentation results will appear here. Use the search box above to get
                    started.
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

export default DocumentationPage;
