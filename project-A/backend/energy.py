"""
Energy measurement module.
Uses psutil (cross-platform) with optional Intel RAPL support on Linux.
Falls back to CPU-time based estimation on Windows.
"""

import time
import os
import platform
import psutil
from dataclasses import dataclass, field, asdict
from typing import Optional, Dict, List
from contextlib import contextmanager


@dataclass
class EnergyReading:
    """A single energy snapshot."""
    timestamp: float = 0.0
    cpu_percent: float = 0.0
    memory_mb: float = 0.0
    energy_uj: Optional[float] = None  # micro-joules from RAPL if available


@dataclass
class EnergyReport:
    """Full energy report for one analysis run."""
    wall_time_s: float = 0.0
    cpu_time_s: float = 0.0
    peak_memory_mb: float = 0.0
    avg_cpu_percent: float = 0.0
    estimated_energy_joules: float = 0.0
    carbon_emissions_g_co2: float = 0.0
    rapl_available: bool = False
    rapl_energy_joules: Optional[float] = None
    readings: List[Dict] = field(default_factory=list)
    phases: Dict[str, float] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return asdict(self)


# ---------------------------------------------------------------------------
# RAPL helpers (Linux only)
# ---------------------------------------------------------------------------
RAPL_BASE = "/sys/class/powercap/intel-rapl"


def _rapl_available() -> bool:
    return platform.system() == "Linux" and os.path.isdir(RAPL_BASE)


def _read_rapl_uj() -> Optional[int]:
    """Read total package energy in micro-joules from RAPL."""
    try:
        pkg0 = os.path.join(RAPL_BASE, "intel-rapl:0", "energy_uj")
        with open(pkg0) as f:
            return int(f.read().strip())
    except Exception:
        return None


# ---------------------------------------------------------------------------
# TDP-estimation fallback (works on Windows / macOS / Linux without RAPL)
# ---------------------------------------------------------------------------
_ESTIMATED_TDP_WATTS = 28.0  # conservative laptop TDP


def _estimate_energy_joules(cpu_time_s: float, avg_cpu_pct: float) -> float:
    """Estimate energy from CPU time and average utilisation."""
    utilisation = max(avg_cpu_pct / 100.0, 0.01)
    return _ESTIMATED_TDP_WATTS * utilisation * cpu_time_s


# ---------------------------------------------------------------------------
# Collector
# ---------------------------------------------------------------------------
class EnergyCollector:
    """Collects energy / performance readings during an analysis run."""

    def __init__(self):
        self._readings: List[EnergyReading] = []
        self._start_wall: float = 0
        self._start_cpu: float = 0
        self._rapl_start: Optional[int] = None
        self._peak_mem: float = 0
        self._phase_marks: Dict[str, float] = {}
        self._phase_start: Optional[str] = None
        self._phase_t0: float = 0

    # -- lifecycle ----------------------------------------------------------
    def start(self):
        self._start_wall = time.perf_counter()
        self._start_cpu = time.process_time()
        if _rapl_available():
            self._rapl_start = _read_rapl_uj()
        self._snap()

    def stop(self) -> EnergyReport:
        self._snap()
        wall = time.perf_counter() - self._start_wall
        cpu = time.process_time() - self._start_cpu
        avg_cpu = (
            sum(r.cpu_percent for r in self._readings) / len(self._readings)
            if self._readings
            else 0.0
        )

        rapl_j: Optional[float] = None
        rapl_ok = False
        if self._rapl_start is not None:
            rapl_end = _read_rapl_uj()
            if rapl_end is not None:
                rapl_j = (rapl_end - self._rapl_start) / 1_000_000
                rapl_ok = True

        estimated = rapl_j if rapl_j is not None else _estimate_energy_joules(cpu, avg_cpu)

        # Assuming global average carbon intensity: ~475 grams of CO2 per kWh.
        # 1 Joule = 1 / 3,600,000 kWh.
        # 475 / 3,600,000 = 0.00013194 g CO2 per Joule
        # Add PUE (Power Usage Effectiveness) of average data center ~ 1.5
        CARBON_INTENSITY_G_CO2_PER_JOULE = 0.00013194 * 1.5
        
        # Prevent zero-emission display for ultra-fast executions (minimum 1ms cpu time assumed)
        min_cpu = max(cpu, 0.001)
        min_estimated = rapl_j if rapl_j is not None else _estimate_energy_joules(min_cpu, max(avg_cpu, 1.0))
        
        carbon_emissions = min_estimated * CARBON_INTENSITY_G_CO2_PER_JOULE

        return EnergyReport(
            wall_time_s=round(wall, 4),
            cpu_time_s=round(cpu, 4),
            peak_memory_mb=round(self._peak_mem, 2),
            avg_cpu_percent=round(avg_cpu, 2),
            estimated_energy_joules=round(estimated, 6),
            carbon_emissions_g_co2=round(carbon_emissions, 10),
            rapl_available=rapl_ok,
            rapl_energy_joules=round(rapl_j, 6) if rapl_j is not None else None,
            readings=[
                {
                    "t": round(r.timestamp - self._start_wall, 4),
                    "cpu": round(r.cpu_percent, 1),
                    "mem": round(r.memory_mb, 1),
                }
                for r in self._readings
            ],
            phases=self._phase_marks,
        )

    # -- phase tracking -----------------------------------------------------
    def begin_phase(self, name: str):
        now = time.perf_counter()
        if self._phase_start:
            self._phase_marks[self._phase_start] = round(now - self._phase_t0, 4)
        self._phase_start = name
        self._phase_t0 = now
        self._snap()

    def end_phase(self):
        if self._phase_start:
            now = time.perf_counter()
            self._phase_marks[self._phase_start] = round(now - self._phase_t0, 4)
            self._phase_start = None
        self._snap()

    # -- internal -----------------------------------------------------------
    def _snap(self):
        proc = psutil.Process()
        mem = proc.memory_info().rss / (1024 * 1024)
        self._peak_mem = max(self._peak_mem, mem)
        reading = EnergyReading(
            timestamp=time.perf_counter(),
            cpu_percent=psutil.cpu_percent(interval=0),
            memory_mb=mem,
            energy_uj=_read_rapl_uj() if _rapl_available() else None,
        )
        self._readings.append(reading)


@contextmanager
def measure_energy():
    """Context manager that yields an EnergyCollector."""
    collector = EnergyCollector()
    collector.start()
    try:
        yield collector
    finally:
        pass  # caller calls collector.stop() explicitly for the report
