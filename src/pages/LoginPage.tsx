import { Link } from 'react-router-dom';

import Button from '../components/ui/Button';
import Card, { CardBody } from '../components/ui/Card';
import Input from '../components/ui/Input';

const LoginPage = () => {
  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 dark:bg-gray-900 py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-md w-full space-y-8">
        <div className="text-center">
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white">MAGPIE</h1>
          <h2 className="mt-6 text-2xl font-bold text-gray-900 dark:text-white">
            Sign in to your account
          </h2>
          <p className="mt-2 text-sm text-gray-600 dark:text-gray-400">
            Or{' '}
            <Link
              to="/register"
              className="font-medium text-primary-600 hover:text-primary-500 dark:text-primary-400"
            >
              create a new account
            </Link>
          </p>
        </div>

        <Card>
          <CardBody>
            <form className="space-y-6">
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
                  autoComplete="current-password"
                  required
                  fullWidth
                />
              </div>

              <div className="flex items-center justify-between">
                <div className="flex items-center">
                  <input
                    id="remember-me"
                    name="remember-me"
                    type="checkbox"
                    className="h-4 w-4 text-primary-600 focus:ring-primary-500 border-gray-300 rounded"
                  />
                  <label
                    htmlFor="remember-me"
                    className="ml-2 block text-sm text-gray-900 dark:text-gray-300"
                  >
                    Remember me
                  </label>
                </div>

                <div className="text-sm">
                  <a
                    href="#"
                    className="font-medium text-primary-600 hover:text-primary-500 dark:text-primary-400"
                  >
                    Forgot your password?
                  </a>
                </div>
              </div>

              <div>
                <Button type="submit" variant="primary" fullWidth>
                  Sign in
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

export default LoginPage;
