/**
 * Input Component Tests
 */

import React from 'react';
import { render, fireEvent } from '../utils/test-utils';
import { Input } from '@/components/ui/Input';

describe('Input Component', () => {
  it('should render input field', () => {
    const { getByTestId } = render(
      <Input placeholder="Enter text" testID="text-input" />
    );
    expect(getByTestId('text-input')).toBeTruthy();
  });

  it('should update value on change', () => {
    const mockOnChange = jest.fn();
    const { getByTestId } = render(
      <Input
        placeholder="Enter text"
        onChangeText={mockOnChange}
        testID="text-input"
      />
    );

    fireEvent.changeText(getByTestId('text-input'), 'new value');
    expect(mockOnChange).toHaveBeenCalledWith('new value');
  });

  it('should show error state', () => {
    const { getByTestId } = render(
      <Input
        placeholder="Enter text"
        error="Field is required"
        testID="error-input"
      />
    );

    expect(getByTestId('error-input')).toBeTruthy();
  });

  it('should be disabled when specified', () => {
    const mockOnChange = jest.fn();
    const { getByTestId } = render(
      <Input
        placeholder="Disabled"
        editable={false}
        onChangeText={mockOnChange}
        testID="disabled-input"
      />
    );

    fireEvent.changeText(getByTestId('disabled-input'), 'text');
    expect(mockOnChange).not.toHaveBeenCalled();
  });

  it('should hide text for password input', () => {
    const { getByTestId } = render(
      <Input placeholder="Password" secureTextEntry={true} testID="password-input" />
    );

    const input = getByTestId('password-input');
    expect(input.props.secureTextEntry).toBe(true);
  });
});
