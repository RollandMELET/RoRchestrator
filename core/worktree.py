"""Git Worktree Manager pour isolation des features."""

import subprocess
import shutil
from pathlib import Path
from typing import Optional, Dict, List
from dataclasses import dataclass


@dataclass
class WorktreeInfo:
    """Information sur un worktree actif.

    Attributes:
        feature_id: Identifiant de la feature
        path: Chemin absolu vers le worktree
        branch_name: Nom de la branche Git
    """
    feature_id: str
    path: Path
    branch_name: str


class WorktreeError(Exception):
    """Exception levée lors d'erreurs de gestion des worktrees."""
    pass


class WorktreeManager:
    """Gère les Git worktrees pour l'isolation des features.

    Permet de créer des environnements isolés pour chaque feature,
    chacun dans son propre working directory avec sa propre branche.

    Attributes:
        repo_path: Chemin vers le repo Git principal
        worktrees_base: Répertoire de base pour les worktrees
        active_worktrees: Dict des worktrees actifs (feature_id -> WorktreeInfo)

    Example:
        >>> manager = WorktreeManager("/path/to/repo")
        >>> worktree_path = manager.create("auth-gtin", base_branch="main")
        >>> # Travailler dans le worktree...
        >>> manager.remove("auth-gtin")
    """

    def __init__(self, repo_path: Path, worktrees_base: Optional[Path] = None):
        """Initialise le manager de worktrees.

        Args:
            repo_path: Chemin vers le repo Git principal
            worktrees_base: Répertoire de base pour les worktrees.
                          Par défaut: ../worktrees/ (sibling du repo)

        Raises:
            WorktreeError: Si repo_path n'est pas un repo Git valide
        """
        self.repo_path = Path(repo_path).resolve()

        # Vérifier que c'est un repo Git
        if not (self.repo_path / ".git").exists():
            raise WorktreeError(f"'{self.repo_path}' n'est pas un repo Git valide")

        self.worktrees_base = worktrees_base or self.repo_path.parent / "worktrees"
        self.worktrees_base.mkdir(exist_ok=True)
        self.active_worktrees: Dict[str, WorktreeInfo] = {}

    def create(
        self,
        feature_id: str,
        base_branch: str = "main",
        force: bool = False
    ) -> Path:
        """Crée un worktree isolé pour une feature.

        Args:
            feature_id: Identifiant de la feature
            base_branch: Branche de base pour créer la nouvelle branche
            force: Si True, supprime le worktree existant avant de créer

        Returns:
            Chemin absolu vers le worktree créé

        Raises:
            WorktreeError: Si la création échoue

        Example:
            >>> path = manager.create("auth-gtin", base_branch="develop")
        """
        worktree_path = self.worktrees_base / feature_id
        branch_name = f"feature/{feature_id}"

        # Supprimer si existe déjà et force=True
        if worktree_path.exists():
            if force:
                self.remove(feature_id, force=True)
                # Supprimer aussi la branche si elle existe
                subprocess.run(
                    ["git", "branch", "-D", branch_name],
                    cwd=self.repo_path,
                    capture_output=True
                )
            else:
                raise WorktreeError(
                    f"Worktree '{feature_id}' existe déjà. "
                    "Utilisez force=True pour le recréer."
                )

        # Vérifier que la branche de base existe
        result = subprocess.run(
            ["git", "rev-parse", "--verify", base_branch],
            cwd=self.repo_path,
            capture_output=True,
            text=True
        )
        if result.returncode != 0:
            raise WorktreeError(f"Branche de base '{base_branch}' introuvable")

        # Créer le worktree avec nouvelle branche
        result = subprocess.run(
            ["git", "worktree", "add", "-b", branch_name, str(worktree_path), base_branch],
            cwd=self.repo_path,
            capture_output=True,
            text=True
        )

        if result.returncode != 0:
            raise WorktreeError(f"Erreur création worktree: {result.stderr}")

        # Enregistrer le worktree actif
        info = WorktreeInfo(
            feature_id=feature_id,
            path=worktree_path,
            branch_name=branch_name
        )
        self.active_worktrees[feature_id] = info

        # Configurer CLAUDE.md si présent
        self._setup_claude_md(worktree_path, feature_id)

        return worktree_path

    def remove(self, feature_id: str, force: bool = False) -> bool:
        """Supprime un worktree.

        Args:
            feature_id: Identifiant de la feature
            force: Si True, force la suppression même avec modifications non commitées

        Returns:
            True si supprimé, False si n'existait pas

        Raises:
            WorktreeError: Si la suppression échoue
        """
        worktree_path = self.worktrees_base / feature_id

        if not worktree_path.exists():
            # Retirer de la liste des actifs si présent
            self.active_worktrees.pop(feature_id, None)
            return False

        cmd = ["git", "worktree", "remove"]
        if force:
            cmd.append("--force")
        cmd.append(str(worktree_path))

        result = subprocess.run(
            cmd,
            cwd=self.repo_path,
            capture_output=True,
            text=True
        )

        if result.returncode != 0:
            raise WorktreeError(
                f"Erreur suppression worktree '{feature_id}': {result.stderr}"
            )

        self.active_worktrees.pop(feature_id, None)
        return True

    def cleanup_all(self):
        """Supprime tous les worktrees actifs et nettoie les références.

        Attention: Cette opération est destructive !
        """
        # Supprimer tous les worktrees actifs
        for feature_id in list(self.active_worktrees.keys()):
            try:
                self.remove(feature_id, force=True)
            except WorktreeError:
                pass  # Continuer même si une suppression échoue

        # Nettoyer les références orphelines
        subprocess.run(
            ["git", "worktree", "prune"],
            cwd=self.repo_path,
            capture_output=True
        )

    def cleanup_merged(self, target_branch: str = "main") -> List[str]:
        """Supprime les worktrees dont la branche a été mergée.

        Args:
            target_branch: Branche cible (généralement 'main' ou 'develop')

        Returns:
            Liste des feature_ids supprimés

        Example:
            >>> cleaned = manager.cleanup_merged("main")
            >>> print(f"Nettoyé: {cleaned}")
        """
        # Récupérer les branches mergées
        result = subprocess.run(
            ["git", "branch", "--merged", target_branch],
            cwd=self.repo_path,
            capture_output=True,
            text=True
        )

        if result.returncode != 0:
            raise WorktreeError(f"Erreur lors de la vérification des branches mergées: {result.stderr}")

        # Parser les branches mergées (retirer les espaces et *)
        merged_branches = set(
            line.strip().lstrip('*').strip()
            for line in result.stdout.strip().split("\n")
            if line.strip()
        )

        cleaned = []
        for feature_id, info in list(self.active_worktrees.items()):
            if info.branch_name in merged_branches:
                try:
                    self.remove(feature_id)

                    # Supprimer aussi la branche
                    subprocess.run(
                        ["git", "branch", "-d", info.branch_name],
                        cwd=self.repo_path,
                        capture_output=True
                    )

                    cleaned.append(feature_id)
                except WorktreeError:
                    pass  # Continuer même si une suppression échoue

        return cleaned

    def list_active(self) -> Dict[str, WorktreeInfo]:
        """Liste les worktrees actifs gérés par ce manager.

        Returns:
            Dictionnaire des worktrees actifs (feature_id -> WorktreeInfo)
        """
        return self.active_worktrees.copy()

    def list_all_worktrees(self) -> List[Dict[str, str]]:
        """Liste TOUS les worktrees Git (même ceux non gérés par ce manager).

        Returns:
            Liste de dictionnaires avec les infos de chaque worktree

        Example:
            >>> worktrees = manager.list_all_worktrees()
            >>> for wt in worktrees:
            ...     print(f"{wt['path']} -> {wt['branch']}")
        """
        result = subprocess.run(
            ["git", "worktree", "list", "--porcelain"],
            cwd=self.repo_path,
            capture_output=True,
            text=True
        )

        if result.returncode != 0:
            raise WorktreeError(f"Erreur listing worktrees: {result.stderr}")

        worktrees = []
        current = {}

        for line in result.stdout.split("\n"):
            line = line.strip()
            if not line:
                if current:
                    worktrees.append(current)
                    current = {}
                continue

            if line.startswith("worktree "):
                current["path"] = line[9:]
            elif line.startswith("branch "):
                current["branch"] = line[7:]
            elif line.startswith("HEAD "):
                current["head"] = line[5:]

        if current:
            worktrees.append(current)

        return worktrees

    def exists(self, feature_id: str) -> bool:
        """Vérifie si un worktree existe pour une feature.

        Args:
            feature_id: Identifiant de la feature

        Returns:
            True si le worktree existe
        """
        worktree_path = self.worktrees_base / feature_id
        return worktree_path.exists()

    def get_path(self, feature_id: str) -> Optional[Path]:
        """Récupère le chemin d'un worktree actif.

        Args:
            feature_id: Identifiant de la feature

        Returns:
            Chemin du worktree ou None si n'existe pas
        """
        info = self.active_worktrees.get(feature_id)
        return info.path if info else None

    def _setup_claude_md(self, worktree_path: Path, feature_id: str):
        """Configure CLAUDE.md pour le worktree.

        Crée un CLAUDE.md simplifié spécifique au worktree,
        sans le workflow de session qui pourrait interférer.

        Args:
            worktree_path: Chemin du worktree
            feature_id: ID de la feature
        """
        target_claude_md = worktree_path / "CLAUDE.md"

        # Créer un CLAUDE.md simplifié pour le worktree
        content = f"""# CLAUDE.md - Worktree Feature

## Current Feature

**Feature ID:** {feature_id}
**Branch:** feature/{feature_id}
**Worktree:** {worktree_path}

## Context

This is an isolated worktree created by RoRchestrator for parallel development.

**Your task:** Implement the feature as described in the prompt.

**Focus:** Work only on this feature. Other features are being developed in parallel in separate worktrees.

## Important

- Create the files and code as specified in the prompt
- Write tests for your implementation
- Commit your changes when done
- Do NOT work on other features
- Do NOT modify files outside the scope of this feature

## Project Structure

See the main README.md for overall project structure and conventions.
"""

        target_claude_md.write_text(content)
