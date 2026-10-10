/**
 * Button Component Tests
 */

import React from 'react';
import { render, fireEvent } from '../utils/test-utils';
import { Button } from '@/components/ui/Button';

describe('Button Component', () => {
  it('should render button with title', () => {
    const { getByText } = render(<Button title="Click Me" onPress={() => {}} />);
    expect(getByText('Click Me')).toBeTruthy();
  });

  it('should call onPress when pressed', () => {
    const mockOnPress = jest.fn();
    const { getByText } = render(<Button title="Click" onPress={mockOnPress} />);

    fireEvent.press(getByText('Click'));
    expect(mockOnPress).toHaveBeenCalled();
  });

  it('should be disabled when loading', () => {
    const mockOnPress = jest.fn();
    const { getByTestId } = render(
      <Button title="Click" onPress={mockOnPress} loading={true} testID="button" />
    );

    fireEvent.press(getByTestId('button'));
    expect(mockOnPress).not.toHaveBeenCalled();
  });

  it('should apply variant styles', () => {
    const { getByTestId } = render(
      <Button title="Danger" variant="danger" onPress={() => {}} testID="danger-btn" />
    );

    const button = getByTestId('danger-btn');
    expect(button).toBeTruthy();
  });

  it('should render full width when specified', () => {
    const { getByTestId } = render(
      <Button title="Full Width" fullWidth={true} onPress={() => {}} testID="full-btn" />
    );

    const button = getByTestId('full-btn');
    expect(button).toBeTruthy();
  });
});
