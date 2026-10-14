from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, List
import numpy as np


@dataclass
class CalibrationResult:
    floor: float
    max_val: float
    T1: float
    T2: float
    T3: float
    explanation: str


class CalibrationManager:
    def __init__(self):
        self.state: str = "idle"
        self._buffer: List[float] = []
        self._target_seconds: float = 0.0
        self._start_time: Optional[float] = None
        self._baseline_vals: Optional[np.ndarray] = None
        self._active_vals: Optional[np.ndarray] = None
        self.result: Optional[CalibrationResult] = None

    def start_baseline(self, now_t: float, seconds: float) -> None:
        self.state = "baseline"
        self._buffer = []
        self._target_seconds = float(seconds)
        self._start_time = float(now_t)
        self.result = None

    def start_active(self, now_t: float, seconds: float) -> None:
        self.state = "active"
        self._buffer = []
        self._target_seconds = float(seconds)
        self._start_time = float(now_t)
        self.result = None

    def cancel(self) -> None:
        self.state = "idle"
        self._buffer = []
        self._target_seconds = 0.0
        self._start_time = None
        self.result = None

    def update(self, now_t: float, raw_feature: float) -> None:
        if self.state not in ("baseline", "active"):
            return
        if self._start_time is None:
            self._start_time = now_t

        if raw_feature is not None and not np.isnan(raw_feature):
            self._buffer.append(float(raw_feature))

        if (now_t - self._start_time) >= self._target_seconds:
            vals = np.array(self._buffer, dtype=float) if self._buffer else np.array([0.0], dtype=float)
            if self.state == "baseline":
                self._baseline_vals = vals
                self.state = "idle"
            elif self.state == "active":
                self._active_vals = vals
                self.state = "idle"

            if self._baseline_vals is not None and self._active_vals is not None:
                self.result = self._compute_result(self._baseline_vals, self._active_vals)
                self._baseline_vals = None
                self._active_vals = None

    def _compute_result(self, baseline: np.ndarray, active: np.ndarray) -> CalibrationResult:
        floor = float(np.percentile(baseline, 95))
        max_val = float(np.percentile(active, 95))
        if max_val <= floor + 1e-6:
            max_val = floor + 1.0

        r = max_val - floor
        T1 = floor + 0.15 * r
        T2 = floor + 0.45 * r
        T3 = floor + 0.75 * r

        explanation = (
            "Calibration summary:\n"
            f"- floor set to 95th percentile of baseline: {floor:.3f}\n"
            f"- max set to 95th percentile of active: {max_val:.3f}\n"
            "Thresholds suggested at 15% / 45% / 75% of the usable range (max-floor).\n"
            "These are starting points; adjust based on desired sensitivity."
        )
        return CalibrationResult(floor=floor, max_val=max_val, T1=T1, T2=T2, T3=T3, explanation=explanation)
