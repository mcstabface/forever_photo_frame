# forever_photo_frame architecture

## Core idea
A deterministic e-ink art frame that reveals one image into another over time.

## Current behavior
- images are pre-generated and preloaded
- manifest-driven image selection
- color and monochrome modes alternate
- transitions are defined in JSON
- hidden progress advances every tick
- physical e-ink refresh happens in batches
- state is persisted for restart recovery

## Runtime model
1. load current image
2. choose next image
3. choose transition
4. mutate one pixel per tick in memory
5. refresh display every N ticks
6. persist state for clean resume
7. on completion, promote next image to current and select the next cycle

## Current transition support
- sweep
- random

## Important constraint
The display performs visible full refresh behavior, so internal progression and physical refresh cadence are intentionally decoupled.