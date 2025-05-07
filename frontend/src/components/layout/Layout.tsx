import { useState, useEffect } from 'react';
import Header from './Header';
import Footer from './Footer';

interface LayoutProps {
  children: React.ReactNode;
}

export default function Layout({ children }: LayoutProps) {
  const [isDarkMode, setIsDarkMode] = useState(false);

  useEffect(() => {
    // Check if user has a preference stored
    const storedDarkMode = localStorage.getItem('darkMode');

    if (storedDarkMode !== null) {
      setIsDarkMode(storedDarkMode === 'true');
    } else {
      // Check if user prefers dark mode at OS level
      const prefersDarkMode = window.matchMedia('(prefers-color-scheme: dark)').matches;
      setIsDarkMode(prefersDarkMode);
    }
  }, []);

  useEffect(() => {
    // Update the document class when dark mode changes
    if (isDarkMode) {
      document.documentElement.classList.add('dark');
    } else {
      document.documentElement.classList.remove('dark');
    }

    // Store the preference
    localStorage.setItem('darkMode', isDarkMode.toString());

    // Force scroll to top on initial render
    window.scrollTo(0, 0);
  }, [isDarkMode]);

  const toggleDarkMode = () => {
    setIsDarkMode(!isDarkMode);
  };

  // Track if this is the initial render
  const [isInitialRender, setIsInitialRender] = useState(true);

  // After component mounts, set isInitialRender to false
  useEffect(() => {
    // Use a timeout to ensure the component has fully rendered
    const timer = setTimeout(() => {
      setIsInitialRender(false);
    }, 1000);

    return () => clearTimeout(timer);
  }, []);

  return (
    <div className={`min-h-screen flex flex-col bg-gray-50 dark:bg-gray-900 text-gray-900 dark:text-gray-100 ${isInitialRender ? 'overflow-hidden' : ''}`}>
      <Header isDarkMode={isDarkMode} toggleDarkMode={toggleDarkMode} />
      <main className="flex-grow">
        {children}
      </main>
      <Footer />
    </div>
  );
}
