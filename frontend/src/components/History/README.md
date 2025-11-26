# History Component

## Overview

The History component displays a list of past verification sessions, allowing users to review and reload previous fact-checks. It implements all requirements from Task 17 of the KEPLER Web Interface specification.

## Features

### Core Functionality
- **Display Past Verifications**: Shows a list of all past verification sessions from localStorage
- **Truncated Claim Text**: Displays claim text truncated to 80 characters for readability
- **Verdict Display**: Shows the verdict with color-coded badges (Supported/Refuted/Not Enough Information)
- **Timestamp Formatting**: Displays human-readable timestamps (e.g., "Nov 25, 2025 at 3:45 PM")
- **Confidence Score**: Shows the confidence percentage for each verification
- **Item Interaction**: Click any history item to reload and display its full results
- **Clear History**: Button to clear all history with confirmation dialog
- **Collapsible Panel**: Can be collapsed to save screen space
- **localStorage Persistence**: Automatically saves and loads history from browser storage

### Requirements Satisfied
- **13.1**: History tracking and localStorage persistence
- **13.2**: Display claim text for each verification
- **13.3**: Display verdict for each verification
- **13.4**: Display timestamp for each verification
- **13.5**: Load full results when clicking history items

## Components

### History.tsx
Main container component that manages the history panel.

**Props:**
- `history: HistoryItemData[]` - Array of history items to display
- `onItemClick: (item: HistoryItemData) => void` - Callback when user clicks a history item
- `onClearHistory: () => void` - Callback when user clears all history

**Features:**
- Collapsible sidebar design
- Empty state message when no history exists
- Clear all button with confirmation
- Responsive design for mobile devices

### HistoryItem.tsx
Individual history item component.

**Props:**
- `item: HistoryItemData` - The history item data to display
- `onClick: () => void` - Callback when item is clicked

**Features:**
- Truncates long claim text to 80 characters
- Color-coded verdict badges
- Formatted timestamps
- Confidence score display
- Hover and focus states for accessibility

## Data Structure

```typescript
interface HistoryItemData {
  sessionId: string;           // Unique session identifier
  timestamp: string;            // ISO timestamp string
  claimText: string;            // Original claim text
  verdict: string;              // Verdict classification
  confidence: number;           // Confidence score (0-1)
  fullResults: VerificationResult; // Complete verification results
}
```

## Usage

```tsx
import { History } from './components/History';
import type { HistoryItemData } from './components/History';

function App() {
  const [history, setHistory] = useState<HistoryItemData[]>([]);

  const handleItemClick = (item: HistoryItemData) => {
    // Load the full results
    console.log('Loading results for:', item.sessionId);
  };

  const handleClearHistory = () => {
    setHistory([]);
  };

  return (
    <History
      history={history}
      onItemClick={handleItemClick}
      onClearHistory={handleClearHistory}
    />
  );
}
```

## Styling

The component uses CSS modules with the following files:
- `History.css` - Main panel styles
- `HistoryItem.css` - Individual item styles

### Color Scheme
- **Supported**: Green (#d1e7dd background, #0f5132 text)
- **Refuted**: Red (#f8d7da background, #842029 text)
- **Not Enough Information**: Yellow (#fff3cd background, #664d03 text)

### Responsive Behavior
- **Desktop (>1024px)**: Fixed sidebar on the right (320px width)
- **Tablet (768-1024px)**: Collapsible sidebar
- **Mobile (<768px)**: Overlay panel with toggle button

## Accessibility

- Semantic HTML with proper ARIA labels
- Keyboard navigation support
- Focus indicators on interactive elements
- Screen reader friendly
- Reduced motion support for animations

## Integration with App

The History component is integrated into the main App component:

1. App maintains history state in localStorage
2. When verification completes, App adds item to history
3. History component displays all items
4. When user clicks item, App loads the full results
5. When user clears history, App removes all items

## Example

See `History.example.tsx` for a complete working example with sample data.

## Files

- `History.tsx` - Main component
- `HistoryItem.tsx` - Item component
- `History.css` - Panel styles
- `HistoryItem.css` - Item styles
- `index.ts` - Exports
- `History.example.tsx` - Usage example
- `README.md` - This file
