# KEPLER Web Interface

A responsive web application for interacting with the KEPLER fact-verification system.

## Features

- Submit text claims for verification
- Upload images for multimodal verification
- Select multiple language models for verification
- View detailed verification results including:
  - Verdict classification with confidence scores
  - Evidence sources with credibility ratings
  - Step-by-step reasoning chain
  - Individual model verdicts
  - Atomic claim decomposition
- Export results as JSON or PDF
- View verification history
- Responsive design for desktop, tablet, and mobile

## Technology Stack

- **Framework**: React 18 with TypeScript
- **Build Tool**: Vite
- **HTTP Client**: Axios
- **Styling**: CSS3 with CSS Modules

## Getting Started

### Prerequisites

- Node.js 18+ and npm

### Installation

1. Install dependencies:
```bash
npm install
```

2. Configure environment variables:
```bash
cp .env.example .env
```

Edit `.env` and set the API URL:
```
VITE_API_URL=http://localhost:8000
```

### Development

Start the development server:
```bash
npm run dev
```

The application will be available at `http://localhost:5173`

### Building for Production

Build the application:
```bash
npm run build
```

Preview the production build:
```bash
npm run preview
```

## Project Structure

```
frontend/
├── src/
│   ├── components/
│   │   ├── InputForm/      # Input components (ClaimInput, ImageUpload, ModelSelector)
│   │   ├── Results/        # Results display components
│   │   ├── Common/         # Shared components (LoadingIndicator, ErrorMessage)
│   │   ├── History/        # History components
│   │   └── Export/         # Export functionality
│   ├── services/
│   │   └── api.ts          # API client functions
│   ├── utils/
│   │   ├── validation.ts   # Input validation utilities
│   │   └── formatting.ts   # Data formatting utilities
│   ├── App.tsx             # Main application component
│   ├── App.css             # Application styles
│   ├── main.tsx            # Application entry point
│   └── index.css           # Global styles
├── public/                 # Static assets
├── .env                    # Environment variables
└── package.json            # Dependencies and scripts
```

## API Integration

The frontend communicates with the KEPLER REST API backend. The API base URL is configured via the `VITE_API_URL` environment variable.

### API Endpoints Used

- `POST /api/verify` - Submit verification request
- `GET /api/models` - Get available LLM models
- `GET /api/health` - Check API health status

## Development Guidelines

### Code Style

- Use TypeScript for type safety
- Follow React best practices and hooks patterns
- Use functional components with hooks
- Keep components small and focused
- Extract reusable logic into custom hooks

### Component Organization

- Place related components in the same directory
- Co-locate component-specific styles
- Use descriptive component and prop names
- Document complex components with JSDoc comments

### State Management

- Use React hooks (useState, useEffect) for local state
- Consider Context API for shared state if needed
- Keep state as close to where it's used as possible

## Testing

Tests will be added in future tasks using:
- Jest for unit testing
- React Testing Library for component testing
- Property-based testing with fast-check

## Accessibility

The application follows accessibility best practices:
- Semantic HTML elements
- ARIA labels for interactive elements
- Keyboard navigation support
- Focus indicators
- Color contrast ratios ≥ 4.5:1

## Browser Support

- Chrome/Edge (latest)
- Firefox (latest)
- Safari (latest)
- Mobile browsers (iOS Safari, Chrome Mobile)

## License

Part of the KEPLER fact-verification system.
