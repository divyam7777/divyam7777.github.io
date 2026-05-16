# Divyam Matia Portfolio

React + Vite portfolio site prepared for GitHub Pages deployment.

## Replace before publishing

- `public/profile-placeholder.jpg` with your portrait
- `public/Divyam_Matia_Resume.pdf` with your resume
- Placeholder email in `src/content.js`
- Project entries, certifications, and achievements in `src/content.js`

## Run locally

```bash
npm install
npm run dev
```

## Build

```bash
npm run build
```

## GitHub Pages deployment

This project includes a GitHub Actions workflow that builds the React app and publishes the `dist` folder to GitHub Pages on every push to `main`.

In the GitHub repository settings:

1. Open **Settings → Pages**
2. Under **Build and deployment**, choose **GitHub Actions**
3. Push the repository to the `main` branch
