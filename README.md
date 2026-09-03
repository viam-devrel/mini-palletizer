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
| Eight ~16 mm cubes | what gets packed (fold the template, or use wooden/foam cubes or dice) |
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
   mat and the staging square. Wooden or foam 16 mm cubes work too.

3. **Add your machine credentials and taught poses.** Fill in the relevant variables in helpers.py: the machine
   address and API key/ID from your machine's CONNECT tab, plus the two anchor
   poses you capture in Phase 3. Be sure not to commit credentials if you're going to have a public repo for this work.

   The anchors are **gripper-frame** poses. The gripper's kinematics end at the
   TCP between the fingertips, and that is the frame the motion service plans
   for, so read them from the Motion tab of the machine configuration in Viam.

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
  configure resources by hand with the discovery service. The resource names
  there (`follower-arm`, `follower-gripper`) must match `ARM` and `GRIPPER` in
  `helpers.py` — `GRIPPER` doubles as a frame name, so a mismatch fails the move
  with an unknown-frame error rather than failing quietly.
- The template dimensions (`CUBE = 16 mm`, `PITCH = 30 mm`) match the constants
  in the code. If you change one, change the other, and regenerate the PDF with
  `uv run --with reportlab python template/generate_template.py`.
- The pallet mat fixes the four cells relative to each other; the staging square
  is a separate cut-out you place wherever the arm reaches. Both anchors are
  taught by hand, so the code never assumes a distance between them.
- The reference drives the jaws with the gripper module's `set_position`
  DoCommand rather than the Gripper API's `open()`/`grab()`. `grab()` keeps
  pulling against the cube and overloads the servo; a full `open()` swings the
  moving jaw into cubes already on the pallet. `JAW_OPEN` and `JAW_CLOSED` in
  `reference/palletizer.py` are calibration values — expect to tune them.
- Never commit real credentials.
