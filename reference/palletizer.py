"""Finished reference for the mini-palletizer workshop (milestone one).

This is the `palletizer.py` the tutorial builds up one method at a time in
Phase 4. Keep it here to check your work; write your own version in the repo
root as you follow the phases.

    uv run reference/palletizer.py move    # send the gripper to a safe pose
    uv run reference/palletizer.py pick    # pick one hand-fed cube
    uv run reference/palletizer.py pack    # the static bottom-layer pack (default)

Phase 5 extends `move_gripper` with a WorldState of the placed and held cubes
so the arm can stack the second layer without colliding.
"""

import asyncio
import sys

from viam.components.gripper import Gripper
from viam.services.motion import MotionClient
from viam.proto.common import Pose, PoseInFrame

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

    async def move_gripper(self, pose: Pose):
        destination = PoseInFrame(reference_frame="world", pose=pose)
        await self.motion.move(
            component_name=helpers.ARM,
            destination=destination,
            world_state=None,
        )

    async def move(self):
        """Send the gripper to a safe pose, pointing straight down."""
        await self.move_gripper(down_pose(200, 0, 150))

    async def pick(self):
        """Pick the cube waiting on the staging spot and lift it clear."""
        staging = helpers.STAGING_POSE
        hover = down_pose(staging.x, staging.y, staging.z + APPROACH)
        grasp = down_pose(staging.x, staging.y, staging.z - GRASP_DEPTH)
        await self.move_gripper(hover)
        await self.move_gripper(grasp)
        await self.gripper.grab()
        await self.move_gripper(hover)

    async def place(self, seq: int):
        """Place the held cube into bottom-layer grid cell `seq`."""
        target = helpers.grid(helpers.PALLET_ORIGIN, PITCH, CUBE)[seq]
        hover = down_pose(target.x, target.y, target.z + APPROACH)
        await self.move_gripper(hover)
        await self.move_gripper(down_pose(target.x, target.y, target.z))
        await self.gripper.open()
        await self.move_gripper(hover)
        self.placed.append(target)

    async def pack(self):
        """Pack the bottom layer: one cube per grid cell, cells 0 through 3."""
        for seq in range(4):
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
