import { Link } from 'react-router-dom';

import Button from '../components/ui/Button';
import Card, { CardBody } from '../components/ui/Card';
import Input from '../components/ui/Input';

const RegisterPage = () => {
  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 dark:bg-gray-900 py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-md w-full space-y-8">
        <div className="text-center">
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white">MAGPIE</h1>
          <h2 className="mt-6 text-2xl font-bold text-gray-900 dark:text-white">
            Create a new account
          </h2>
          <p className="mt-2 text-sm text-gray-600 dark:text-gray-400">
            Or{' '}
            <Link
              to="/login"
              className="font-medium text-primary-600 hover:text-primary-500 dark:text-primary-400"
            >
              sign in to your existing account
            </Link>
          </p>
        </div>

        <Card>
          <CardBody>
            <form className="space-y-6">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <Input
                    label="First Name"
                    type="text"
                    id="firstName"
                    autoComplete="given-name"
                    required
                    fullWidth
                  />
                </div>
                <div>
                  <Input
                    label="Last Name"
                    type="text"
                    id="lastName"
                    autoComplete="family-name"
                    required
                    fullWidth
                  />
                </div>
              </div>

              <div>
                <Input
                  label="Email Address"
                  type="email"
                  id="email"
                  autoComplete="email"
                  required
                  fullWidth
                />
              </div>

              <div>
                <Input
                  label="Password"
                  type="password"
                  id="password"
                  autoComplete="new-password"
                  required
                  fullWidth
                />
              </div>

              <div>
                <Input
                  label="Confirm Password"
                  type="password"
                  id="confirmPassword"
                  autoComplete="new-password"
                  required
                  fullWidth
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Role
                </label>
                <select className="w-full px-4 py-2 border border-gray-300 dark:border-gray-700 rounded-md bg-white dark:bg-gray-800">
                  <option>Select Role</option>
                  <option>Maintenance Technician</option>
                  <option>Engineer</option>
                  <option>Inspector</option>
                  <option>Manager</option>
                  <option>Administrator</option>
                </select>
              </div>

              <div className="flex items-center">
                <input
                  id="terms"
                  name="terms"
                  type="checkbox"
                  className="h-4 w-4 text-primary-600 focus:ring-primary-500 border-gray-300 rounded"
                  required
                />
                <label
                  htmlFor="terms"
                  className="ml-2 block text-sm text-gray-900 dark:text-gray-300"
                >
                  I agree to the{' '}
                  <a
                    href="#"
                    className="font-medium text-primary-600 hover:text-primary-500 dark:text-primary-400"
                  >
                    Terms of Service
                  </a>{' '}
                  and{' '}
                  <a
                    href="#"
                    className="font-medium text-primary-600 hover:text-primary-500 dark:text-primary-400"
                  >
                    Privacy Policy
                  </a>
                </label>
              </div>

              <div>
                <Button type="submit" variant="primary" fullWidth>
                  Create Account
                </Button>
              </div>
            </form>
          </CardBody>
        </Card>

        <div className="text-center mt-4">
          <Link to="/" className="text-sm text-gray-600 dark:text-gray-400 hover:underline">
            Back to Home
          </Link>
        </div>
      </div>
    </div>
  );
};

export default RegisterPage;
