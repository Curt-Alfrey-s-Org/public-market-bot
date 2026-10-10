/**
 * Theme System - Colors, spacing, typography for light/dark modes
 */

export const colors = {
  light: {
    primary: '#0ea5e9', // sky-500
    primaryDark: '#0284c7', // sky-600
    secondary: '#64748b', // slate-500
    background: '#ffffff',
    surface: '#f8fafc', // slate-50
    surfaceSecondary: '#f1f5f9', // slate-100
    text: '#0f172a', // slate-950
    textSecondary: '#64748b', // slate-500
    border: '#e2e8f0', // slate-200
    error: '#ef4444', // red-500
    success: '#22c55e', // green-500
    warning: '#f59e0b', // amber-500
    info: '#3b82f6', // blue-500
    overlay: 'rgba(0, 0, 0, 0.5)',
  },
  dark: {
    primary: '#0ea5e9', // sky-500
    primaryDark: '#0284c7', // sky-600
    secondary: '#64748b', // slate-500
    background: '#0f172a', // slate-950
    surface: '#1e293b', // slate-800
    surfaceSecondary: '#334155', // slate-700
    text: '#f8fafc', // slate-50
    textSecondary: '#cbd5e1', // slate-300
    border: '#334155', // slate-700
    error: '#ef4444',
    success: '#22c55e',
    warning: '#f59e0b',
    info: '#3b82f6',
    overlay: 'rgba(0, 0, 0, 0.7)',
  },
};

export const spacing = {
  xs: 4,
  sm: 8,
  md: 16,
  lg: 24,
  xl: 32,
  xxl: 48,
};

export const borderRadius = {
  sm: 4,
  md: 8,
  lg: 12,
  xl: 16,
  full: 9999,
};

export const typography = {
  fontSizes: {
    xs: 12,
    sm: 14,
    md: 16,
    lg: 18,
    xl: 20,
    xxl: 24,
    xxxl: 32,
  },
  fontWeights: {
    regular: '400' as const,
    medium: '500' as const,
    semibold: '600' as const,
    bold: '700' as const,
  },
  lineHeights: {
    tight: 1.2,
    normal: 1.5,
    relaxed: 1.75,
  },
};

export const shadows = {
  sm: {
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.05,
    shadowRadius: 2,
    elevation: 2,
  },
  md: {
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 4,
  },
  lg: {
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.15,
    shadowRadius: 8,
    elevation: 8,
  },
};

export type Theme = {
  colors: typeof colors.light;
  spacing: typeof spacing;
  borderRadius: typeof borderRadius;
  typography: typeof typography;
  shadows: typeof shadows;
  isDark: boolean;
};

export const createTheme = (isDark: boolean): Theme => ({
  colors: isDark ? colors.dark : colors.light,
  spacing,
  borderRadius,
  typography,
  shadows,
  isDark,
});
