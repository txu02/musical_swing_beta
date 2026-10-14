from __future__ import annotations

from dataclasses import dataclass
import math
import numpy as np
from .config import PhysicsConfig


@dataclass
class PhysicsState:
    theta: float = 0.0   # radians
    omega: float = 0.0   # rad/s


class PhysicsSim:
    """
    Damped pendulum model with semi-implicit Euler integration at 1 kHz.
    Includes mouse dragging, impulse injection, and wind forcing.
    """

    def __init__(self, cfg: PhysicsConfig):
        self.cfg = cfg
        self.state = PhysicsState(theta=0.0, omega=0.0)
        self._t = 0.0

        self.is_dragging = False
        self.drag_theta = 0.0

        self._rng = np.random.default_rng(self.cfg.seed)

        self.impulse_strength = 1.2
        self.impulse_mode = "assist"  # assist|positive|negative

    @property
    def t(self) -> float:
        return self._t

    def reset(self) -> None:
        self.state = PhysicsState(theta=0.0, omega=0.0)
        self._t = 0.0

    def set_seed(self, seed: int) -> None:
        self.cfg.seed = seed
        self._rng = np.random.default_rng(seed)

    def set_drag(self, dragging: bool, theta: float | None = None) -> None:
        self.is_dragging = dragging
        if theta is not None:
            self.drag_theta = theta

    def apply_impulse(self) -> None:
        s = 1.0
        if self.impulse_mode == "positive":
            s = 1.0
        elif self.impulse_mode == "negative":
            s = -1.0
        else:
            if abs(self.state.omega) > 1e-3:
                s = math.copysign(1.0, self.state.omega)
            else:
                s = -math.copysign(1.0, self.state.theta) if abs(self.state.theta) > 1e-4 else 1.0
        self.state.omega += s * self.impulse_strength

    def _wind_torque(self) -> float:
        if not self.cfg.wind_enabled:
            return 0.0
        sine = self.cfg.wind_sine_amp * math.sin(2.0 * math.pi * self.cfg.wind_sine_hz * self._t)
        noise = self.cfg.wind_noise_amp * float(self._rng.normal())
        return sine + noise

    def step(self) -> None:
        dt = self.cfg.dt_physics
        self._t += dt

        if self.is_dragging:
            self.state.theta = self.drag_theta
            self.state.omega *= 0.2
            return

        theta = self.state.theta
        omega = self.state.omega

        alpha = -(self.cfg.g / self.cfg.length_m) * math.sin(theta)
        alpha += -self.cfg.damping * omega
        alpha += self._wind_torque()

        omega_new = omega + dt * alpha
        theta_new = theta + dt * omega_new

        if theta_new > math.pi:
            theta_new -= 2 * math.pi
        elif theta_new < -math.pi:
            theta_new += 2 * math.pi

        self.state.theta = theta_new
        self.state.omega = omega_new
