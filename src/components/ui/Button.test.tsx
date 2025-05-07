import { render, screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';

import Button from './Button';

describe('Button Component', () => {
  it('renders correctly with default props', () => {
    render(<Button>Click me</Button>);
    const button = screen.getByRole('button', { name: /click me/i });
    expect(button).toBeInTheDocument();
    expect(button).toHaveClass('bg-primary-600');
  });

  it('renders with secondary variant', () => {
    render(<Button variant="secondary">Secondary Button</Button>);
    const button = screen.getByRole('button', { name: /secondary button/i });
    expect(button).toHaveClass('bg-secondary-600');
  });

  it('renders with outline variant', () => {
    render(<Button variant="outline">Outline Button</Button>);
    const button = screen.getByRole('button', { name: /outline button/i });
    expect(button).toHaveClass('border-gray-300');
    expect(button).toHaveClass('bg-transparent');
  });

  it('renders with ghost variant', () => {
    render(<Button variant="ghost">Ghost Button</Button>);
    const button = screen.getByRole('button', { name: /ghost button/i });
    expect(button).toHaveClass('bg-transparent');
  });

  it('renders with different sizes', () => {
    const { rerender } = render(<Button size="sm">Small Button</Button>);
    let button = screen.getByRole('button', { name: /small button/i });
    expect(button).toHaveClass('px-3 py-1.5 text-sm');

    rerender(<Button size="md">Medium Button</Button>);
    button = screen.getByRole('button', { name: /medium button/i });
    expect(button).toHaveClass('px-4 py-2 text-base');

    rerender(<Button size="lg">Large Button</Button>);
    button = screen.getByRole('button', { name: /large button/i });
    expect(button).toHaveClass('px-6 py-3 text-lg');
  });

  it('renders full width button', () => {
    render(<Button fullWidth>Full Width Button</Button>);
    const button = screen.getByRole('button', { name: /full width button/i });
    expect(button).toHaveClass('w-full');
  });

  it('passes additional props to the button element', () => {
    render(
      <Button data-testid="test-button" disabled>
        Disabled Button
      </Button>
    );
    const button = screen.getByTestId('test-button');
    expect(button).toBeDisabled();
  });
});
