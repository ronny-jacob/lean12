# Lean 12 training log

A phone-first web app for a 12-week full-body training plan: today's workout with exercise pictures and cues,
a set logger with automatic "add load" cues, a daily log (weight, food and protein, steps, sleep), weekly check-ins
and a progress view. It runs entirely in the browser. There is no server and no account.

**Your data never leaves your phone.** Logs are stored in the browser's local storage on the device you use.
Use **Data > Copy backup** now and then and paste it into a note. Clearing browser data, switching browsers or using
a private tab erases the logs.

## Deploy on GitHub Pages

1. Create a new repository on github.com (for example `lean12`). Public is required for free GitHub Pages.
2. Upload every file in this folder to the repository root: `index.html`, `manifest.webmanifest`, `sw.js`,
   `.nojekyll` and the `icons` folder. On the web: **Add file > Upload files**, drag them in, then **Commit changes**.
3. Open **Settings > Pages**. Under *Build and deployment*, set **Source** to *Deploy from a branch*,
   **Branch** `main`, folder `/ (root)`, and **Save**.
4. After a minute or two the site is live at `https://<your-username>.github.io/<repo-name>/`.
5. Open that address on your phone and choose **Add to Home Screen** (iPhone: Share > Add to Home Screen; Android Chrome:
   menu > Add to Home screen / Install app). After the first load it also works offline.

## Updating

Replace `index.html` (and any other changed file) in the repository. Then bump the `CACHE` name in `sw.js`
(for example `lean12-v2`) so phones pick up the new version. Because the service worker is network-first, an online
phone usually gets the update on the next open anyway.

## Credits and licence notes

- Exercise pictures: Exercise data by [RepDB](https://repdb.co) (repdb.co), used under RepDB's free tier
  (in-app use with visible attribution). The pictures are embedded inside `index.html` as part of the app.
  Do not extract or republish them as a separate image set or dataset; the RepDB terms do not allow that.
  See https://github.com/RepDB/exercise-dataset for the terms.
- The app code and plan text are yours to use and change.
- This is general fitness guidance, not medical advice. See a physiotherapist or doctor for injury or health concerns.
