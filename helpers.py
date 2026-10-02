"""Plumbing for the mini-palletizer workshop.

You import this file from `palletizer.py`; you do not need to edit anything here
except the two blocks at the top: your machine credentials, and the two anchor
poses you capture by hand in Phase 3.

It provides:
- `connect()`            an async function that returns a connected RobotClient
- `ARM`, `GRIPPER`, `MOTION`   the resource handles palletizer.py passes around
- `down_pose(x, y, z)`   a pose at (x, y, z) with the tool pointing straight down
- `grid(origin, pitch, cube)`  the eight pallet target poses from one corner
- `STAGING_POSE`, `PALLET_ORIGIN`   the two gripper-frame poses you teach by hand
"""

from viam.robot.client import RobotClient
from viam.proto.common import Pose

# ---------------------------------------------------------------------------
# 1. Machine credentials. Copy these from your machine's CONNECT tab in the
#    Viam app (select "Python SDK" and toggle "Include API key").
# ---------------------------------------------------------------------------
MACHINE_ADDRESS = "<machine-address>"
API_KEY = "<api-key>"
API_KEY_ID = "<api-key-id>"

# ---------------------------------------------------------------------------
# 2. The two anchor poses you capture in Phase 3. These are GRIPPER-frame poses:
#    the gripper's kinematics end at the TCP between the fingertips, which is
#    the frame the motion service plans for. Jog the arm until the fingertips
#    straddle a cube's top face, then read the x, y, z with
#
#        await motion.get_pose(component_name=GRIPPER, destination_frame="world")
#
#    An arm-frame pose will not do: it sits one finger length higher, and
#    pasting one here drives the gripper into the table. The straight-down
#    orientation is already set.
# ---------------------------------------------------------------------------
GRASP_THETA = 0  # roll about the tool axis: which way the jaws face
STAGING_POSE = Pose(x=0.0, y=0.0, z=0.0, o_x=0, o_y=0, o_z=-1, theta=GRASP_THETA)
PALLET_ORIGIN = Pose(x=0.0, y=0.0, z=0.0, o_x=0, o_y=0, o_z=-1, theta=GRASP_THETA)


# ---------------------------------------------------------------------------
# Resource handles. All three are plain strings: the motion service takes a
# component *or frame* name, and `from_robot` takes a component name.
#
# `GRIPPER` does triple duty: the component to open and close, the frame the
# motion service plans for, and the frame the held cube is attached to. These
# must match the component names on your machine and in machine-fragment.json,
# or the motion service rejects the move with an unknown-frame error. `ARM` is
# here for arm-level calls; the palletizer plans in the gripper frame.
# ---------------------------------------------------------------------------
ARM = "arm-1"
GRIPPER = "gripper-1"
MOTION = "builtin"


async def connect() -> RobotClient:
    """Connect to your machine using the credentials above."""
    if MACHINE_ADDRESS.startswith("<"):
        raise RuntimeError(
            "No machine credentials. Copy local_config.example.py to "
            "local_config.py and fill in MACHINE_ADDRESS, API_KEY and "
            "API_KEY_ID from your machine's CONNECT tab. Run from the repo "
            "root so local_config.py is importable."
        )
    opts = RobotClient.Options.with_api_key(api_key=API_KEY, api_key_id=API_KEY_ID)
    return await RobotClient.at_address(MACHINE_ADDRESS, opts)


def down_pose(x, y, z, theta=None) -> Pose:
    """A pose at (x, y, z) with the tool pointing straight down.

    `theta` rolls the tool about that axis, setting which way the jaws face.
    It defaults to the roll your anchors are taught at, so a cube is set down
    the same way it was picked up.
    """
    return Pose(
        x=x,
        y=y,
        z=z,
        o_x=0,
        o_y=0,
        o_z=-1,
        theta=GRASP_THETA if theta is None else theta,
    )


def grid(origin, pitch, cube):
    """Return the eight target poses for a two-layer, four-cell pallet,
    given the bottom-layer origin corner (cell [0, 0]).

    Indices 0-3 are the bottom layer; 4-7 are the top layer, one `cube`
    height above their bottom-layer counterparts.
    """

    def cell(x, y, z):
        # Carry the origin's orientation. A Pose left at its defaults has a
        # zero-magnitude orientation vector, which is not a valid orientation.
        return Pose(
            x=x,
            y=y,
            z=z,
            o_x=origin.o_x,
            o_y=origin.o_y,
            o_z=origin.o_z,
            theta=origin.theta,
        )

    bottom = [
        cell(origin.x + dx, origin.y + dy, origin.z)
        for dx in (0, pitch)
        for dy in (0, pitch)
    ]
    top = [cell(p.x, p.y, p.z + cube) for p in bottom]
    return bottom + top
