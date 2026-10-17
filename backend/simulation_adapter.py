"""Replace this boundary once sim exposes a scenario API (smoke tests are not one)."""
from backend.models import Inputs


class SimulationUnavailable(Exception):
    pass


class SimulationAdapter:
    version = "demo-2"

    def require_sumo(self) -> None:
        raise SimulationUnavailable(
            "SUMO scenario evaluation unavailable: sim currently exposes only discovery "
            "and smoke tests, not a network/demand/intervention API. No fallback was run."
        )

    def indicators(self, inputs: Inputs) -> dict[str, float]:
        """Illustrative delay; never a calibrated traffic model or SUMO result.

        Uniform-arrival red delay R²/(2C), plus 60 seconds times excess
        demand/capacity ratio. Synthetic saturation flow is 1800 veh/hour.
        """
        cycle = inputs.cycle_seconds
        def delay(green: float, demand: float) -> float:
            capacity = 1800 * green / cycle
            return (cycle - green) ** 2 / (2 * cycle) + 60 * max(0, demand / capacity - 1)
        ns = delay(inputs.ns_green_seconds, inputs.ns_demand_vph)
        ew = delay(cycle - inputs.lost_seconds - inputs.ns_green_seconds, inputs.ew_demand_vph)
        return {"ns_delay": ns, "ew_delay": ew, "mean_delay":
                (ns * inputs.ns_demand_vph + ew * inputs.ew_demand_vph) /
                (inputs.ns_demand_vph + inputs.ew_demand_vph)}
