# Portfolio

Christopher Naglik's game programming portfolio, featuring **Champions Arena**. Built with [Astro](https://astro.build) and deployed to GitHub Pages.

## Editing content

- **System deep dives:** `src/content/systems/*.md`. One Markdown file per page. The front matter at the top holds the title, summary, tags, "At a glance" bullets and key files; the body holds the sections.
- **Links, email, trailer:** `src/config.ts`.
- **Images/GIFs/CV:** put them in `public/` (e.g. `public/media/combo.gif`, `public/cv.pdf`) and reference them as `/portfolio/media/combo.gif`.
- **Code links:** write function names as `[\`DetermineRoundWinner\`](code:AChrisGameMode::DetermineRoundWinner)` (or just a class/struct name, e.g. `code:FPlayerSelection`). Then, with the game repo checked out at a release tag, run `python3 scripts/gen-code-refs.py <path-to-game-repo>` to refresh `src/data/code-refs.json`. The build fails if a symbol can't be found.
- Set `status: ready` on a system page to remove the "work in progress" banner.

## Run locally (optional)

```
npm install
npm run dev
```

Every push to `main` rebuilds and redeploys the site automatically.
