# Image Direction

The frame should feel like a quiet wall object, not a slideshow and not a tech demo.

## Core visual rule
Generate images in small coherent series, then curate hard.

Avoid:
- glossy AI fantasy art
- cinematic poster compositions
- obvious sci-fi concept art
- neon saturation
- text, logos, signatures, captions
- people, faces, hands, mascot energy
- busy compositions

Prefer:
- quiet negative space
- archival or photographic texture
- muted palettes
- weather, sea, empty rooms, field notes, distant signals
- images that can sit on a wall for hours without shouting

## Prompt families

### Weather memory
Archival-feeling seascapes, fog, storms, distant lights, low cloud, rain.

Example prompt:

```text
an archival photograph of a quiet storm over a dark sea, distant horizon, soft mist, muted palette, restrained composition, large areas of negative space, aged paper texture, natural grain, no people, no text, museum print
```

### Impossible field notes
Scientific plates of things that do not quite exist.

Example prompt:

```text
a vintage scientific field plate of an unknown deep sea botanical specimen, ink and faded watercolor, off white paper, precise but slightly uncanny, sparse annotations removed, centered composition, natural imperfections, no text
```

### Empty architecture
Rooms, corridors, windows, stairwells, quiet structures.

Example prompt:

```text
a quiet empty room at dusk, one tall window, soft indirect light, old plaster walls, minimal composition, muted colors, contemplative atmosphere, medium format photograph, no people, no furniture clutter, no text
```

### Night signals
Distant towers, windows, small lights, fog, vacant land.

Example prompt:

```text
a distant radio tower in fog at night, small red signal light, empty landscape, dark blue gray palette, long exposure feeling, quiet negative space, photographic grain, no people, no text
```

## Negative prompt baseline

```text
text, words, logo, watermark, signature, people, face, hands, animals, anime, cartoon, glossy, oversaturated, neon, fantasy armor, dramatic explosion, cinematic poster, sharp digital artifacts, bad anatomy, duplicate objects, cluttered composition
```

## Curation rule
Generate batches of 4-8 images per prompt. Keep at most one or two. Most generated images should be rejected.

## Frame-ready process
1. Generate source images at 4:3 or close to 4:3.
2. Save promising originals into `artpack/inbox/`.
3. Register selected images with `scripts/add_image.py`.
4. Commit the panel-ready PNG and manifest update.

Examples:

```bash
python scripts/add_image.py artpack/inbox/weather_01.png --mode color --copy-source
python scripts/add_image.py artpack/inbox/field_note_01.png --mode monochrome --copy-source
```
