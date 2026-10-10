/**
 * useForm Hook - Wrapper for react-hook-form with Zod validation
 */

import { useForm as useReactHookForm, UseFormProps, FieldValues, UseFormReturn } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { ZodSchema } from 'zod';

interface UseFormOptions<T extends FieldValues> extends Omit<UseFormProps<T>, 'resolver'> {
  schema: ZodSchema<T>;
}

export function useForm<T extends FieldValues>(options: UseFormOptions<T>): UseFormReturn<T> {
  const { schema, ...formOptions } = options;

  return useReactHookForm<T>({
    ...formOptions,
    resolver: zodResolver(schema),
    mode: 'onChange', // Validate on change for better UX
  });
}
