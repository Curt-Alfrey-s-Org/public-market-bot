/**
 * Validation Schemas - Zod schemas for form validation
 */

import { z } from 'zod';

// Login form schema
export const loginSchema = z.object({
  username: z
    .string()
    .min(3, 'Username must be at least 3 characters')
    .max(50, 'Username must be less than 50 characters')
    .regex(/^[a-zA-Z0-9_-]+$/, 'Username can only contain letters, numbers, underscores, and hyphens'),
  password: z
    .string()
    .min(6, 'Password must be at least 6 characters')
    .max(100, 'Password must be less than 100 characters'),
});

export type LoginFormData = z.infer<typeof loginSchema>;

// Settings form schema
export const settingsSchema = z.object({
  displayName: z
    .string()
    .min(2, 'Display name must be at least 2 characters')
    .max(50, 'Display name must be less than 50 characters')
    .optional(),
  email: z
    .string()
    .email('Invalid email address')
    .optional()
    .or(z.literal('')),
  notifications: z.boolean().default(true),
  darkMode: z.boolean().default(false),
});

export type SettingsFormData = z.infer<typeof settingsSchema>;

// Trade filter schema
export const tradeFilterSchema = z.object({
  startDate: z.date().optional(),
  endDate: z.date().optional(),
  minAmount: z.number().min(0, 'Amount must be positive').optional(),
  maxAmount: z.number().min(0, 'Amount must be positive').optional(),
  status: z.enum(['all', 'open', 'closed', 'pending']).default('all'),
});

export type TradeFilterData = z.infer<typeof tradeFilterSchema>;
