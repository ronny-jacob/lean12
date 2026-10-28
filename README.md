# Lean 12 training log

A phone-first web app for a 12-week, 3-day-a-week plan built on dumbbells and stack machines. It shows today's
workout with pictures and cues, logs each set, tells you when to add load, tracks weight, food and steps, and
runs a weekly check-in. It runs entirely in the browser: no server, no account.

**Your data never leaves your phone.** Logs live in the browser's local storage. Use **Data > Copy backup** now
and then. Clearing browser data, switching browsers or using a private tab erases them. On iPhone, the Home Screen
app and Safari keep separate data, so install first, then log.

## Deploy on GitHub Pages (about 5 minutes)

1. Create a new repository (for example `lean12`). Public is required for free GitHub Pages.
2. Upload everything in this folder to the repository root: `index.html`, `manifest.webmanifest`, `sw.js`,
   `.nojekyll`, the `icons` folder and (optionally) `tests`. Web route: **Add file > Upload files**, drag the files and
   folders in, then **Commit changes**.
3. **Settings > Pages > Build and deployment**: Source *Deploy from a branch*, Branch `main`, folder `/ (root)`, **Save**.
4. After a minute or two the site is live at `https://<your-username>.github.io/<repo>/`.
5. Open it on your phone and choose **Add to Home Screen**. After the first load it also works offline.

## Updating

Replace `index.html` (and any other changed file), then change `CACHE` in `sw.js` (for example `lean12-v4`) so phones
pick up the new version. Because the worker tries the network first, an online phone usually updates on the next open anyway.

## Tests

`tests/smoke_test.py` drives the app in a phone-sized browser: workout flow, progression cues, focus handling,
corrupt-data recovery, backups, tap-target size, 200% zoom and (with axe-core installed) an accessibility scan.

```
pip install playwright && playwright install chromium
npm install axe-core            # optional, enables the accessibility checks
AXE_PATH=node_modules/axe-core/axe.min.js python3 tests/smoke_test.py index.html
```

## Privacy and search engines

The page asks search engines not to index it (`noindex`). The defaults in the code (75 kg start weight, 168 cm height,
68 kg goal) are visible in a public repository. Change them in **Data > Settings** or edit them before publishing.

## Credits and licence notes

- Exercise pictures: Exercise data by [RepDB](https://repdb.co), used under RepDB's free tier (in-app use with visible
  attribution). The pictures are embedded inside `index.html` as part of the app. Do not extract or republish them as a
  separate image set or dataset; the RepDB terms do not allow that. Terms: https://github.com/RepDB/exercise-dataset
- The app code and plan text are yours to use and change.
- General fitness guidance, not medical advice. See a physiotherapist or doctor for injury or health concerns.
