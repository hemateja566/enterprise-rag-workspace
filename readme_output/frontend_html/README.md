# Frontend HTML Practice

Collection of HTML/CSS frontend practice projects and page templates.

## Overview

This repository contains multiple HTML pages demonstrating frontend fundamentals: semantic HTML, CSS layout techniques, responsive design, and form handling.

## Pages

| File | Description |
|------|-------------|
| `index.html` | Main landing page |
| `home.html` | Home page template |
| `menu.html` | Navigation menu examples |
| `contact.html` | Contact form with validation |
| `register.html` | User registration form |

## Features Demonstrated

### HTML5 Semantics
- `<header>`, `<nav>`, `<main>`, `<section>`, `<article>`, `<aside>`, `<footer>`
- Proper heading hierarchy (h1-h6)
- Semantic form elements

### CSS Layout
- Flexbox for navigation and card layouts
- CSS Grid for page layouts
- CSS Custom Properties (variables)
- Media queries for responsiveness

### Forms
- Input types (text, email, tel, password, date, select)
- Client-side validation (HTML5 + JavaScript)
- Accessible labels and error messages
- Form submission handling

### Responsive Design
- Mobile-first approach
- Breakpoints: 480px, 768px, 1024px, 1200px
- Fluid typography with `clamp()`
- Flexible images

## Project Structure

```
frontend_html/
├── index.html      # Landing page
├── home.html       # Home template
├── menu.html       # Navigation patterns
├── contact.html    # Contact form
├── register.html   # Registration form
└── README.md
```

## Getting Started

```bash
git clone https://github.com/hemateja566/frontend_html.git
cd frontend_html

# Open any HTML file in browser
open index.html
```

## Page Details

### index.html
Landing page with hero, features, testimonials, footer.

### home.html
Clean home page template with sidebar layout.

### menu.html
Multiple navigation patterns:
- Horizontal navbar
- Hamburger menu (mobile)
- Dropdown menus
- Mega menu example

### contact.html
Contact form with:
- Name, email, subject, message
- HTML5 validation
- JavaScript enhancement
- Success/error states

### register.html
Registration form with:
- Username, email, password, confirm
- Real-time validation
- Password strength meter
- Terms acceptance

## CSS Architecture

```css
/* Variables */
:root {
  --primary: #2563eb;
  --secondary: #64748b;
  --spacing: 1rem;
  --radius: 0.5rem;
}

/* Reset & Base */
*, *::before, *::after { box-sizing: border-box; }

/* Layout */
.container { max-width: 1200px; margin: 0 auto; padding: 0 var(--spacing); }

/* Components */
.btn, .card, .form-group, .navbar { /* ... */ }

/* Utilities */
.visually-hidden, .sr-only { /* ... */ }
```

## Browser Support

- Chrome 88+
- Firefox 78+
- Safari 14+
- Edge 88+

## Learning Objectives

- Semantic HTML structure
- CSS layout (Flexbox, Grid)
- Responsive design principles
- Form accessibility
- CSS custom properties
- Mobile-first development

## License

MIT License - Free for learning and portfolio use