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

import helpers
from helpers import down_pose

PITCH = 30  # mm, center-to-center spacing between adjacent pallet cells
CUBE = 20  # mm, cube side length, and the z offset between layers
APPROACH = 40  # mm, hover height above a pose before descending
GRASP_DEPTH = 5  # mm, how far the gripper descends past the cube top to close on it


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
                        center=Pose(x=p.x, y=p.y, z=p.z, o_x=0, o_y=0, o_z=1, theta=0),
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
                        pose=Pose(x=0, y=0, z=CUBE / 2, o_x=0, o_y=0, o_z=1, theta=0),
                    ),
                    physical_object=Geometry(
                        center=Pose(x=0, y=0, z=0),
                        box=RectangularPrism(dims_mm=Vector3(x=CUBE, y=CUBE, z=CUBE)),
                        label="held-cube",
                    ),
                )
            )
        if not placed and not transforms:
            return None
        return WorldState(obstacles=placed, transforms=transforms)

    async def move_gripper(self, pose: Pose, world_state=None):
        destination = PoseInFrame(reference_frame="world", pose=pose)
        await self.motion.move(
            component_name=helpers.ARM,
            destination=destination,
            world_state=world_state,
        )

    async def move(self):
        """Send the gripper to a safe pose, pointing straight down."""
        await self.move_gripper(down_pose(200, 0, 150))

    async def pick(self):
        """Pick the cube waiting on the staging spot and lift it clear."""
        staging = helpers.STAGING_POSE
        hover = down_pose(staging.x, staging.y, staging.z + APPROACH)
        grasp = down_pose(staging.x, staging.y, staging.z - GRASP_DEPTH)
        await self.move_gripper(hover, self.obstacles())
        await self.move_gripper(grasp, self.obstacles())
        await self.gripper.grab()
        await self.move_gripper(hover, self.obstacles(held=True))

    async def place(self, seq: int):
        """Place the held cube into grid cell `seq`."""
        target = helpers.grid(helpers.PALLET_ORIGIN, PITCH, CUBE)[seq]
        hover = down_pose(target.x, target.y, target.z + APPROACH)
        await self.move_gripper(hover, self.obstacles(held=True))
        await self.move_gripper(down_pose(target.x, target.y, target.z), self.obstacles())
        await self.gripper.open()
        await self.move_gripper(hover, self.obstacles())
        self.placed.append(target)

    async def pack(self):
        """Pack both layers: eight cubes, cells 0 through 7."""
        for seq in range(8):
            input(f"Place a cube on the staging spot, then press Enter (cell {seq})... ")
            await self.pick()
            await self.place(seq)
        print(f"packed {len(self.placed)} cubes")


STEPS = {
    "move": Palletizer.move,
    "pick": Palletizer.pick,
    "pack": Palletizer.pack,
}


async def main(verb):
    robot = await helpers.connect()
    palletizer = Palletizer(robot)
    try:
        step = STEPS.get(verb)
        if step is None:
            print(f"unknown step '{verb}'. steps: {', '.join(STEPS)}")
            return
        await step(palletizer)
    finally:
        await robot.close()


if __name__ == "__main__":
    verb = sys.argv[1] if len(sys.argv) > 1 else "pack"
    asyncio.run(main(verb))
