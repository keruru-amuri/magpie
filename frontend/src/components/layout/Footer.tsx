import Link from 'next/link';

export default function Footer() {
  return (
    <footer className="bg-white dark:bg-gray-800 border-t border-gray-200 dark:border-gray-700">
      <div className="max-w-7xl mx-auto py-6 px-4 sm:px-6 lg:px-8">
        <div className="md:flex md:items-center md:justify-between">
          <div className="flex justify-center md:justify-start space-x-6">
            <Link 
              href="/about" 
              className="text-gray-500 hover:text-gray-700 dark:text-gray-300 dark:hover:text-white text-sm"
            >
              About
            </Link>
            <Link 
              href="/help" 
              className="text-gray-500 hover:text-gray-700 dark:text-gray-300 dark:hover:text-white text-sm"
            >
              Help
            </Link>
            <Link 
              href="/privacy" 
              className="text-gray-500 hover:text-gray-700 dark:text-gray-300 dark:hover:text-white text-sm"
            >
              Privacy
            </Link>
            <Link 
              href="/terms" 
              className="text-gray-500 hover:text-gray-700 dark:text-gray-300 dark:hover:text-white text-sm"
            >
              Terms
            </Link>
          </div>
          <div className="mt-8 md:mt-0">
            <p className="text-center md:text-right text-sm text-gray-500 dark:text-gray-400">
              &copy; {new Date().getFullYear()} MAGPIE Platform. All rights reserved.
            </p>
          </div>
        </div>
      </div>
    </footer>
  );
}
