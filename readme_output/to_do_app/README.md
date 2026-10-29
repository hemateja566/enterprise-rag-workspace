# Todo App (Vanilla JS)

A simple, lightweight Todo List application built with vanilla HTML, CSS, and JavaScript.

## Features

- Add, edit, delete tasks
- Mark tasks as complete/incomplete
- Filter tasks (All, Active, Completed)
- Clear completed tasks
- Task counter
- Data persistence using localStorage
- Clean, minimal UI
- No dependencies

## Project Structure

```
to_do_app/
├── index.html      # Main HTML structure
├── script.js       # Application logic
├── style.css       # Styling (embedded or separate)
└── README.md
```

## Getting Started

### Installation

No installation required. Just open `index.html` in any modern browser.

```bash
# Clone repository
git clone https://github.com/hemateja566/to_do_app.git

# Open in browser
open index.html  # macOS
start index.html # Windows
xdg-open index.html # Linux
```

## Usage

1. Enter a task in the input field
2. Click "Add" or press Enter
3. Click checkbox to mark complete
4. Double-click task text to edit
5. Click delete button to remove
6. Use filter tabs to view different states
7. Click "Clear Completed" to remove finished tasks

## Data Persistence

Tasks are saved to browser's `localStorage` automatically. Data persists across browser sessions.

## JavaScript API (script.js)

```javascript
// TodoApp class with methods:
todoApp.addTask(text)
todoApp.deleteTask(id)
todoApp.toggleTask(id)
todoApp.editTask(id, newText)
todoApp.clearCompleted()
todoApp.setFilter(filter) // 'all', 'active', 'completed'
todoApp.getTasks()
```

## Browser Support

- Chrome 60+
- Firefox 55+
- Safari 11+
- Edge 79+

## Customization

Edit `style.css` to customize:
- Colors (CSS variables at top)
- Spacing, typography
- Animations
- Responsive breakpoints

## Future Enhancements

- [ ] Due dates
- [ ] Categories/tags
- [ ] Drag-and-drop reordering
- [ ] Dark mode toggle
- [ ] Export/import data
- [ ] Keyboard shortcuts

## License

MIT License