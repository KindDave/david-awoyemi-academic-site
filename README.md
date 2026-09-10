# CV Automation

This project turns `David_CV.docx` into a static academic website.

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

## Publishing an updated CV (one click)

Double-click `Publish CV to website.bat` in the project folder. It finds the
newest `David_CV.docx` under your job-materials folder, shows which sections
and homepage metrics would change, asks for confirmation, then copies the CV
into the repository, rebuilds the pages, commits, and pushes. GitHub Actions
deploys the site about a minute later.

- To publish a specific file instead, drop the `.docx` onto the `.bat` file.
- The job-materials folder is set in `scripts/sync_cv.config.json` (kept out
  of git). Set `"strip_phone": true` there to remove the phone number from the
  published copy only.
- From a terminal: `python scripts/sync_cv.py --dry-run` previews without
  changing anything; `--yes` skips the prompt; `--no-push` commits locally.

## Suggested update loop

1. Edit `David_CV.docx`.
2. Run `python scripts/build_site.py`.
3. Review `index.html`.
4. Commit the changes.
5. Push to GitHub.
6. Let GitHub Pages redeploy the site.
