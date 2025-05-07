import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';

import Layout from './components/layout/Layout';
import Dashboard from './pages/Dashboard';
import DocumentationPage from './pages/DocumentationPage';
import LoginPage from './pages/LoginPage';
import MaintenancePage from './pages/MaintenancePage';
import NotFoundPage from './pages/NotFoundPage';
import RegisterPage from './pages/RegisterPage';
import TroubleshootingPage from './pages/TroubleshootingPage';

function App() {
  return (
    <Router>
      <Routes>
        <Route
          path="/"
          element={
            <Layout>
              <Dashboard />
            </Layout>
          }
        />
        <Route
          path="/documentation"
          element={
            <Layout>
              <DocumentationPage />
            </Layout>
          }
        />
        <Route
          path="/troubleshooting"
          element={
            <Layout>
              <TroubleshootingPage />
            </Layout>
          }
        />
        <Route
          path="/maintenance"
          element={
            <Layout>
              <MaintenancePage />
            </Layout>
          }
        />
        <Route path="/login" element={<LoginPage />} />
        <Route path="/register" element={<RegisterPage />} />
        <Route
          path="*"
          element={
            <Layout>
              <NotFoundPage />
            </Layout>
          }
        />
      </Routes>
    </Router>
  );
}

export default App;
