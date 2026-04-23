# CV Automation

This project turns `CV_David.docx` into a static academic website.

## Source of truth

The Word document is the content source. The build script reads the `.docx` directly and regenerates:

- `index.html`
- `site-data.json`
- `dist/` for GitHub Pages deployment

## Local rebuild

From this folder, run:

```powershell
python scripts/build_site.py
```

Then open `index.html` locally to review the regenerated site.

## GitHub workflow

1. Create a new GitHub repository.
2. Initialize or connect this folder to that repository.
3. Push the `main` branch.
4. GitHub Actions will run `.github/workflows/deploy.yml`.
5. GitHub Pages will publish the contents of `dist/`.

## Suggested update loop

1. Edit `CV_David.docx`.
2. Run `python scripts/build_site.py`.
3. Review `index.html`.
4. Commit the changes.
5. Push to GitHub.
6. Let GitHub Pages redeploy the site.
