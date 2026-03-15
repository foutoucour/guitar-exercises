# guitar-exercises

Multiple exercises to improve your knowledge of guitar.

## Local development

```bash
npm install
npm run dev
```

The app runs at `http://localhost:5173`.

```bash
npm test        # run unit tests
npm run build   # production build (output in dist/)
```

## Deploy to GitHub Pages

The repo includes a GitHub Actions workflow that builds and deploys automatically on every push to `main`.

**One-time setup:**

1. Go to your repo on GitHub → **Settings** → **Pages**
2. Under _Source_, select **GitHub Actions**
3. Push to `main` — the workflow will build and publish the site

The live URL will be `https://<your-username>.github.io/guitar-exercises/`.

> If your repo is named differently, update the `base` path in `vite.config.ts` to match.
