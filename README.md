# Mini-Palletizer Workshop — Companion Repo

Clone-able helpers, reference code, config, and a printable template for the
**Miniature Palletizing with the SO-ARM101** workshop: teach an affordable
desktop arm where the cubes and pallet are by hand, then write the Python that
packs a two-by-two-by-two stack of cubes on its own.

This repo holds the supplemental assets the workshop links to. Follow the
step-by-step tutorial in the Viam docs:

> **Tutorial:** [Miniature Palletizing with the SO-ARM101](https://docs.viam.com/tutorials/so-arm101-palletizing/)
> *(link goes live when the workshop ships)*

You don't need to read this repo cover to cover. The tutorial tells you which
file to grab at each phase.

---

## What's here

```
mini-palletizer/
├── helpers.py                    # provided plumbing you import from palletizer.py
├── reference/
│   └── palletizer.py             # the finished script the tutorial builds (check your work)
├── config/
│   └── machine-fragment.json     # arm + gripper + frames, for checking your config by hand
├── template/
│   ├── cube-and-pallet-template.pdf   # print at 100%: fold-up cubes + pallet mat
│   └── generate_template.py           # regenerates the PDF (uv run --with reportlab ...)
├── pyproject.toml                # uv project, declares viam-sdk
└── .python-version               # pins Python 3.11
```

You write `palletizer.py` yourself in the repo root as you work through the
phases; `helpers.py` is provided so you import the connection and grid math
instead of rewriting them.

## Hardware

| Item | Role |
|---|---|
| SO-ARM101 arm + finger gripper | picks and stacks the cubes; connects over USB serial |
| Eight ~20 mm cubes | what gets packed (fold the template, or use wooden/foam cubes) |
| Pallet mat + staging spot | where cubes get stacked and fed from (print the template) |
| Personal computer | runs `viam-server` and your Python |

## Getting started

1. **Clone and enter the project:**

   ```sh
   git clone https://github.com/viam-devrel/mini-palletizer.git
   cd mini-palletizer
   ```

2. **Print the template** at `template/cube-and-pallet-template.pdf` at 100%
   scale (turn off "fit to page"), then fold eight cubes and cut out the pallet
   mat. Wooden or foam 20 mm cubes work too.

3. **Add your machine credentials and taught poses** to `helpers.py`: paste the
   machine address and API key/ID from your machine's CONNECT tab, and the two
   anchor poses you read off the arm's test card in Phase 3.

4. **Run a step** (uv installs `viam-sdk` on first run):

   ```sh
   uv run palletizer.py move    # send the gripper to a safe pose
   uv run palletizer.py pick    # pick one hand-fed cube
   uv run palletizer.py pack    # the static bottom-layer pack (default)
   ```

   To check your work against the finished version, run
   `uv run reference/palletizer.py <step>`.

## Notes

- `config/machine-fragment.json` mirrors the end state of Phase 2 (arm at the
  world origin, gripper parented to the arm). Replace `REPLACE_WITH_ARM_PORT`
  with your serial port. Use it to check your config; the tutorial has you
  configure resources by hand with the discovery service.
- The template dimensions (`CUBE = 20 mm`, `PITCH = 30 mm`) match the constants
  in the code. If you change one, change the other, and regenerate the PDF with
  `uv run --with reportlab python template/generate_template.py`.
- Never commit real credentials. `helpers.py` ships with placeholders; keep it
  that way in any fork.
