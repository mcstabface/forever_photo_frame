# forever_photo_frame

Deterministic e-ink art frame project built around a Raspberry Pi and a 13.3 inch Spectra 6 display.

## Concept
The frame reveals one image into the next over time instead of swapping instantly. Internal progress advances continuously. The physical display refreshes in batches to manage e-ink behavior.

## Hardware
- Raspberry Pi Zero 2 W
- Pimoroni Inky Impression 13.3 inch Spectra 6
- preprocessed image pack
- custom wood enclosure

## Project structure
- `app/` runtime code
- `artpack/` images, manifest, transitions
- `docs/` architecture notes
- `scripts/` utility and preprocessing scripts
- `tests/manual/` manual test scripts
- `state/` runtime state on device

## Current status
- display hardware working
- manifest-driven image loading working
- persisted state and resume working
- sweep and random transition paths in progress
- batched refresh model confirmed

## Notes
This project is intentionally deterministic and offline-friendly.