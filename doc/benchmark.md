# Benchmarks

## `benchmark.py`

This is a simple benchmark for measuring the speed of movement actions. The Magnebot will spawn into an empty room. Note that empty rooms loaded via `self.init_scene()` always run faster than floorplan scenes loaded via `self.init_floorplan_scene().

To run the benchmark:

1. `cd controllers/tests/benchmark`
2. `python3 benchmark.py`
3. Launch the build.

#### `turn_by()`

Average time elapsed during `turn_by(45)`: 0.24716432094573976 seconds

#### `move_by()`

Average time elapsed during `move_by(0.5)`: 0.13557246923446656 seconds

#### Skipped frames

These tests measure the average time elapsed during `move_by(0.5)` with varying quantities of skipped frames per `communicate()` call (see the `skip_frames` parameter in the `Magnebot` constructor).

| Skipped frames | Time elapsed |
| --- | --- |
| 0 | 0.34852654933929444 |
| 5 | 0.14801830053329468 |
| 10 | 0.13034409284591675 |
| 15 | 0.14144458770751953 |
| 20 | 0.14268385171890258 |

## `floorplan_benchmark.py`

This benchmark tests the intrinsic slowdown in the simulation in a floorplan scene. Compare these results to the `move_by()` test in `benchmark.py`.

To run the benchmark:

1. `cd controllers/tests/benchmark`
2. `python3 floorplan_benchmark.py`
3. Launch the build.

The "Default" test uses the default values in the Magnebot API. The other tests toggle on and off global parameters for the simulator. These parameters aren't actually toggeable in the Magnebot API (they're crucial for image quality) but they are included here to help explain why the floorplan scenes run slower than the test room. 

| Test                                               | Time elapsed        |
| -------------------------------------------------- | ------------------- |
| Default                                            | 0.303550660610199   |
| Without reflection probes                          | 0.2659665584564209  |
| Without post-process                               | 0.3082748770713806  |
| Without post-process and without reflection probes | 0.26149789094924925 |

## `precision.py`

This benchmark tests how the precision of the Magnebot's moving and turning affects its speed. Moving and turning actions have a threshold at which the Magnebot has "arrived" at the target. For example, if the action is `m.move_by(distance=2, arrived_at=0.3)`, the Magnebot will stop moving when it is within 0.3 meters of the target distance of 2 meters.

To run the benchmark:

1. `cd controllers/tests/benchmark`
2. `python3 precision.py`
3. Launch the build.

| `aligned_at` | Average time elapsed |
| ------------ | -------------------- |
| 3            | 0.5524171471595765   |
| 1            | 0.548958420753479    |
| 0.5          | 0.6427297115325927   |
| 0.2          | 0.5990262508392334   |

| `arrived_at` | Average time elapsed |
| ------------ | -------------------- |
| 0.3          | 0.2924862623214722   |
| 0.1          | 0.32846505641937257  |
| 0.02         | 0.4408447504043579   |
| 0.01         | 0.47646485567092894  |