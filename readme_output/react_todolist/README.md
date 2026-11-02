# React Todo List

A modern, responsive Todo List application built with React and Vite.

## Live Demo

**[to-do-list-tau-three-67.vercel.app](https://to-do-list-tau-three-67.vercel.app)**

## Features

- Add, edit, delete tasks
- Mark tasks as complete/incomplete
- Filter tasks (All, Active, Completed)
- Clear completed tasks
- Task counter
- Persistent storage (localStorage)
- Responsive design
- Keyboard shortcuts

## Tech Stack

- **Framework**: React 18
- **Build Tool**: Vite
- **Styling**: CSS3 / CSS Modules
- **State Management**: React Hooks (useState, useEffect)
- **Persistence**: localStorage
- **Deployment**: Vercel
- **Linting**: ESLint

## Project Structure

```
react_todolist/
├── public/                 # Static assets
├── src/
│   ├── components/
│   │   ├── TodoApp.jsx     # Main todo component
│   │   ├── TodoForm.jsx    # Add/edit task form
│   │   ├── TodoItem.jsx    # Individual task item
│   │   ├── TodoFilter.jsx  # Filter buttons
│   │   └── TodoStats.jsx   # Task counter
│   ├── hooks/
│   │   └── useTodos.js     # Custom hook for todo logic
│   ├── App.jsx             # Root component
│   ├── main.jsx            # Entry point
│   └── index.css           # Global styles
├── index.html
├── package.json
├── vite.config.js
├── eslint.config.js
└── README.md
```

## Getting Started

### Prerequisites

- Node.js 18+
- npm

### Installation

```bash
cd react_todolist
npm install
```

### Development

```bash
npm run dev
```

Runs at `http://localhost:5173`

### Build for Production

```bash
npm run build
```

### Preview Production Build

```bash
npm run preview
```

## Usage

1. Type a task in the input field
2. Press Enter or click "Add" to create task
3. Click checkbox to toggle completion
4. Click edit icon to modify task
5. Click delete icon to remove task
6. Use filter buttons to view All/Active/Completed
7. Click "Clear Completed" to remove finished tasks

## Keyboard Shortcuts

- `Enter` - Add new task / Save edit
- `Escape` - Cancel edit
- `Ctrl/Cmd + Enter` - Toggle completion (when focused)

## Data Persistence

Tasks are automatically saved to `localStorage` and restored on page load.

## Available Scripts

| Command | Description |
|---------|-------------|
| `npm run dev` | Start development server |
| `npm run build` | Build for production |
| `npm run preview` | Preview production build |
| `npm run lint` | Run ESLint |

## Deployment

### Vercel (Current)

1. Push to GitHub
2. Import in Vercel
3. Auto-deploys on push to main

### Other Platforms

Deploy `dist/` folder to any static hosting (Netlify, GitHub Pages, etc.)

## Future Enhancements

- [ ] Due dates and reminders
- [ ] Categories/tags
- [ ] Drag-and-drop reordering
- [ ] Dark mode
- [ ] Sync with backend API
- [ ] PWA support
- [ ] Unit tests

## License

MIT License