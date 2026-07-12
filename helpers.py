"""Plumbing for the mini-palletizer workshop.

You import this file from `palletizer.py`; you do not need to edit anything here
except the two blocks at the top: your machine credentials, and the two anchor
poses you capture by hand in Phase 3.

It provides:
- `connect()`            an async function that returns a connected RobotClient
- `ARM`, `GRIPPER`, `MOTION`   the resource handles palletizer.py passes around
- `down_pose(x, y, z)`   a pose at (x, y, z) with the tool pointing straight down
- `grid(origin, pitch, cube)`  the eight pallet target poses from one corner
- `STAGING_POSE`, `PALLET_ORIGIN`   the two poses you teach the arm by hand
"""

from viam.components.arm import Arm
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
# 2. The two anchor poses you capture in Phase 3. Paste the x, y, z you read
#    off the arm's test card. The straight-down orientation is already set.
# ---------------------------------------------------------------------------
STAGING_POSE = Pose(x=0.0, y=0.0, z=0.0, o_x=0, o_y=0, o_z=-1, theta=0)
PALLET_ORIGIN = Pose(x=0.0, y=0.0, z=0.0, o_x=0, o_y=0, o_z=-1, theta=0)

# ---------------------------------------------------------------------------
# Resource handles. `ARM` is a ResourceName because the motion service takes
# one; `GRIPPER` and `MOTION` are plain names passed to `from_robot`.
# These assume you named the arm "arm" and the gripper "gripper" in Phase 2,
# and that the built-in motion service is named "builtin".
# ---------------------------------------------------------------------------
ARM = Arm.get_resource_name("arm")
GRIPPER = "gripper"
MOTION = "builtin"


async def connect() -> RobotClient:
    """Connect to your machine using the credentials above."""
    opts = RobotClient.Options.with_api_key(
        api_key=API_KEY, api_key_id=API_KEY_ID
    )
    return await RobotClient.at_address(MACHINE_ADDRESS, opts)


def down_pose(x, y, z) -> Pose:
    """A pose at (x, y, z) with the tool pointing straight down."""
    return Pose(x=x, y=y, z=z, o_x=0, o_y=0, o_z=-1, theta=0)


def grid(origin, pitch, cube):
    """Return the eight target poses for a two-layer, four-cell pallet,
    given the bottom-layer origin corner (cell [0, 0]).

    Indices 0-3 are the bottom layer; 4-7 are the top layer, one `cube`
    height above their bottom-layer counterparts.
    """
    bottom = [
        Pose(x=origin.x + dx, y=origin.y + dy, z=origin.z)
        for dx in (0, pitch)
        for dy in (0, pitch)
    ]
    top = [Pose(x=p.x, y=p.y, z=p.z + cube) for p in bottom]
    return bottom + top
