# Sylvan Library frontend

The React app for Sylvan Library. It's a single-page app using React Router, and gets
all its data from the Django REST API.

Needs Node 20.19 or newer.

## Development

```bash
npm install
npm run dev
```

Then open http://localhost:5173/. Vite passes API, admin and static requests on to
Django at http://localhost:8000 (or `DJANGO_BACKEND`), so run `manage.py runserver` as
well.

## Building

```bash
npm run build
```

This builds the app and copies it into `sylvan_library/frontend/static/react/`, where
Django serves it when not in debug mode.

## Other commands

- `npm run typecheck` checks the TypeScript
- `npx prettier --write .` formats the code
