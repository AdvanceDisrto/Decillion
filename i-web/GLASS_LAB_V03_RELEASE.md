# i™ Direct-to-Glass Neural Screen / iCalculator v0.3

**Status:** Built and validated as a local downloadable Omni-Sync master website release; NOT deployed to the existing Render frontend. This branch tracks the release without altering `main` or the preview's existing assets.

## Release contents
The file `i-the-one-omnisync-glasslab-v0.3.zip` is attached in the ChatGPT conversation of Oct 15, 2026. Source files in its root: `glass-lab.js`, `index.html`, `app.js`, `sw.js`, `style.css`, `i-master-artwork.jpg`, `omnisync.js`, existing secure backend client, and tests.

- Original approved i™ master visual kept byte-for-byte; image SHA-256 `c4aae6d23088ef16f5aa6282ab8e66b171d90f70200aa0202fadc319d649a3ce`.
- The rejected white-and-blue GLB is **not** loaded.
- **Custom character pipeline:** four local archetypes, vector Buddy with two lowercase i eyes, and manual local `.glb` import; embedded animation clips can play when available.
- **MoCap simulation:** simulated walking pace, stride, drift, turn, start/pause/reset and actual browser frame telemetry. This is not true skeleton motion capture.
- **Optical reference:** adjustable phase, depth, scattering, specular, topology; ideal two-beam wave-intensity calculator; analytic and 721-sample phase sweep optimization.
- **Device calibration:** browser-reported pixel ratio and user-editable iPhone/Android/tablet/desktop/custom profiles. No real micro-prism or refractive sensor hardware accessed.
- **Environment:** explicit-permission camera luminance sampling and optional motion-sensor readout, all local.
- **Data:** finite 500-sample rolling telemetry; downloadable JSON; SHA-256 browser integrity receipt. No signature or chain proof.
- **No physical GPU bypass:** standard OLED/LCD glass cannot render without the ordinary graphics/display pipeline by a PWA. OFED hardware is a design hypothesis not installed on the user's phone.
- `node tests/test_glass_lab.mjs`: **PASS** (12 static/math assertions). `node --check app.js` and `node --check glass-lab.js`: PASS. Existing `pytest tests/test_package.py tests/test_omnisync.py`: 10 PASS. Browser visual automation unavailable in this execution environment.

## Publishing
Extract the attached ZIP on a GitHub-authenticated Windows machine and run the included `publish-to-render.ps1` only after reviewing it and confirming the assets. It is designed to archive the old preview and publish to the existing Render-tracked branch, without merging to main. Visual and interactive acceptance testing on physical iPhone/iPad/Desktop remains required.

The actual JavaScript source lives in the attached bundle. Do not treat this release note alone as a deployed feature or proof of optical hardware.
