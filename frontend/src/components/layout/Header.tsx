import { useState } from 'react';
import Link from 'next/link';
import { Disclosure } from '@headlessui/react';
import { Bars3Icon, XMarkIcon, SunIcon, MoonIcon } from '@heroicons/react/24/outline';

const navigation = [
  { name: 'Dashboard', href: '/' },
  { name: 'Documentation', href: '/documentation' },
  { name: 'Troubleshooting', href: '/troubleshooting' },
  { name: 'Maintenance', href: '/maintenance' },
];

interface HeaderProps {
  isDarkMode: boolean;
  toggleDarkMode: () => void;
}

export default function Header({ isDarkMode, toggleDarkMode }: HeaderProps) {
  return (
    <Disclosure as="nav" className="bg-white dark:bg-gray-800 shadow-sm">
      {({ open }) => (
        <>
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="flex justify-between h-16">
              <div className="flex">
                <div className="flex-shrink-0 flex items-center">
                  <Link href="/" className="flex items-center">
                    <div className="h-10 w-10 rounded-md bg-gradient-to-br from-primary-500 to-primary-700 flex items-center justify-center text-white mr-3">
                      <svg 
                        xmlns="http://www.w3.org/2000/svg" 
                        className="h-6 w-6" 
                        viewBox="0 0 24 24" 
                        fill="none" 
                        stroke="currentColor" 
                        strokeWidth="2" 
                        strokeLinecap="round" 
                        strokeLinejoin="round"
                      >
                        <path d="M22 12H8l4-4H8l-6 6 6 6h4l-4-4h14z" />
                      </svg>
                    </div>
                    <span className="text-xl font-bold text-gray-900 dark:text-white">MAGPIE</span>
                  </Link>
                </div>
                <div className="hidden sm:ml-6 sm:flex sm:space-x-8">
                  {navigation.map((item) => (
                    <Link
                      key={item.name}
                      href={item.href}
                      className="inline-flex items-center px-1 pt-1 border-b-2 border-transparent text-sm font-medium text-gray-500 hover:text-gray-700 hover:border-gray-300 dark:text-gray-300 dark:hover:text-white dark:hover:border-gray-600"
                    >
                      {item.name}
                    </Link>
                  ))}
                </div>
              </div>
              <div className="hidden sm:ml-6 sm:flex sm:items-center">
                <button
                  onClick={toggleDarkMode}
                  className="p-2 rounded-full text-gray-500 hover:text-gray-700 dark:text-gray-300 dark:hover:text-white focus:outline-none"
                >
                  {isDarkMode ? (
                    <SunIcon className="h-5 w-5" aria-hidden="true" />
                  ) : (
                    <MoonIcon className="h-5 w-5" aria-hidden="true" />
                  )}
                </button>
              </div>
              <div className="-mr-2 flex items-center sm:hidden">
                <Disclosure.Button className="inline-flex items-center justify-center p-2 rounded-md text-gray-400 hover:text-gray-500 hover:bg-gray-100 dark:hover:bg-gray-700 dark:hover:text-white focus:outline-none">
                  <span className="sr-only">Open main menu</span>
                  {open ? (
                    <XMarkIcon className="block h-6 w-6" aria-hidden="true" />
                  ) : (
                    <Bars3Icon className="block h-6 w-6" aria-hidden="true" />
                  )}
                </Disclosure.Button>
              </div>
            </div>
          </div>

          <Disclosure.Panel className="sm:hidden">
            <div className="pt-2 pb-3 space-y-1">
              {navigation.map((item) => (
                <Disclosure.Button
                  key={item.name}
                  as={Link}
                  href={item.href}
                  className="block pl-3 pr-4 py-2 border-l-4 border-transparent text-base font-medium text-gray-500 hover:text-gray-700 hover:bg-gray-50 hover:border-gray-300 dark:text-gray-300 dark:hover:text-white dark:hover:bg-gray-700 dark:hover:border-gray-600"
                >
                  {item.name}
                </Disclosure.Button>
              ))}
              <div className="pl-3 pr-4 py-2 flex items-center">
                <button
                  onClick={toggleDarkMode}
                  className="p-2 rounded-full text-gray-500 hover:text-gray-700 dark:text-gray-300 dark:hover:text-white focus:outline-none"
                >
                  {isDarkMode ? (
                    <SunIcon className="h-5 w-5" aria-hidden="true" />
                  ) : (
                    <MoonIcon className="h-5 w-5" aria-hidden="true" />
                  )}
                </button>
                <span className="ml-2 text-sm text-gray-500 dark:text-gray-300">
                  {isDarkMode ? 'Light Mode' : 'Dark Mode'}
                </span>
              </div>
            </div>
          </Disclosure.Panel>
        </>
      )}
    </Disclosure>
  );
}
