'use client';

import React, { useState } from 'react';
import { Dialog, Transition } from '@headlessui/react';
import { XMarkIcon, CommandLineIcon } from '@heroicons/react/24/outline';

interface Shortcut {
  key: string;
  description: string;
  isMac?: boolean;
  isWindows?: boolean;
}

export default function KeyboardShortcutsHelp() {
  const [isOpen, setIsOpen] = useState(false);
  const isMac = typeof navigator !== 'undefined' ? navigator.platform.toUpperCase().indexOf('MAC') >= 0 : false;

  const shortcuts: Shortcut[] = [
    { key: `${isMac ? '⌘' : 'Ctrl'} + /`, description: 'Focus the chat input' },
    { key: `${isMac ? '⌘' : 'Ctrl'} + .`, description: 'Toggle context panel' },
    { key: 'Esc', description: 'Close context panel' },
    { key: 'Enter', description: 'Send message' },
    { key: 'Shift + Enter', description: 'Add new line in message' },
    { key: '↑', description: 'Edit last message (when input is empty)' },
  ];

  return (
    <>
      <button
        onClick={() => setIsOpen(true)}
        className="p-2 rounded-full text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-800"
        aria-label="Keyboard shortcuts"
        title="Keyboard shortcuts"
      >
        <CommandLineIcon className="h-5 w-5" />
      </button>

      <Transition show={isOpen} as={React.Fragment}>
        <Dialog
          as="div"
          className="fixed inset-0 z-50 overflow-y-auto"
          onClose={() => setIsOpen(false)}
        >
          <div className="min-h-screen px-4 text-center">
            <Transition.Child
              as={React.Fragment}
              enter="ease-out duration-300"
              enterFrom="opacity-0"
              enterTo="opacity-100"
              leave="ease-in duration-200"
              leaveFrom="opacity-100"
              leaveTo="opacity-0"
            >
              <Dialog.Overlay className="fixed inset-0 bg-black opacity-30" />
            </Transition.Child>

            {/* This element is to trick the browser into centering the modal contents. */}
            <span
              className="inline-block h-screen align-middle"
              aria-hidden="true"
            >
              &#8203;
            </span>
            
            <Transition.Child
              as={React.Fragment}
              enter="ease-out duration-300"
              enterFrom="opacity-0 scale-95"
              enterTo="opacity-100 scale-100"
              leave="ease-in duration-200"
              leaveFrom="opacity-100 scale-100"
              leaveTo="opacity-0 scale-95"
            >
              <div className="inline-block w-full max-w-md p-6 my-8 overflow-hidden text-left align-middle transition-all transform bg-white dark:bg-gray-800 shadow-xl rounded-2xl">
                <div className="flex justify-between items-center mb-4">
                  <Dialog.Title
                    as="h3"
                    className="text-lg font-medium leading-6 text-gray-900 dark:text-white flex items-center"
                  >
                    <CommandLineIcon className="h-5 w-5 mr-2" />
                    Keyboard Shortcuts
                  </Dialog.Title>
                  <button
                    type="button"
                    className="text-gray-400 hover:text-gray-500 dark:hover:text-gray-300"
                    onClick={() => setIsOpen(false)}
                  >
                    <span className="sr-only">Close</span>
                    <XMarkIcon className="h-6 w-6" aria-hidden="true" />
                  </button>
                </div>
                
                <div className="mt-2">
                  <div className="space-y-2">
                    {shortcuts.map((shortcut, index) => (
                      <div
                        key={index}
                        className="flex justify-between items-center py-2 border-b border-gray-200 dark:border-gray-700 last:border-0"
                      >
                        <span className="text-gray-700 dark:text-gray-300">
                          {shortcut.description}
                        </span>
                        <kbd className="px-2 py-1 text-xs font-semibold text-gray-800 bg-gray-100 border border-gray-200 rounded-lg dark:bg-gray-700 dark:text-gray-200 dark:border-gray-600">
                          {shortcut.key}
                        </kbd>
                      </div>
                    ))}
                  </div>
                </div>
                
                <div className="mt-6">
                  <button
                    type="button"
                    className="w-full inline-flex justify-center px-4 py-2 text-sm font-medium text-white bg-primary-600 border border-transparent rounded-md hover:bg-primary-700 focus:outline-none focus-visible:ring-2 focus-visible:ring-offset-2 focus-visible:ring-primary-500 dark:bg-primary-500 dark:hover:bg-primary-600"
                    onClick={() => setIsOpen(false)}
                  >
                    Got it
                  </button>
                </div>
              </div>
            </Transition.Child>
          </div>
        </Dialog>
      </Transition>
    </>
  );
}
