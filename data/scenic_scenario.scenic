# Scenic tutorial inspired scenario.
# This file documents the starting scenario idea. The runnable project uses
# the CSV trace in this folder, so no simulator is required for Phase 1.

model scenic.domains.driving.model

param map = localPath("maps/simple-town.xodr")

ego = new Car with behavior FollowLaneBehavior,
    with speed 13

parked = new Car ahead of ego by Range(18, 42),
    offset by Range(1.4, 2.2) @ 90 deg,
    with behavior PullIntoRoadBehavior

require distance to parked < 45
terminate after 12 seconds
