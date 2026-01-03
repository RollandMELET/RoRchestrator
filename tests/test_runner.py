"""Tests unitaires pour le Claude Runner."""

import unittest
import asyncio
import json
import tempfile
from pathlib import Path
from datetime import datetime
from unittest.mock import patch, MagicMock, AsyncMock
from core.runner import ClaudeRunner, ClaudeResult


class TestClaudeRunner(unittest.TestCase):
    """Tests pour la classe ClaudeRunner."""

    def test_init_default_parameters(self):
        """Test l'initialisation avec paramètres par défaut."""
        runner = ClaudeRunner()

        self.assertEqual(runner.max_parallel, 3)
        self.assertEqual(runner.permission_mode, "acceptEdits")
        self.assertIsNotNone(runner.allowed_tools)
        self.assertEqual(runner.timeout_seconds, 1800)
        self.assertEqual(runner.claude_binary, "claude")

    def test_init_custom_parameters(self):
        """Test l'initialisation avec paramètres personnalisés."""
        custom_tools = ["Read", "Write"]
        runner = ClaudeRunner(
            max_parallel=5,
            permission_mode="askUser",
            allowed_tools=custom_tools,
            timeout_seconds=3600,
            claude_binary="/custom/path/claude"
        )

        self.assertEqual(runner.max_parallel, 5)
        self.assertEqual(runner.permission_mode, "askUser")
        self.assertEqual(runner.allowed_tools, custom_tools)
        self.assertEqual(runner.timeout_seconds, 3600)
        self.assertEqual(runner.claude_binary, "/custom/path/claude")

    def test_check_claude_available_when_present(self):
        """Test la vérification de disponibilité de Claude (présent)."""
        runner = ClaudeRunner(claude_binary="echo")  # echo existe toujours

        # echo --version retourne 0
        available = runner.check_claude_available()
        self.assertTrue(available)

    def test_check_claude_available_when_absent(self):
        """Test la vérification de disponibilité de Claude (absent)."""
        runner = ClaudeRunner(claude_binary="nonexistent_binary_xyz")

        available = runner.check_claude_available()
        self.assertFalse(available)

    def test_get_claude_version(self):
        """Test la récupération de la version Claude."""
        # Utiliser 'echo' pour simuler (retourne une chaîne)
        runner = ClaudeRunner(claude_binary="echo")

        version = runner.get_claude_version()
        # echo --version affiche "--version"
        self.assertIsNotNone(version)

    def test_get_claude_version_when_unavailable(self):
        """Test la récupération de version quand Claude est absent."""
        runner = ClaudeRunner(claude_binary="nonexistent_binary_xyz")

        version = runner.get_claude_version()
        self.assertIsNone(version)


class TestClaudeRunnerAsync(unittest.IsolatedAsyncioTestCase):
    """Tests asynchrones pour ClaudeRunner."""

    async def test_run_single_success(self):
        """Test une exécution réussie."""
        runner = ClaudeRunner()

        # Mock du subprocess
        mock_json = {
            "type": "result",
            "subtype": "success",
            "total_cost_usd": 0.003,
            "duration_ms": 1234,
            "num_turns": 5,
            "result": "Feature implemented successfully",
            "session_id": "test-session-123"
        }

        with patch("asyncio.create_subprocess_exec") as mock_exec:
            # Configurer le mock
            mock_process = AsyncMock()
            mock_process.returncode = 0
            mock_process.communicate = AsyncMock(
                return_value=(
                    json.dumps(mock_json).encode(),
                    b""
                )
            )
            mock_exec.return_value = mock_process

            # Exécuter
            result = await runner.run_single(
                worktree_path=Path("/tmp/test"),
                prompt="Test prompt",
                feature_id="test-feature"
            )

            # Vérifier
            self.assertTrue(result.success)
            self.assertEqual(result.feature_id, "test-feature")
            self.assertEqual(result.cost_usd, 0.003)
            self.assertEqual(result.duration_ms, 1234)
            self.assertEqual(result.session_id, "test-session-123")
            self.assertEqual(result.num_turns, 5)
            self.assertIsNone(result.error)

    async def test_run_single_process_error(self):
        """Test une exécution avec erreur de processus."""
        runner = ClaudeRunner()

        with patch("asyncio.create_subprocess_exec") as mock_exec:
            mock_process = AsyncMock()
            mock_process.returncode = 1
            mock_process.communicate = AsyncMock(
                return_value=(b"", b"Error: something went wrong")
            )
            mock_exec.return_value = mock_process

            result = await runner.run_single(
                worktree_path=Path("/tmp/test"),
                prompt="Test prompt",
                feature_id="test-feature"
            )

            self.assertFalse(result.success)
            self.assertIn("something went wrong", result.error)

    async def test_run_single_timeout(self):
        """Test une exécution qui timeout."""
        runner = ClaudeRunner(timeout_seconds=1)

        with patch("asyncio.create_subprocess_exec") as mock_exec:
            # Simuler un processus qui ne termine jamais
            mock_process = AsyncMock()
            mock_process.communicate = AsyncMock(
                side_effect=asyncio.TimeoutError()
            )
            mock_exec.return_value = mock_process

            result = await runner.run_single(
                worktree_path=Path("/tmp/test"),
                prompt="Test prompt",
                feature_id="test-feature"
            )

            self.assertFalse(result.success)
            self.assertIn("Timeout", result.error)
            self.assertIn("1s", result.error)

    async def test_run_single_json_parse_error(self):
        """Test une exécution avec JSON invalide."""
        runner = ClaudeRunner()

        with patch("asyncio.create_subprocess_exec") as mock_exec:
            mock_process = AsyncMock()
            mock_process.returncode = 0
            mock_process.communicate = AsyncMock(
                return_value=(b"not valid json", b"")
            )
            mock_exec.return_value = mock_process

            result = await runner.run_single(
                worktree_path=Path("/tmp/test"),
                prompt="Test prompt",
                feature_id="test-feature"
            )

            self.assertFalse(result.success)
            self.assertIn("JSON parse error", result.error)

    async def test_run_single_file_not_found(self):
        """Test l'exécution avec binaire Claude introuvable."""
        runner = ClaudeRunner(claude_binary="nonexistent_binary_xyz")

        result = await runner.run_single(
            worktree_path=Path("/tmp/test"),
            prompt="Test prompt",
            feature_id="test-feature"
        )

        self.assertFalse(result.success)
        self.assertIn("not found", result.error)

    async def test_run_wave_parallel(self):
        """Test l'exécution parallèle d'une vague."""
        runner = ClaudeRunner(max_parallel=2)

        mock_json = {
            "type": "result",
            "subtype": "success",
            "total_cost_usd": 0.001,
            "duration_ms": 500,
            "result": "Done",
            "session_id": "session-123"
        }

        with patch("asyncio.create_subprocess_exec") as mock_exec:
            mock_process = AsyncMock()
            mock_process.returncode = 0
            mock_process.communicate = AsyncMock(
                return_value=(json.dumps(mock_json).encode(), b"")
            )
            mock_exec.return_value = mock_process

            # Créer 3 tasks
            tasks = [
                (Path("/tmp/wt1"), "Prompt 1", "feature-1"),
                (Path("/tmp/wt2"), "Prompt 2", "feature-2"),
                (Path("/tmp/wt3"), "Prompt 3", "feature-3"),
            ]

            # Callback pour suivre la progression
            progress_log = []

            def on_progress(feature_id, status):
                progress_log.append((feature_id, status))

            results = await runner.run_wave(tasks, on_progress=on_progress)

            # Vérifier les résultats
            self.assertEqual(len(results), 3)
            self.assertTrue(all(r.success for r in results))
            self.assertEqual(results[0].feature_id, "feature-1")
            self.assertEqual(results[1].feature_id, "feature-2")
            self.assertEqual(results[2].feature_id, "feature-3")

            # Vérifier que les callbacks ont été appelés
            self.assertEqual(len(progress_log), 6)  # 3 started + 3 completed

    async def test_run_sequential(self):
        """Test l'exécution séquentielle."""
        runner = ClaudeRunner()

        mock_json = {
            "type": "result",
            "subtype": "success",
            "total_cost_usd": 0.001,
            "duration_ms": 500,
            "result": "Done",
            "session_id": "session-123"
        }

        with patch("asyncio.create_subprocess_exec") as mock_exec:
            mock_process = AsyncMock()
            mock_process.returncode = 0
            mock_process.communicate = AsyncMock(
                return_value=(json.dumps(mock_json).encode(), b"")
            )
            mock_exec.return_value = mock_process

            tasks = [
                (Path("/tmp/wt1"), "Prompt 1", "feature-1"),
                (Path("/tmp/wt2"), "Prompt 2", "feature-2"),
            ]

            results = await runner.run_sequential(tasks)

            self.assertEqual(len(results), 2)
            self.assertTrue(all(r.success for r in results))


class TestClaudeResult(unittest.TestCase):
    """Tests pour la classe ClaudeResult."""

    def test_to_dict(self):
        """Test la conversion en dictionnaire."""
        result = ClaudeResult(
            feature_id="test",
            success=True,
            result="Done",
            cost_usd=0.5,
            duration_ms=1000,
            session_id="abc123",
            started_at=datetime(2026, 1, 2, 10, 0, 0),
            finished_at=datetime(2026, 1, 2, 10, 1, 0),
            num_turns=3
        )

        data = result.to_dict()

        self.assertEqual(data["feature_id"], "test")
        self.assertTrue(data["success"])
        self.assertEqual(data["cost_usd"], 0.5)
        self.assertEqual(data["started_at"], "2026-01-02T10:00:00")
        self.assertEqual(data["finished_at"], "2026-01-02T10:01:00")


if __name__ == "__main__":
    unittest.main()
