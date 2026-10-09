# Icon asset matrix

Every asset an Android-first Expo app needs from one drawing, and the rule behind each. Specs as of *(checked 2026-10)*; confirm sizes against current Android, Expo and Play docs before rendering. Use the full mark at large sizes and the reduced-detail one below about 64px.

| Asset | Size | Rule |
|---|---|---|
| Launcher icon | 1024 | Full mark on the tile |
| Adaptive foreground | 1024 canvas | Android shows the inner 72dp of a 108dp canvas, so scale the glyph by 72/108 relative to the plain icon to land in the same place |
| Adaptive background | 1024 | Flat colour, not a tint that fights the mark |
| Monochrome (themed icon) | 1024 | Alpha silhouette only; the system recolours it. Cuts in one colour become holes, so fine detail goes |
| Notification icon | 96 | White on transparent; Android masks it to one colour |
| Splash image | per splash config | The native splash contains the image in a square, so a non-square glyph renders smaller than the number. Match the JS overlay to the rendered size |
| Favicon | 196 | Reduced-detail mark |
| Web app icons | 512 | Manifest and Apple touch icon |
| Lockups | SVG | Mark plus wordmark, horizontal and stacked, light and dark |
| Logo kit | SVG + PNG | Lockups, bare mark, square icon, a rounded icon for places that do not mask |
| Store listing icon | 512 | RGB, no alpha. Uploaded separately (`play.py icon`) |

Checks before shipping a new mark:

- The 16px favicon still reads.
- The themed icon on a light and a dark wallpaper.
- The adaptive icon under circle, squircle and teardrop masks, nothing clipped.
- Native splash and JS overlay match to the pixel on a real phone; screenshot both frames.
