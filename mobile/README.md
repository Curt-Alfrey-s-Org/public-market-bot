# Market Bot Mobile App

AI-powered trading bot mobile application built with React Native and Expo.

## ✨ Phase 3-B: Enhanced UI/UX - COMPLETED

### New Features
- 🎨 Custom UI component library with 6 reusable components
- ✅ Form validation using react-hook-form + zod
- 🔔 Toast notifications with auto-dismiss
- 🌓 Light/Dark theme system with toggle
- 💀 Loading skeletons for better perceived performance
- 🛡️ Error boundaries for graceful error handling
- ♿ Full accessibility support (WCAG compliant)

## Features

- 🔐 JWT Authentication with automatic token refresh
- 📊 Real-time bot status monitoring
- 📈 Trade history and statistics
- 🎯 Bot control (start/stop)
- 📱 Cross-platform (iOS, Android, Web)
- 🔒 Secure token storage with expo-secure-store
- 🎨 Professional UI with theme switching
- 📝 Form validation with error messages
- 🔔 Toast notifications for user feedback

## Tech Stack

- **Framework:** Expo ~54.0 with Expo Router (file-based routing)
- **Language:** TypeScript (strict mode)
- **State Management:** Zustand + @tanstack/react-query
- **API Communication:** Axios with interceptors
- **Storage:** expo-secure-store + @react-native-async-storage/async-storage
- **Form Validation:** react-hook-form + zod
- **UI:** React Native with custom component library
- **Icons:** @expo/vector-icons (Ionicons)

## Prerequisites

- Node.js 18+ and npm
- Expo CLI (`npm install -g expo-cli`)
- For iOS: macOS with Xcode
- For Android: Android Studio
- Market Bot API running (default: http://localhost:8004)

## Installation

```bash
# Install dependencies
npm install

# Copy environment template
cp .env.example .env.local

# Edit .env.local and set your API URL
# EXPO_PUBLIC_API_URL=http://your-api-url:8004/api/v1
```

## Running the App

### Development Mode

```bash
# Start the development server
npm start

# Run on specific platforms
npm run android  # Android
npm run ios      # iOS (requires macOS)
npm run web      # Web browser
```

### Testing on Physical Device

1. Install Expo Go app on your device:
   - iOS: https://apps.apple.com/app/expo-go/id982107779
   - Android: https://play.google.com/store/apps/details?id=host.exp.exponent

2. Scan the QR code shown in the terminal with:
   - iOS: Camera app
   - Android: Expo Go app

### Production Build

```bash
# Install EAS CLI
npm install -g eas-cli

# Login to Expo
eas login

# Build for iOS
eas build --platform ios

# Build for Android
eas build --platform android
```

## Project Structure

```
mobile/
├── app/                    # Expo Router pages
│   ├── (auth)/            # Authenticati with validation
│   ├── (tabs)/            # Main app tabs
│   │   ├── _layout.tsx    # Tabs layout
│   │   ├── index.tsx      # Dashboard screen
│   │   ├── trades.tsx     # Trades history screen
│   │   └── settings.tsx   # Settings & theme toggle
│   └── _layout.tsx        # Root layout with providers
├── src/
│   ├── api/               # API layer
│   │   ├── client.ts      # Axios instance with interceptors
│   │   └── services/      # API service modules
│   │       ├── auth.ts    # Authentication
│   │       ├── bot.ts     # Bot control
│   │       └── trades.ts  # Trades history
│   ├── components/        # React components
│   │   ├── ui/            # Reusable UI components
│   │   │   ├── Button.tsx         # Custom button
│   │   │   ├── Card.tsx           # Container card
│   │   │   ├── Input.tsx          # Form input
│   │   │   ├── Badge.tsx          # Status badge
│   │   │   ├── LoadingSkeleton.tsx # Loading state
│   │   │   └── index.ts           # Barrel export
│   │   ├── ErrorBoundary.tsx      # Error catcher
│   │   ├── Toast.tsx              # Notifications
│   │   └── FullPageLoader.tsx     # Loading screen
│   ├── context/           # React contexts
│   │   ├── AuthContext.tsx        # Auth state
│   │   ├── ThemeContext.tsx       # Theme management
│   │   └── ToastContext.tsx       # Toast notifications
│   ├── hooks/             # Custom React hooks
│   │   └── useForm.ts             # Form validation hook
│   ├── types/             # TypeScript type definitions
│   │   └── index.ts       # API response types
│   ├── utils/             # Utility functions
│   │   ├── storage.ts     # Secure token storage
│   │   └── validation.ts  # Zod validation schemas
│   └── constants/         # App constants
│       ├── api.ts         # API configuration
│       └── theme.ts       # Theme colors & stylesage
│   └── constants/         # App constants
│       └── api.ts         # API configuration
├── assets/                # Images, fonts, etc.
├── .env.example           # Environment template
├── .env.local             # Local environment (gitignored)
├── app.json               # Expo configuration
├── package.json           # Dependencies
└── tsconfig.json          # TypeScript configuration
```

## 🎨 UI Component Library

### Button Component

Customizable button with variants, sizes, and loading states.

```tsx
import { Button } from '@/components/ui';

// Basic usage
<Button title="Click Me" onPress={handlePress} />

// With variants
<Button title="Primary" variant="primary" onPress={handlePress} />
<Button title="Secondary" variant="secondary" onPress={handlePress} />
<Button title="Danger" variant="danger" onPress={handlePress} />
<Button title="Ghost" variant="ghost" onPress={handlePress} />

// With sizes
<Button title="Small" size="sm" onPress={handlePress} />
<Button title="Medium" size="md" onPress={handlePress} />
<Button title="Large" size="lg" onPress={handlePress} />

// Loading state
<Button title="Submit" loading={isLoading} onPress={handleSubmit} />

// Full width
<Button title="Sign In" fullWidth onPress={handleLogin} />
```

### Card Component

Container with shadow, padding, and optional header/footer.

```tsx
import { Card } from '@/components/ui';

// Basic card
<Card>
  <Text>Card content</Text>
</Card>

// With header
<Card header="Bot Status">
  <Text>Running</Text>
</Card>

// Custom header component
<Card header={<CustomHeader />}>
  <Text>Content</Text>
</Card>

// With footer
<Card 
  header="Statistics"
  footer={<Button title="Refresh" size="sm" />}
>
  <Text>Stats here</Text>
</Card>

// No padding (for custom layouts)
<Card noPadding>
  <Image source={...} style={{ width: '100%' }} />
</Card>
```

### Input Component

TextInput wrapper with label, validation, and icons.

```tsx
import { Input } from '@/components/ui';
import { Controller } from 'react-hook-form';

// Basic input
<Input
  label="Username"
  placeholder="Enter username"
  value={username}
  onChangeText={setUsername}
/>

// With validation error
<Input
  label="Email"
  placeholder="Enter email"
  value={email}
  onChangeText={setEmail}
  error={errors.email?.message}
/>

// With icons
<Input
  label="Username"
  leftIcon="person-outline"
  value={username}
  onChangeText={setUsername}
/>

// Password input (auto-shows eye icon)
<Input
  label="Password"
  placeholder="Enter password"
  value={password}
  onChangeText={setPassword}
  secureTextEntry
  leftIcon="lock-closed-outline"
/>

// With react-hook-form
<Controller
  control={control}
  name="username"
  render={({ field: { onChange, onBlur, value } }) => (
    <Input
      label="Username"
      value={value}
      onChangeText={onChange}
      onBlur={onBlur}
      error={errors.username?.message}
    />
  )}
/>
```

### Badge Component

Small colored label for status indicators.

```tsx
import { Badge } from '@/components/ui';

// With variants
<Badge label="Success" variant="success" />
<Badge label="Warning" variant="warning" />
<Badge label="Error" variant="error" />
<Badge label="Info" variant="info" />
<Badge label="Default" variant="default" />

// With sizes
<Badge label="Small" size="sm" />
<Badge label="Medium" size="md" />
<Badge label="Large" size="lg" />

// In context
<View style={{ flexDirection: 'row', alignItems: 'center' }}>
  <Text>Bot Status: </Text>
  <Badge 
    label={isRunning ? 'RUNNING' : 'STOPPED'} 
    variant={isRunning ? 'success' : 'error'} 
  />
</View>
```

### LoadingSkeleton Component

Animated placeholder for loading states.

```tsx
import { LoadingSkeleton, SkeletonText, SkeletonCard } from '@/components/ui';

// Basic skeleton
<LoadingSkeleton width={200} height={20} />

// Full width
<LoadingSkeleton width="100%" height={40} />

// Custom border radius
<LoadingSkeleton width={100} height={100} borderRadius={50} />

// Multiple lines of text
<SkeletonText lines={3} />

// Card skeleton
<SkeletonCard />

// In a loading state
{isLoading ? (
  <SkeletonCard />
) : (
  <Card header="Data">
    <Text>{data.content}</Text>
  </Card>
)}
```

### ErrorBoundary Component

Catches React errors and displays fallback UI.

```tsx
import { ErrorBoundary } from '@/components/ErrorBoundary';

// Wrap any component
<ErrorBoundary>
  <YourComponent />
</ErrorBoundary>

// Custom fallback
<ErrorBoundary
  fallback={(error, resetError) => (
    <View>
      <Text>Custom error: {error.message}</Text>
      <Button title="Retry" onPress={resetError} />
    </View>
  )}
>
  <YourComponent />
</ErrorBoundary>
```

## 🎨 Theme System

The app supports light and dark themes with seamless switching.

### Using Theme

```tsx
import { useTheme } from '@/context/ThemeContext';

function MyComponent() {
  const { theme, toggleTheme, themeMode, setThemeMode } = useTheme();

  return (
    <View style={{ backgroundColor: theme.colors.background }}>
      <Text style={{ color: theme.colors.text }}>Hello</Text>
      <Button title="Toggle Theme" onPress={toggleTheme} />
    </View>
  );
}
```

### Theme Properties

```tsx
// Colors
theme.colors.primary
theme.colors.background
theme.colors.surface
theme.colors.text
theme.colors.textSecondary
theme.colors.border
theme.colors.error
theme.colors.success
theme.colors.warning
theme.colors.info

// Spacing
theme.spacing.xs  // 4
theme.spacing.sm  // 8
theme.spacing.md  // 16
theme.spacing.lg  // 24
theme.spacing.xl  // 32

// Border radius
theme.borderRadius.sm   // 4
theme.borderRadius.md   // 8
theme.borderRadius.lg   // 12
theme.borderRadius.full // 9999

// Typography
theme.typography.fontSizes.xs    // 12
theme.typography.fontSizes.md    // 16
theme.typography.fontSizes.xl    // 20
theme.typography.fontWeights.regular
theme.typography.fontWeights.bold

// Shadows
theme.shadows.sm
theme.shadows.md
theme.shadows.lg
```

## 🔔 Toast Notifications

Display temporary messages to users.

```tsx
import { useToast } from '@/context/ToastContext';

function MyComponent() {
  const { showToast } = useToast();

  const handleSuccess = () => {
    showToast('Operation successful!', 'success');
  };

  const handleError = () => {
    showToast('Something went wrong', 'error');
  };

  const handleInfo = () => {
    showToast('This is informational', 'info');
  };

  const handleWarning = () => {
    showToast('Warning message', 'warning');
  };

  // Custom duration (default 3000ms)
  const handleCustom = () => {
    showToast('Quick message', 'info', 1500);
  };

  return (
    <View>
      <Button title="Show Success" onPress={handleSuccess} />
      <Button title="Show Error" onPress={handleError} />
    </View>
  );
}
```

## ✅ Form Validation

Using react-hook-form with Zod schemas.

### Define Schema

```tsx
import { z } from 'zod';

const loginSchema = z.object({
  username: z.string().min(3, 'Username must be at least 3 characters'),
  password: z.string().min(6, 'Password must be at least 6 characters'),
});

type LoginFormData = z.infer<typeof loginSchema>;
```

### Use in Component

```tsx
import { useForm } from '@/hooks/useForm';
import { loginSchema, LoginFormData } from '@/utils/validation';
import { Controller } from 'react-hook-form';
import { Input, Button } from '@/components/ui';

function LoginForm() {
  const { control, handleSubmit, formState: { errors } } = useForm<LoginFormData>({
    schema: loginSchema,
    defaultValues: { username: '', password: '' },
  });

  const onSubmit = (data: LoginFormData) => {
    console.log(data); // Validated data
  };

  return (
    <View>
      <Controller
        control={control}
        name="username"
        render={({ field }) => (
          <Input
            label="Username"
            value={field.value}
            onChangeText={field.onChange}
            error={errors.username?.message}
          />
        )}
      />
      
      <Controller
        control={control}
        name="password"
        render={({ field }) => (
          <Input
            label="Password"
            value={field.value}
            onChangeText={field.onChange}
            error={errors.password?.message}
            secureTextEntry
          />
        )}
      />
      
      <Button
        title="Submit"
        onPress={handleSubmit(onSubmit)}
      />
    </View>
  );
}
```

## Environment Variables

- `EXPO_PUBLIC_API_URL` - Backend API base URL (default: http://localhost:8004/api/v1)

## API Integration

The app connects to the Market Bot API v1. There are no default credentials: sign in with
an account configured on the server (`ADMIN_USERNAME`/`ADMIN_PASSWORD` etc.) or a registered,
email-verified user. Bot start/stop and settings writes require an admin (DB user with role `admin`).

API features:
- JWT authentication with 24-hour token expiry
- Automatic token refresh on 401 responses
- Secure token storage in device keychain
- Rate limiting and error handling

## Scripts

```bash
npm start         # Start development server
npm run android   # Run on Android
npm run ios       # Run on iOS
npm run web       # Run on web
npm run lint      # Run ESLint
npm run type-check # Run TypeScript checks
npm test          # Run tests
```

## Troubleshooting

### Cannot connect to API

1. Ensure the backend API is running
2. Check your `.env.local` file has the correct `EXPO_PUBLIC_API_URL`
3. For physical devices, use your computer's IP address instead of `localhost`

### Build errors

1. Clear cache: `expo start -c`
2. Reinstall dependencies: `rm -rf node_modules && npm install`
3. Reset Metro bundler: `npx expo start --clear`

### Token expiry issues

Tokens expire after 24 hours. The app automatically refreshes tokens on 401 responses. If you see repeated login prompts, check the API server logs.

## Development Notes

- TypeScript strict mode is enabled - no `any` types allowed
- Path aliases configured: `@/*` maps to `src/*`
- All API calls use the centralized Axios client with interceptors
- Auth state managed by reducer pattern in AuthContext
- React Query handles data fetching, caching, and synchronization

## Contributing

1. Follow TypeScript strict typing
2. Use path aliases (`@/`) for imports
3. Test on both iOS and Android before committing
4. Keep dependencies up to date

## License

GPL-3.0. See the repository LICENSE.

## Support

For issues or questions, contact the development team.
