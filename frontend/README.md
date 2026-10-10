# Market Pie5 Bot - React Frontend

Modern React frontend for Market Pie5 Trading Bot.

## Setup Instructions

### Prerequisites
- Node.js 18+ 
- npm or yarn

### Installation

1. **Create React app (if not already created):**
   ```bash
   npm create vite@latest . -- --template react-ts
   ```

2. **Install dependencies:**
   ```bash
   npm install
   ```

3. **Install UI libraries:**
   ```bash
   npm install -D tailwindcss postcss autoprefixer
   npm install @tanstack/react-query axios zustand
   npx tailwindcss init -p
   ```

4. **Set up Shadcn/ui:**
   ```bash
   npx shadcn-ui@latest init
   ```

5. **Start development server:**
   ```bash
   npm run dev
   ```

## Project Structure

```
frontend/
├── src/
│   ├── components/     # Reusable components
│   ├── pages/          # Page components
│   ├── api/            # API client functions
│   ├── store/          # State management (Zustand)
│   ├── lib/            # Utilities
│   └── App.tsx         # Main app component
├── public/              # Static assets
└── package.json         # Dependencies
```

## API Connection

The frontend connects to the FastAPI backend at:
- Development: `http://localhost:8000`
- Production: Configure via environment variables

## Available Scripts

- `npm run dev` - Start development server
- `npm run build` - Build for production
- `npm run preview` - Preview production build
