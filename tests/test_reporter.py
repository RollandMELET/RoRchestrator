"""Tests unitaires pour le Reporter."""

import unittest
import json
import tempfile
from pathlib import Path
from datetime import datetime
from io import StringIO
import sys

from core.reporter import Reporter, ExecutionReport
from core.runner import ClaudeResult


class TestReporter(unittest.TestCase):
    """Tests pour la classe Reporter."""

    def test_init(self):
        """Test l'initialisation."""
        reporter = Reporter(verbose=True)
        self.assertTrue(reporter.verbose)
        self.assertEqual(len(reporter.results), 0)

    def test_add_result(self):
        """Test l'ajout d'un résultat."""
        reporter = Reporter()

        result = ClaudeResult(
            feature_id="test",
            success=True,
            result="Done",
            cost_usd=0.5,
            duration_ms=1000,
            session_id="abc"
        )

        reporter.add_result(result)
        self.assertEqual(len(reporter.results), 1)

    def test_add_results(self):
        """Test l'ajout de plusieurs résultats."""
        reporter = Reporter()

        results = [
            ClaudeResult("f1", True, "Done", 0.1, 100, "s1"),
            ClaudeResult("f2", True, "Done", 0.2, 200, "s2"),
        ]

        reporter.add_results(results)
        self.assertEqual(len(reporter.results), 2)

    def test_generate_report(self):
        """Test la génération d'un rapport."""
        reporter = Reporter()

        results = [
            ClaudeResult(
                "feature-1", True, "Done", 0.5, 1000, "s1",
                started_at=datetime(2026, 1, 2, 10, 0, 0),
                finished_at=datetime(2026, 1, 2, 10, 1, 0),
                num_turns=3
            ),
            ClaudeResult(
                "feature-2", True, "Done", 0.3, 800, "s2",
                started_at=datetime(2026, 1, 2, 10, 0, 30),
                finished_at=datetime(2026, 1, 2, 10, 1, 30),
                num_turns=2
            ),
            ClaudeResult(
                "feature-3", False, "", 0.0, 0, "",
                error="Timeout",
                started_at=datetime(2026, 1, 2, 10, 0, 45),
                finished_at=datetime(2026, 1, 2, 10, 31, 0)
            ),
        ]

        reporter.add_results(results)

        waves = [["feature-1"], ["feature-2", "feature-3"]]
        report = reporter.generate_report("TestProject", waves)

        self.assertEqual(report.project_name, "TestProject")
        self.assertEqual(report.total_features, 3)
        self.assertEqual(report.successful, 2)
        self.assertEqual(report.failed, 1)
        self.assertEqual(report.total_cost_usd, 0.8)
        self.assertEqual(report.total_duration_ms, 1800)
        self.assertEqual(len(report.branches_created), 2)
        self.assertIn("feature/feature-1", report.branches_created)
        self.assertIn("feature/feature-2", report.branches_created)
        self.assertEqual(len(report.errors), 1)
        self.assertEqual(report.errors[0]["feature_id"], "feature-3")

    def test_generate_report_no_results(self):
        """Test la génération de rapport sans résultats."""
        reporter = Reporter()

        with self.assertRaises(ValueError):
            reporter.generate_report("TestProject", [])

    def test_save_report(self):
        """Test la sauvegarde d'un rapport en JSON."""
        reporter = Reporter()

        result = ClaudeResult(
            "f1", True, "Done", 0.5, 1000, "s1",
            started_at=datetime(2026, 1, 2, 10, 0, 0),
            finished_at=datetime(2026, 1, 2, 10, 1, 0)
        )
        reporter.add_result(result)

        report = reporter.generate_report("TestProject", [["f1"]])

        # Sauvegarder dans un fichier temporaire
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
            temp_path = Path(f.name)

        try:
            reporter.save_report(report, temp_path)

            # Vérifier que le fichier a été créé
            self.assertTrue(temp_path.exists())

            # Vérifier le contenu
            with open(temp_path) as f:
                data = json.load(f)

            self.assertEqual(data["project_name"], "TestProject")
            self.assertEqual(data["successful"], 1)
            self.assertEqual(data["failed"], 0)

        finally:
            # Cleanup
            if temp_path.exists():
                temp_path.unlink()

    def test_save_results(self):
        """Test la sauvegarde des résultats bruts."""
        reporter = Reporter()

        results = [
            ClaudeResult("f1", True, "Done", 0.5, 1000, "s1"),
            ClaudeResult("f2", False, "", 0.0, 0, "", error="Failed"),
        ]
        reporter.add_results(results)

        # Sauvegarder dans un fichier temporaire
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
            temp_path = Path(f.name)

        try:
            reporter.save_results(temp_path)

            # Vérifier le contenu
            with open(temp_path) as f:
                data = json.load(f)

            self.assertEqual(len(data), 2)
            self.assertEqual(data[0]["feature_id"], "f1")
            self.assertTrue(data[0]["success"])
            self.assertEqual(data[1]["feature_id"], "f2")
            self.assertFalse(data[1]["success"])

        finally:
            if temp_path.exists():
                temp_path.unlink()

    def test_display_dag(self):
        """Test l'affichage du DAG."""
        reporter = Reporter()

        waves = [["auth"], ["api", "batch"], ["dashboard"]]
        features = {
            "auth": {"id": "auth", "name": "Auth", "depends_on": []},
            "api": {"id": "api", "name": "API", "depends_on": ["auth"], "estimated_tokens": 30000},
            "batch": {"id": "batch", "name": "Batch", "depends_on": ["auth"]},
            "dashboard": {"id": "dashboard", "name": "Dashboard", "depends_on": ["api", "batch"]},
        }

        # Capturer stdout
        captured_output = StringIO()
        sys.stdout = captured_output

        reporter.display_dag(waves, features)

        sys.stdout = sys.__stdout__
        output = captured_output.getvalue()

        # Vérifier le contenu
        self.assertIn("PLAN D'EXÉCUTION", output)
        self.assertIn("VAGUE 1", output)
        self.assertIn("VAGUE 2", output)
        self.assertIn("PARALLÈLE", output)
        self.assertIn("auth", output)
        self.assertIn("30,000 tokens", output)

    def test_display_progress(self):
        """Test l'affichage de la progression."""
        reporter = Reporter(verbose=True)

        # Capturer stdout
        captured_output = StringIO()
        sys.stdout = captured_output

        reporter.display_progress("test-feature", "started")
        reporter.display_progress("test-feature", "completed")
        reporter.display_progress("test-feature", "failed")

        sys.stdout = sys.__stdout__
        output = captured_output.getvalue()

        self.assertIn("🚀", output)
        self.assertIn("✅", output)
        self.assertIn("❌", output)
        self.assertIn("test-feature", output)


class TestExecutionReport(unittest.TestCase):
    """Tests pour ExecutionReport."""

    def test_to_dict(self):
        """Test la conversion en dictionnaire."""
        report = ExecutionReport(
            project_name="Test",
            started_at=datetime(2026, 1, 2, 10, 0, 0),
            finished_at=datetime(2026, 1, 2, 11, 0, 0),
            total_features=5,
            successful=4,
            failed=1,
            total_cost_usd=2.5,
            total_duration_ms=120000,
            waves=[{"wave": 1, "features": ["a", "b"]}],
            branches_created=["feature/a", "feature/b"],
            errors=[{"feature_id": "c", "error": "Failed"}]
        )

        data = report.to_dict()

        self.assertEqual(data["project_name"], "Test")
        self.assertEqual(data["total_features"], 5)
        self.assertEqual(data["started_at"], "2026-01-02T10:00:00")
        self.assertEqual(data["finished_at"], "2026-01-02T11:00:00")


if __name__ == "__main__":
    unittest.main()
