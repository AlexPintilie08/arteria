from pathlib import Path

from sim.sumo_support import discover_sumo


def test_sumo_home_discovery_is_portable(tmp_path: Path) -> None:
    binary_dir = tmp_path / "bin"
    binary_dir.mkdir()
    sumo = binary_dir / "sumo"
    netconvert = binary_dir / "netconvert"
    sumo.write_text("", encoding="utf-8")
    netconvert.write_text("", encoding="utf-8")

    result = discover_sumo({"SUMO_HOME": str(tmp_path)}, search_path="")

    assert result.sumo == sumo.resolve()
    assert result.netconvert == netconvert.resolve()
    assert result.home == tmp_path.resolve()
