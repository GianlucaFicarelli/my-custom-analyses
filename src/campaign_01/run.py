from pathlib import Path
from typing import Optional

from blueetl.campaign.config import SimulationCampaign
from bluepysnap.circuit_ids import CircuitNodeIds
from bluepysnap.frame_report import FrameReport
from bluepysnap.simulation import Simulation
from bluepysnap.spike_report import SpikeReport

from common.utils import L, run_analysis


def _get_ids(
    simulation: Simulation, node_set: Optional[str | dict], cell_step: int = 1
) -> CircuitNodeIds:
    if isinstance(node_set, str):
        node_set = simulation.node_sets[node_set]
    ids = simulation.circuit.nodes.ids(group=node_set)
    ids = ids[::cell_step] if cell_step != 1 else ids
    return ids


def _get_report(simulation: Simulation, report_type: str) -> SpikeReport | FrameReport:
    if report_type == "spikes":
        report = simulation.spikes
    else:
        report = simulation.reports[report_type]
    return report


def _plot(index: int, path: str, conditions: dict, analysis_config: dict) -> Path | None:
    file_name = Path(
        analysis_config["output"],
        f"plot_{analysis_config['report_type']}_{analysis_config['report_name']}_{index}.png",
    )
    L.info("Simulation: %s, Plot: %s", path, file_name)
    simulation = Simulation(path)
    cell_step = analysis_config["cell_step"]
    ax = None
    # iterate over the configured node_sets, or fallback to the simulation node_set
    node_sets = analysis_config.get("node_sets", [simulation.to_libsonata.node_set])
    for node_set in node_sets:
        ids = _get_ids(
            simulation,
            node_set=node_set,
            cell_step=cell_step,
        )
        L.info("Node set: %s, ids: %s", node_set, len(ids))
        report = _get_report(
            simulation,
            report_type=analysis_config["report_type"],
        )
        report = report.filter(group=ids)
        report = getattr(report, analysis_config["report_name"])
        ax = report(ax=ax)
    if not ax:
        return None
    label = "  ".join(f"{k}={v}" for k, v in conditions.items())
    ax.set_title(
        f"{analysis_config['report_type']} {analysis_config['report_name']} {index}: {label}"
    )
    legend_labels = [str(i) for i in node_sets]
    ax.legend(legend_labels, loc="upper center", bbox_to_anchor=(0.5, -0.1))
    ax.figure.savefig(file_name, bbox_inches="tight")
    ax.figure.clear()
    ax.cla()
    return file_name


@run_analysis
def main(analysis_config: dict) -> dict:
    outputs = []
    campaign = SimulationCampaign.load(analysis_config["simulation_campaign"])
    for sim in campaign:
        output_plot = _plot(
            index=sim.index,
            path=sim.path,
            conditions=sim.conditions,
            analysis_config=analysis_config,
        )
        if output_plot:
            outputs.append(
                {
                    "path": str(output_plot),
                    "report_type": analysis_config["report_type"],
                    "report_name": analysis_config["report_name"],
                    "node_sets": analysis_config["node_sets"],
                    "cell_step": analysis_config["cell_step"],
                    "simulation_ids": [sim.index],
                }
            )
    return {"outputs": outputs}
