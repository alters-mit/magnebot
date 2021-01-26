# Benchmarks

## `benchmark.py`

This is a simple benchmark for measuring the speed of movement actions. It uses the [`TestController`](api/test_controller.md) class, meaning that the Magnebot will spawn into an empty room. This Magnebot will always be faster in this scene than in a floorplan scene used by the `Magnebot` class.

To run the benchmark:

1. `cd controllers/tests/benchmark`
2. `python3 benchmark.py`
3. Launch the build.

#### `turn_by()`

Average time elapsed during `turn_by(45)`: 0.3626535892486572 seconds

#### `move_by()`

Average time elapsed during `move_by(0.5)`: 0.18326703310012818 seconds

#### Skipped frames

These tests measure the average time elapsed during `move_by(0.5)` with varying quantities of skipped frames per `communicate()` call (see the `skip_frames` parameter in the `Magnebot` constructor).

| Skipped frames | Time elapsed        |
| -------------- | ------------------- |
| 0              | 0.6230585694313049  |
| 5              | 0.2050017833709717  |
| 10             | 0.18139997720718384 |
| 15             | 0.17385331392288209 |
| 20             | 0.17365176677703859 |

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