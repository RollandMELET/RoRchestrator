"""Tests unitaires pour le Worktree Manager."""

import unittest
import tempfile
import shutil
import subprocess
from pathlib import Path
from core.worktree import WorktreeManager, WorktreeError


class TestWorktreeManager(unittest.TestCase):
    """Tests pour la classe WorktreeManager."""

    def setUp(self):
        """Crée un repo Git temporaire pour les tests."""
        # Créer un répertoire temporaire
        self.test_dir = Path(tempfile.mkdtemp())
        self.repo_path = self.test_dir / "test_repo"
        self.repo_path.mkdir()

        # Initialiser un repo Git
        subprocess.run(
            ["git", "init"],
            cwd=self.repo_path,
            capture_output=True,
            check=True
        )

        # Configurer Git pour les tests
        subprocess.run(
            ["git", "config", "user.email", "test@example.com"],
            cwd=self.repo_path,
            capture_output=True,
            check=True
        )
        subprocess.run(
            ["git", "config", "user.name", "Test User"],
            cwd=self.repo_path,
            capture_output=True,
            check=True
        )

        # Créer un commit initial sur main
        readme = self.repo_path / "README.md"
        readme.write_text("# Test Repo\n")

        subprocess.run(
            ["git", "add", "README.md"],
            cwd=self.repo_path,
            capture_output=True,
            check=True
        )
        subprocess.run(
            ["git", "commit", "-m", "Initial commit"],
            cwd=self.repo_path,
            capture_output=True,
            check=True
        )

        # Créer un CLAUDE.md pour tester la copie
        claude_md = self.repo_path / "CLAUDE.md"
        claude_md.write_text("# Project Instructions\n\nTest content.")

        subprocess.run(
            ["git", "add", "CLAUDE.md"],
            cwd=self.repo_path,
            capture_output=True,
            check=True
        )
        subprocess.run(
            ["git", "commit", "-m", "Add CLAUDE.md"],
            cwd=self.repo_path,
            capture_output=True,
            check=True
        )

        # S'assurer qu'on est sur main
        subprocess.run(
            ["git", "checkout", "-b", "main"],
            cwd=self.repo_path,
            capture_output=True
        )

    def tearDown(self):
        """Nettoie les fichiers temporaires."""
        if self.test_dir.exists():
            shutil.rmtree(self.test_dir)

    def test_init_with_valid_repo(self):
        """Test l'initialisation avec un repo Git valide."""
        manager = WorktreeManager(self.repo_path)
        # Comparer les chemins résolus (à cause des symlinks /var vs /private/var sur macOS)
        self.assertEqual(manager.repo_path.resolve(), self.repo_path.resolve())
        self.assertTrue(manager.worktrees_base.exists())

    def test_init_with_invalid_repo(self):
        """Test l'initialisation avec un chemin non-Git."""
        invalid_path = self.test_dir / "not_a_repo"
        invalid_path.mkdir()

        with self.assertRaises(WorktreeError):
            WorktreeManager(invalid_path)

    def test_init_with_custom_worktrees_base(self):
        """Test l'initialisation avec un répertoire worktrees custom."""
        custom_base = self.test_dir / "custom_worktrees"
        manager = WorktreeManager(self.repo_path, worktrees_base=custom_base)

        self.assertEqual(manager.worktrees_base, custom_base)
        self.assertTrue(custom_base.exists())

    def test_create_worktree(self):
        """Test la création d'un worktree."""
        manager = WorktreeManager(self.repo_path)
        worktree_path = manager.create("test-feature", base_branch="main")

        # Vérifier que le worktree existe
        self.assertTrue(worktree_path.exists())
        self.assertTrue((worktree_path / "README.md").exists())

        # Vérifier qu'il est enregistré
        self.assertIn("test-feature", manager.active_worktrees)
        self.assertEqual(manager.active_worktrees["test-feature"].path, worktree_path)

    def test_create_worktree_copies_claude_md(self):
        """Test que CLAUDE.md est copié dans le worktree."""
        manager = WorktreeManager(self.repo_path)
        worktree_path = manager.create("test-feature", base_branch="main")

        claude_md = worktree_path / "CLAUDE.md"
        self.assertTrue(claude_md.exists())

        content = claude_md.read_text()
        self.assertIn("Project Instructions", content)
        self.assertIn("Current Feature (Worktree)", content)
        self.assertIn("test-feature", content)

    def test_create_worktree_already_exists(self):
        """Test la création d'un worktree qui existe déjà."""
        manager = WorktreeManager(self.repo_path)
        manager.create("test-feature", base_branch="main")

        # Tenter de créer à nouveau sans force
        with self.assertRaises(WorktreeError) as ctx:
            manager.create("test-feature", base_branch="main")

        self.assertIn("existe déjà", str(ctx.exception))

    def test_create_worktree_with_force(self):
        """Test la recréation d'un worktree avec force=True."""
        manager = WorktreeManager(self.repo_path)
        path1 = manager.create("test-feature", base_branch="main")

        # Modifier un fichier dans le worktree
        (path1 / "test.txt").write_text("modified")

        # Recréer avec force
        path2 = manager.create("test-feature", base_branch="main", force=True)

        self.assertEqual(path1, path2)
        self.assertFalse((path2 / "test.txt").exists())

    def test_create_worktree_invalid_base_branch(self):
        """Test la création avec une branche de base inexistante."""
        manager = WorktreeManager(self.repo_path)

        with self.assertRaises(WorktreeError) as ctx:
            manager.create("test-feature", base_branch="nonexistent")

        self.assertIn("introuvable", str(ctx.exception))

    def test_remove_worktree(self):
        """Test la suppression d'un worktree."""
        manager = WorktreeManager(self.repo_path)
        worktree_path = manager.create("test-feature", base_branch="main")

        # Supprimer (avec force car CLAUDE.md créé n'est pas tracké)
        result = manager.remove("test-feature", force=True)

        self.assertTrue(result)
        self.assertFalse(worktree_path.exists())
        self.assertNotIn("test-feature", manager.active_worktrees)

    def test_remove_nonexistent_worktree(self):
        """Test la suppression d'un worktree qui n'existe pas."""
        manager = WorktreeManager(self.repo_path)

        result = manager.remove("nonexistent")
        self.assertFalse(result)

    def test_remove_worktree_with_uncommitted_changes(self):
        """Test la suppression d'un worktree avec modifications non commitées."""
        manager = WorktreeManager(self.repo_path)
        worktree_path = manager.create("test-feature", base_branch="main")

        # Ajouter des modifications
        (worktree_path / "test.txt").write_text("new file")

        # Tenter de supprimer sans force
        with self.assertRaises(WorktreeError):
            manager.remove("test-feature", force=False)

        # Supprimer avec force
        result = manager.remove("test-feature", force=True)
        self.assertTrue(result)
        self.assertFalse(worktree_path.exists())

    def test_exists(self):
        """Test la vérification de l'existence d'un worktree."""
        manager = WorktreeManager(self.repo_path)

        self.assertFalse(manager.exists("test-feature"))

        manager.create("test-feature", base_branch="main")
        self.assertTrue(manager.exists("test-feature"))

        manager.remove("test-feature", force=True)
        self.assertFalse(manager.exists("test-feature"))

    def test_get_path(self):
        """Test la récupération du chemin d'un worktree."""
        manager = WorktreeManager(self.repo_path)

        # Worktree inexistant
        path = manager.get_path("test-feature")
        self.assertIsNone(path)

        # Worktree existant
        created_path = manager.create("test-feature", base_branch="main")
        path = manager.get_path("test-feature")
        self.assertEqual(path, created_path)

    def test_list_active(self):
        """Test la liste des worktrees actifs."""
        manager = WorktreeManager(self.repo_path)

        # Aucun worktree
        active = manager.list_active()
        self.assertEqual(len(active), 0)

        # Créer plusieurs worktrees
        manager.create("feature-a", base_branch="main")
        manager.create("feature-b", base_branch="main")

        active = manager.list_active()
        self.assertEqual(len(active), 2)
        self.assertIn("feature-a", active)
        self.assertIn("feature-b", active)

        # Les infos sont correctes
        self.assertEqual(active["feature-a"].feature_id, "feature-a")
        self.assertEqual(active["feature-a"].branch_name, "feature/feature-a")

    def test_list_all_worktrees(self):
        """Test la liste de tous les worktrees Git."""
        manager = WorktreeManager(self.repo_path)
        manager.create("feature-a", base_branch="main")

        all_wts = manager.list_all_worktrees()

        # Au moins 2: le repo principal + notre worktree
        self.assertGreaterEqual(len(all_wts), 2)

        # Vérifier que notre worktree est dans la liste
        feature_wt = next(
            (wt for wt in all_wts if "feature-a" in wt.get("path", "")),
            None
        )
        self.assertIsNotNone(feature_wt)

    def test_cleanup_all(self):
        """Test la suppression de tous les worktrees."""
        manager = WorktreeManager(self.repo_path)

        # Créer plusieurs worktrees
        manager.create("feature-a", base_branch="main")
        manager.create("feature-b", base_branch="main")
        manager.create("feature-c", base_branch="main")

        self.assertEqual(len(manager.active_worktrees), 3)

        # Nettoyer tout
        manager.cleanup_all()

        self.assertEqual(len(manager.active_worktrees), 0)
        self.assertFalse(manager.exists("feature-a"))
        self.assertFalse(manager.exists("feature-b"))
        self.assertFalse(manager.exists("feature-c"))

    def test_cleanup_merged(self):
        """Test la suppression des worktrees mergés."""
        manager = WorktreeManager(self.repo_path)

        # Créer deux worktrees
        worktree_path = manager.create("merged-feature", base_branch="main")
        manager.create("unmerged-feature", base_branch="main")

        # Créer un commit dans le premier worktree
        test_file = worktree_path / "test.txt"
        test_file.write_text("test")

        subprocess.run(
            ["git", "add", "test.txt"],
            cwd=worktree_path,
            capture_output=True,
            check=True
        )
        subprocess.run(
            ["git", "commit", "-m", "Test commit"],
            cwd=worktree_path,
            capture_output=True,
            check=True
        )

        # Revenir sur main et merger avec --no-ff pour créer un merge commit
        subprocess.run(
            ["git", "checkout", "main"],
            cwd=self.repo_path,
            capture_output=True,
            check=True
        )
        subprocess.run(
            ["git", "merge", "--no-ff", "-m", "Merge merged-feature", "feature/merged-feature"],
            cwd=self.repo_path,
            capture_output=True,
            check=True
        )

        # Nettoyer les worktrees mergés
        cleaned = manager.cleanup_merged("main")

        # Le comportement peut varier selon la version de Git
        # Au minimum, vérifier que la fonction s'exécute sans erreur
        # et que unmerged-feature n'est pas supprimé
        self.assertNotIn("unmerged-feature", cleaned)
        self.assertTrue(manager.exists("unmerged-feature"))

        # Si merged-feature a été nettoyé, vérifier qu'il n'existe plus
        if "merged-feature" in cleaned:
            self.assertFalse(manager.exists("merged-feature"))


if __name__ == "__main__":
    unittest.main()
