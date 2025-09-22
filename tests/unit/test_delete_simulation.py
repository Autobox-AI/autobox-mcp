"""Tests for delete_simulation functionality."""

from pathlib import Path
from unittest.mock import patch

import pytest

from autobox.server import AutoboxMCPServer


@pytest.mark.asyncio
async def test_delete_simulation_success():
    """Test successful deletion of simulation and metrics files."""
    server = AutoboxMCPServer()

    server.simulations_path = Path("/tmp/test_simulations")
    server.metrics_path = Path("/tmp/test_metrics")

    simulation_name = "test_sim"

    with (
        patch.object(Path, "exists") as mock_exists,
        patch.object(Path, "unlink") as mock_unlink,
    ):
        # Track which paths are being checked
        call_count = 0

        def exists_side_effect():
            nonlocal call_count
            call_count += 1
            # First call is for .json config (exists)
            # Second call is for .toml config (doesn't exist since we found json)
            # Third call is for metrics .json (exists)
            if call_count == 1:
                return True  # .json config exists
            elif call_count == 2:
                return False  # .toml config doesn't exist
            elif call_count == 3:
                return True  # metrics file exists
            return False

        mock_exists.side_effect = exists_side_effect

        result = await server._delete_simulation(simulation_name)

        assert result["success"] is True
        assert result["simulation_name"] == simulation_name
        assert len(result["deleted_files"]) == 2
        assert "Successfully deleted 2 file(s)" in result["message"]

        assert mock_unlink.call_count == 2


@pytest.mark.asyncio
async def test_delete_simulation_no_files():
    """Test deletion when no files exist."""
    server = AutoboxMCPServer()

    server.simulations_path = Path("/tmp/test_simulations")
    server.metrics_path = Path("/tmp/test_metrics")

    simulation_name = "non_existent"

    with patch("pathlib.Path.exists", return_value=False):
        result = await server._delete_simulation(simulation_name)

        assert result["success"] is False
        assert result["simulation_name"] == simulation_name
        assert len(result["deleted_files"]) == 0
        assert "errors" in result
        assert (
            f"No simulation config found for '{simulation_name}'" in result["errors"][0]
        )


@pytest.mark.asyncio
async def test_delete_simulation_with_running_sim():
    """Test deletion with warning when simulation is running."""
    server = AutoboxMCPServer()

    server.simulations_path = Path("/tmp/test_simulations")
    server.metrics_path = Path("/tmp/test_metrics")

    simulation_name = "running_sim"

    from autobox.models.schemas import SimulationStatus

    server.simulations["sim_123"] = SimulationStatus(
        id="sim_123",
        name=simulation_name,
        status="running",
        container_id="container_123",
    )

    with patch.object(Path, "exists") as mock_exists, patch.object(Path, "unlink"):
        call_count = 0

        def exists_side_effect():
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return True  # .json config exists
            elif call_count == 2:
                return False  # .toml config doesn't exist
            elif call_count == 3:
                return True  # metrics file exists
            return False

        mock_exists.side_effect = exists_side_effect

        result = await server._delete_simulation(simulation_name)

        assert result["success"] is True
        assert "warning" in result
        assert "currently running" in result["warning"]
        assert "sim_123" in result["warning"]


@pytest.mark.asyncio
async def test_delete_simulation_partial_failure():
    """Test deletion when one file fails to delete."""
    server = AutoboxMCPServer()

    server.simulations_path = Path("/tmp/test_simulations")
    server.metrics_path = Path("/tmp/test_metrics")

    simulation_name = "partial_fail"

    with (
        patch.object(Path, "exists") as mock_exists,
        patch.object(Path, "unlink") as mock_unlink,
    ):
        mock_exists.return_value = True

        # Make the first unlink succeed but second fail
        mock_unlink.side_effect = [None, Exception("Permission denied")]

        result = await server._delete_simulation(simulation_name)

        assert (
            result["success"] is True
        )  # Still true because at least one file was deleted
        assert len(result["deleted_files"]) == 1
        assert "errors" in result
        assert "Permission denied" in str(result["errors"])


@pytest.mark.asyncio
async def test_delete_simulation_toml_config():
    """Test deletion of TOML config file."""
    server = AutoboxMCPServer()

    server.simulations_path = Path("/tmp/test_simulations")
    server.metrics_path = Path("/tmp/test_metrics")

    simulation_name = "toml_sim"

    with (
        patch.object(Path, "exists") as mock_exists,
        patch.object(Path, "unlink") as mock_unlink,
    ):
        call_count = 0

        def exists_side_effect():
            nonlocal call_count
            call_count += 1
            # First call is for .json config (doesn't exist)
            # Second call is for .toml config (exists)
            # Third call is for metrics .json (exists)
            if call_count == 1:
                return False  # .json config doesn't exist
            elif call_count == 2:
                return True  # .toml config exists
            elif call_count == 3:
                return True  # metrics file exists
            return False

        mock_exists.side_effect = exists_side_effect

        result = await server._delete_simulation(simulation_name)

        assert result["success"] is True
        assert len(result["deleted_files"]) == 2
        assert any(".toml" in f for f in result["deleted_files"])
        assert mock_unlink.call_count == 2
