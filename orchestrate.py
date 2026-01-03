#!/usr/bin/env python3
"""RoRchestrator - CLI pour orchestration parallèle de Claude Code.

Usage:
    orchestrate.py plan [--config CONFIG]
    orchestrate.py run [--config CONFIG] [--yes] [--sequential]
    orchestrate.py cleanup [--merged] [--all]
    orchestrate.py status [--config CONFIG]
"""

import argparse
import asyncio
import json
import sys
from pathlib import Path
from typing import Dict, List, Optional

from core.dag import DAGResolver
from core.worktree import WorktreeManager, WorktreeError
from core.runner import ClaudeRunner
from core.reporter import Reporter


class OrchestratorConfig:
    """Configuration de l'orchestrateur chargée depuis feature_list.json.

    Attributes:
        project_name: Nom du projet
        repo_path: Chemin vers le repo Git
        base_branch: Branche de base (main, master, develop)
        max_parallel: Nombre max d'exécutions parallèles
        timeout_seconds: Timeout par feature
        permission_mode: Mode permissions Claude
        allowed_tools: Liste des outils autorisés
        features: Liste des features à exécuter
        prompts_dir: Répertoire des fichiers prompts
    """

    def __init__(self, config_path: Path):
        """Charge la configuration depuis un fichier JSON.

        Args:
            config_path: Chemin vers feature_list.json

        Raises:
            FileNotFoundError: Si le fichier n'existe pas
            ValueError: Si le JSON est invalide
        """
        if not config_path.exists():
            raise FileNotFoundError(f"Config file not found: {config_path}")

        with open(config_path) as f:
            try:
                data = json.load(f)
            except json.JSONDecodeError as e:
                raise ValueError(f"Invalid JSON in config file: {e}")

        # Charger les paramètres du projet
        project = data.get("project", {})
        self.project_name = project.get("name", "UnnamedProject")
        self.repo_path = Path(project.get("repo_path", Path.cwd()))
        self.base_branch = project.get("base_branch", "main")
        self.max_parallel = project.get("max_parallel", 3)
        self.timeout_seconds = project.get("timeout_seconds", 1800)

        # Charger les paramètres Claude
        claude_config = data.get("claude", {})
        self.permission_mode = claude_config.get("permission_mode", "acceptEdits")
        self.allowed_tools = claude_config.get("allowed_tools", None)

        # Charger les features
        self.features = data.get("features", [])
        if not self.features:
            raise ValueError("No features defined in config")

        # Répertoire des prompts (relatif au fichier de config)
        self.prompts_dir = config_path.parent.parent / "prompts"


class Orchestrator:
    """Orchestrateur principal."""

    def __init__(self, config: OrchestratorConfig):
        """Initialise l'orchestrateur.

        Args:
            config: Configuration chargée
        """
        self.config = config
        self.dag = DAGResolver(config.features)
        self.worktree_mgr = WorktreeManager(config.repo_path)
        self.runner = ClaudeRunner(
            max_parallel=config.max_parallel,
            permission_mode=config.permission_mode,
            allowed_tools=config.allowed_tools,
            timeout_seconds=config.timeout_seconds
        )
        self.reporter = Reporter(verbose=True)

    def validate(self) -> bool:
        """Valide la configuration et le DAG.

        Returns:
            True si tout est valide

        Prints:
            Messages d'erreur sur stderr si invalide
        """
        errors = self.dag.validate()

        if errors:
            print("❌ Erreurs de validation du DAG:\n", file=sys.stderr)
            for error in errors:
                print(f"  • {error}", file=sys.stderr)
            return False

        return True

    def load_prompt(self, feature_id: str) -> str:
        """Charge le prompt pour une feature.

        Args:
            feature_id: ID de la feature

        Returns:
            Contenu du prompt

        Raises:
            FileNotFoundError: Si le fichier prompt n'existe pas
        """
        feature = self.dag.get_feature(feature_id)
        if not feature:
            raise ValueError(f"Feature '{feature_id}' not found")

        prompt_file = feature.get("prompt_file")
        if not prompt_file:
            raise ValueError(f"Feature '{feature_id}' has no prompt_file defined")

        prompt_path = self.config.prompts_dir / prompt_file
        if not prompt_path.exists():
            raise FileNotFoundError(f"Prompt file not found: {prompt_path}")

        return prompt_path.read_text()

    async def execute_waves(self, waves: List[List[str]]) -> bool:
        """Exécute toutes les vagues de features.

        Args:
            waves: Vagues d'exécution calculées par le DAG

        Returns:
            True si toutes les features ont réussi
        """
        all_success = True

        for wave_num, wave in enumerate(waves, 1):
            print(f"\n  ▶️  VAGUE {wave_num}/{len(waves)} - {len(wave)} feature(s)")

            # Créer les worktrees et préparer les tasks
            tasks = []
            for feature_id in wave:
                try:
                    worktree_path = self.worktree_mgr.create(
                        feature_id,
                        base_branch=self.config.base_branch,
                        force=True
                    )

                    prompt = self.load_prompt(feature_id)
                    tasks.append((worktree_path, prompt, feature_id))

                except Exception as e:
                    print(f"  ❌ Erreur préparation '{feature_id}': {e}")
                    all_success = False
                    continue

            # Exécuter la vague
            if tasks:
                results = await self.runner.run_wave(
                    tasks,
                    on_progress=self.reporter.display_progress
                )
                self.reporter.add_results(results)

                # Vérifier les échecs
                for result in results:
                    if not result.success:
                        all_success = False

        return all_success


def cmd_plan(args):
    """Commande 'plan': Affiche le plan d'exécution sans exécuter."""
    config_path = Path(args.config)

    try:
        config = OrchestratorConfig(config_path)
        orchestrator = Orchestrator(config)

        if not orchestrator.validate():
            return 1

        waves = orchestrator.dag.get_execution_waves()
        features_dict = {f["id"]: f for f in config.features}

        orchestrator.reporter.display_dag(waves, features_dict)

        # Afficher les estimations
        total_tokens = sum(f.get("estimated_tokens", 0) for f in config.features)
        print(f"\n  💰 Tokens estimés: {total_tokens:,}")
        print(f"  ⚡ Speedup théorique: {len(config.features) / len(waves):.1f}x")
        print()

        return 0

    except Exception as e:
        print(f"❌ Erreur: {e}", file=sys.stderr)
        return 1


def cmd_run(args):
    """Commande 'run': Exécute les features."""
    config_path = Path(args.config)

    try:
        config = OrchestratorConfig(config_path)
        orchestrator = Orchestrator(config)

        if not orchestrator.validate():
            return 1

        waves = orchestrator.dag.get_execution_waves()
        features_dict = {f["id"]: f for f in config.features}

        # Afficher le plan
        orchestrator.reporter.display_dag(waves, features_dict)

        # Demander confirmation si --yes n'est pas fourni
        if not args.yes:
            response = input("\n  Lancer l'exécution ? [o/N] : ").strip().lower()
            if response != 'o':
                print("  ⏹️  Exécution annulée.")
                return 0

        # Vérifier que Claude est disponible
        if not orchestrator.runner.check_claude_available():
            print("\n❌ Claude CLI n'est pas disponible.", file=sys.stderr)
            print("   Vérifiez que 'claude' est dans votre PATH.", file=sys.stderr)
            return 1

        # Exécuter
        print("\n" + "═" * 60)
        print("  🚀 DÉMARRAGE DE L'EXÉCUTION")
        print("═" * 60)

        success = asyncio.run(orchestrator.execute_waves(waves))

        # Générer le rapport
        print("\n" + "═" * 60)
        print("  📊 GÉNÉRATION DU RAPPORT")
        print("═" * 60)

        report = orchestrator.reporter.generate_report(config.project_name, waves)
        orchestrator.reporter.display_report(report)

        # Sauvegarder le rapport
        output_dir = Path.cwd() / "reports"
        output_dir.mkdir(exist_ok=True)

        from datetime import datetime
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_path = output_dir / f"report_{timestamp}.json"
        results_path = output_dir / f"results_{timestamp}.json"

        orchestrator.reporter.save_report(report, report_path)
        orchestrator.reporter.save_results(results_path)

        print(f"\n  💾 Rapports sauvegardés:")
        print(f"    • {report_path}")
        print(f"    • {results_path}")

        return 0 if success else 1

    except Exception as e:
        print(f"❌ Erreur: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 1


def cmd_cleanup(args):
    """Commande 'cleanup': Nettoie les worktrees."""
    try:
        # Trouver le repo (soit depuis config, soit depuis cwd)
        if args.config:
            config = OrchestratorConfig(Path(args.config))
            repo_path = config.repo_path
        else:
            repo_path = Path.cwd()

        worktree_mgr = WorktreeManager(repo_path)

        if args.all:
            print("  🧹 Nettoyage de TOUS les worktrees...")
            worktree_mgr.cleanup_all()
            print("  ✅ Tous les worktrees supprimés")

        elif args.merged:
            print("  🧹 Nettoyage des worktrees mergés...")
            cleaned = worktree_mgr.cleanup_merged()

            if cleaned:
                print(f"  ✅ {len(cleaned)} worktrees nettoyés:")
                for fid in cleaned:
                    print(f"    • {fid}")
            else:
                print("  ℹ️  Aucun worktree mergé trouvé")

        else:
            print("  ℹ️  Utilisez --merged ou --all")
            return 1

        return 0

    except WorktreeError as e:
        print(f"❌ Erreur: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"❌ Erreur inattendue: {e}", file=sys.stderr)
        return 1


def cmd_status(args):
    """Commande 'status': Affiche l'état actuel."""
    config_path = Path(args.config)

    try:
        config = OrchestratorConfig(config_path)

        print("\n" + "═" * 60)
        print("  STATUT DU PROJET")
        print("═" * 60)

        print(f"\n  📁 Projet : {config.project_name}")
        print(f"  📂 Repo   : {config.repo_path}")
        print(f"  🌿 Branche: {config.base_branch}")

        # Statistiques features
        total = len(config.features)
        print(f"\n  📊 Features: {total}")

        # Lister les worktrees actifs
        worktree_mgr = WorktreeManager(config.repo_path)
        active = worktree_mgr.list_active()

        if active:
            print(f"\n  🔧 Worktrees actifs: {len(active)}")
            for fid, info in active.items():
                print(f"    • {fid} → {info.branch_name}")
        else:
            print("\n  ℹ️  Aucun worktree actif")

        # Vérifier Claude CLI
        runner = ClaudeRunner()
        claude_available = runner.check_claude_available()
        version = runner.get_claude_version()

        print(f"\n  🤖 Claude CLI: {'✅ disponible' if claude_available else '❌ non disponible'}")
        if version:
            print(f"     Version: {version}")

        print("\n" + "═" * 60 + "\n")
        return 0

    except Exception as e:
        print(f"❌ Erreur: {e}", file=sys.stderr)
        return 1


def main():
    """Point d'entrée principal."""
    parser = argparse.ArgumentParser(
        description="RoRchestrator - Orchestration parallèle de Claude Code",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemples:
  orchestrate.py plan                    # Afficher le plan
  orchestrate.py run --yes               # Exécuter sans confirmation
  orchestrate.py cleanup --merged        # Nettoyer les worktrees mergés
  orchestrate.py status                  # Afficher l'état du projet
        """
    )

    subparsers = parser.add_subparsers(dest="command", help="Commande à exécuter")

    # Commande: plan
    parser_plan = subparsers.add_parser(
        "plan",
        help="Afficher le plan d'exécution sans exécuter"
    )
    parser_plan.add_argument(
        "--config",
        default="config/feature_list.json",
        help="Chemin vers feature_list.json (défaut: config/feature_list.json)"
    )

    # Commande: run
    parser_run = subparsers.add_parser(
        "run",
        help="Exécuter les features en parallèle"
    )
    parser_run.add_argument(
        "--config",
        default="config/feature_list.json",
        help="Chemin vers feature_list.json"
    )
    parser_run.add_argument(
        "--yes", "-y",
        action="store_true",
        help="Exécuter sans demander confirmation"
    )
    parser_run.add_argument(
        "--sequential",
        action="store_true",
        help="Exécuter en mode séquentiel (pour debugging)"
    )

    # Commande: cleanup
    parser_cleanup = subparsers.add_parser(
        "cleanup",
        help="Nettoyer les worktrees"
    )
    parser_cleanup.add_argument(
        "--merged",
        action="store_true",
        help="Nettoyer uniquement les worktrees mergés"
    )
    parser_cleanup.add_argument(
        "--all",
        action="store_true",
        help="Nettoyer TOUS les worktrees (attention!)"
    )
    parser_cleanup.add_argument(
        "--config",
        help="Chemin vers feature_list.json (optionnel)"
    )

    # Commande: status
    parser_status = subparsers.add_parser(
        "status",
        help="Afficher l'état du projet"
    )
    parser_status.add_argument(
        "--config",
        default="config/feature_list.json",
        help="Chemin vers feature_list.json"
    )

    args = parser.parse_args()

    # Vérifier qu'une commande a été fournie
    if not args.command:
        parser.print_help()
        return 1

    # Router vers la bonne commande
    commands = {
        "plan": cmd_plan,
        "run": cmd_run,
        "cleanup": cmd_cleanup,
        "status": cmd_status,
    }

    handler = commands.get(args.command)
    if handler:
        return handler(args)
    else:
        print(f"❌ Commande inconnue: {args.command}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
