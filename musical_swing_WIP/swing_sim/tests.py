"""
Headless validation checks.

Run:
  python -m swing_sim.tests
"""
from __future__ import annotations
import math
from swing_sim.config import AppConfig
from swing_sim.physics import PhysicsSim
from swing_sim.imu import IMUSim
from swing_sim.control import IntensityEstimator, Controller


class Harness:
    def __init__(self):
        self.cfg = AppConfig()
        self.physics = PhysicsSim(self.cfg.physics)
        self.imu = IMUSim(self.cfg.imu, seed=self.cfg.physics.seed)
        self.est = IntensityEstimator(self.cfg.env)
        self.ctrl = Controller(self.cfg.ctrl)
        self.control_div = 5
        self.control_dt = self.cfg.physics.dt_physics * self.control_div
        self.step_count = 0
        self.last_out = None


def run_for_seconds(h: Harness, seconds: float) -> None:
    steps = int(seconds / h.cfg.physics.dt_physics)
    for _ in range(steps):
        h.physics.step()
        imu = h.imu.sample(h.physics.t, h.physics.state.omega)
        gy = float(imu.gyro_xyz[1])
        raw = abs(gy) if not math.isnan(gy) else float("nan")
        h.step_count += 1
        if h.step_count % h.control_div == 0:
            env = h.est.update(raw, h.control_dt)
            h.last_out = h.ctrl.update(env.x_norm, h.control_dt, h.cfg.physics.wind_enabled)


def test_wind_quiet_default() -> None:
    h = Harness()
    h.cfg.physics.wind_enabled = True
    h.physics.cfg.wind_enabled = True
    run_for_seconds(h, 10.0)
    assert h.last_out is not None
    assert max(h.last_out.gains) < 1e-3


def test_impulse_activates_layer1() -> None:
    h = Harness()
    for _ in range(6):
        h.physics.apply_impulse()
        run_for_seconds(h, 2.0)
    assert h.last_out is not None
    assert h.last_out.gains[0] > 0.1


if __name__ == "__main__":
    test_wind_quiet_default()
    test_impulse_activates_layer1()
    print("All tests passed.")
