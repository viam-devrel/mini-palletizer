"""Finished reference for the mini-palletizer workshop (milestone two).

This is the `palletizer.py` the tutorial builds up: a static bottom-layer pack
in Phase 4 (milestone one), then a full collision-free two-layer pack in
Phase 5 (milestone two) using WorldState obstacles and a held-cube transform.
Keep it here to check your work; write your own version in the repo root as you
follow the phases.

    uv run reference/palletizer.py move    # send the gripper to a safe pose
    uv run reference/palletizer.py pick    # pick one hand-fed cube
    uv run reference/palletizer.py pack    # the full two-layer pack (default)

Note: the first held-cube move can fail with a "start state in collision" error
because the held-cube geometry overlaps the gripper. If you hit that, allow the
gripper/held-cube pair with a collision specification (see the Viam motion docs
on attaching and detaching geometries).
"""

import asyncio
import sys
from pathlib import Path

from viam.components.gripper import Gripper
from viam.services.motion import MotionClient
from viam.proto.common import (
    Pose,
    PoseInFrame,
    WorldState,
    GeometriesInFrame,
    Geometry,
    RectangularPrism,
    Vector3,
    Transform,
)

# helpers.py lives in the repo root and this file does not. Running a script
# puts the script's own directory on sys.path, not the root, so add the root.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import helpers  # noqa: E402
from helpers import down_pose  # noqa: E402

PITCH = 30  # mm, center-to-center spacing between adjacent pallet cells
CUBE = 16  # mm, cube side length, and the z offset between layers
APPROACH = 40  # mm, hover height above a pose before descending
GRASP_DEPTH = 5  # mm, how far the gripper descends past the cube top to close on it
SETTLE = 0.6  # s, dwell after a gripper command; the servo acks before it finishes

# Jaw positions, as a percentage of full travel, driven through the gripper
# module's `set_position` DoCommand rather than the Gripper API's open()/grab().
# grab() closes against the cube and keeps pulling, which overloads the servo;
# open() swings the moving jaw its full range, which clips cubes already on the
# pallet. These two are a calibration: widen OPEN until the jaws clear a cube,
# tighten CLOSED until it is held without the servo straining.
JAW_OPEN = 20
JAW_CLOSED = 8

# Every pose below is a gripper-frame pose. The gripper's kinematics end at the
# TCP between the fingertips, so a taught pose puts the TCP level with a cube's
# top face and the cube's center is CUBE / 2 below it. This is why move_gripper
# plans for helpers.GRIPPER and not helpers.ARM: the arm's own frame ends at the
# wrist, one finger length higher.
#
# Sanity-check your anchors against that convention: a cube placed at
# PALLET_ORIGIN spans z from `PALLET_ORIGIN.z - CUBE` to `PALLET_ORIGIN.z`, so
# the lower number is where the code thinks your table is.


class Palletizer:
    def __init__(self, robot):
        self.robot = robot
        self.motion = MotionClient.from_robot(robot, helpers.MOTION)
        self.gripper = Gripper.from_robot(robot, helpers.GRIPPER)
        self.placed = []

    def obstacles(self, held=False):
        """Build the WorldState for this move: placed cubes as obstacles, and
        the carried cube as a transform that rides the gripper."""
        placed = [
            GeometriesInFrame(
                reference_frame="world",
                geometries=[
                    Geometry(
                        # `center` is the cube's center; `p` is the TCP level
                        # with the cube's top face.
                        center=Pose(
                            x=p.x, y=p.y, z=p.z - CUBE / 2, o_x=0, o_y=0, o_z=1, theta=0
                        ),
                        box=RectangularPrism(dims_mm=Vector3(x=CUBE, y=CUBE, z=CUBE)),
                        label=f"placed-{i}",
                    )
                ],
            )
            for i, p in enumerate(self.placed)
        ]
        transforms = []
        if held:
            transforms.append(
                Transform(
                    reference_frame="held-cube",
                    pose_in_observer_frame=PoseInFrame(
                        reference_frame=helpers.GRIPPER,
                        # The grasp descends GRASP_DEPTH past the cube's top
                        # face, so the cube's center rides this far out the tool.
                        pose=Pose(
                            x=0,
                            y=0,
                            z=CUBE / 2 - GRASP_DEPTH,
                            o_x=0,
                            o_y=0,
                            o_z=1,
                            theta=0,
                        ),
                    ),
                    physical_object=Geometry(
                        center=Pose(x=0, y=0, z=0, o_x=0, o_y=0, o_z=1, theta=0),
                        box=RectangularPrism(dims_mm=Vector3(x=CUBE, y=CUBE, z=CUBE)),
                        label="held-cube",
                    ),
                )
            )
        if not placed and not transforms:
            return None
        return WorldState(obstacles=placed, transforms=transforms)

    async def set_jaw(self, percentage: int):
        """Drive the jaws to a percentage of full travel, and let them get there."""
        await self.gripper.do_command(
            {"command": "set_position", "percentage": percentage}
        )
        await asyncio.sleep(SETTLE)

    async def move_gripper(self, pose: Pose, world_state=None):
        destination = PoseInFrame(reference_frame="world", pose=pose)
        moved = await self.motion.move(
            # The gripper frame, not the arm frame: its kinematics end at the
            # TCP between the fingertips, which is what the anchors are taught in.
            component_name=helpers.GRIPPER,
            destination=destination,
            world_state=world_state,
        )
        if not moved:
            raise RuntimeError(f"no plan to ({pose.x}, {pose.y}, {pose.z})")

    async def move(self):
        """Send the gripper to a safe pose, pointing straight down."""
        await self.move_gripper(down_pose(200, 0, 150))

    async def pick(self):
        """Pick the cube waiting on the staging spot and lift it clear."""
        staging = helpers.STAGING_POSE
        hover = down_pose(staging.x, staging.y, staging.z + APPROACH, staging.theta)
        grasp = down_pose(staging.x, staging.y, staging.z - GRASP_DEPTH, staging.theta)
        await self.move_gripper(hover, self.obstacles())
        # The jaws may be closed from a previous run; open before descending.
        await self.set_jaw(JAW_OPEN)
        await self.move_gripper(grasp, self.obstacles())
        await self.set_jaw(JAW_CLOSED)
        # set_position is open-loop: nothing here can tell you the cube is
        # actually between the jaws. If your gripper module implements it,
        # `(await self.gripper.is_holding_something()).is_holding_something`
        # is the check to add.
        await self.move_gripper(hover, self.obstacles(held=True))

    async def place(self, seq: int):
        """Place the held cube into grid cell `seq`."""
        target = helpers.grid(helpers.PALLET_ORIGIN, PITCH, CUBE)[seq]
        hover = down_pose(target.x, target.y, target.z + APPROACH, target.theta)
        await self.move_gripper(hover, self.obstacles(held=True))
        # Mirror the pick: the cube was gripped GRASP_DEPTH below its top face,
        # so release it the same distance down or it falls the difference.
        await self.move_gripper(
            down_pose(target.x, target.y, target.z - GRASP_DEPTH, target.theta),
            self.obstacles(),
        )
        await self.set_jaw(JAW_OPEN)
        await self.move_gripper(hover, self.obstacles())
        self.placed.append(target)

    async def pack(self):
        """Pack both layers: eight cubes, cells 0 through 7."""
        for seq in range(8):
            input(
                f"Place a cube on the staging spot, then press Enter (cell {seq})... "
            )
            await self.pick()
            await self.place(seq)
        print(f"packed {len(self.placed)} cubes")


STEPS = {
    "move": Palletizer.move,
    "pick": Palletizer.pick,
    "pack": Palletizer.pack,
}


async def main(verb):
    step = STEPS.get(verb)
    if step is None:
        print(f"unknown step '{verb}'. steps: {', '.join(STEPS)}")
        return
    # Only dial the machine once we know there is something to do.
    robot = await helpers.connect()
    palletizer = Palletizer(robot)
    try:
        await step(palletizer)
    except BaseException:
        # robot.close() does not stop a moving arm; Ctrl-C must not leave it
        # mid-trajectory.
        await robot.stop_all()
        raise
    finally:
        await robot.close()


if __name__ == "__main__":
    verb = sys.argv[1] if len(sys.argv) > 1 else "pack"
    asyncio.run(main(verb))
