#!/usr/bin/env python3
"""Démonstration intégrée : DAG + Worktree + Runner + Reporter.

Ce script illustre comment les composants travaillent ensemble
pour orchestrer l'exécution parallèle de features.

ATTENTION: Ce script utilise un binaire Claude simulé (echo)
pour la démonstration, car exécuter le vrai Claude serait trop long.
"""

import asyncio
import json
import tempfile
import shutil
import subprocess
from pathlib import Path

from core.dag import DAGResolver
from core.worktree import WorktreeManager
from core.runner import ClaudeRunner, ClaudeResult
from core.reporter import Reporter


def print_section(title: str):
    """Affiche un titre de section."""
    print("\n" + "═" * 60)
    print(f"  {title}")
    print("═" * 60)


def setup_demo_repo() -> Path:
    """Crée un repo Git temporaire avec CLAUDE.md."""
    temp_dir = Path(tempfile.mkdtemp(prefix="rorchestrator_integrated_"))
    repo_path = temp_dir / "demo_repo"
    repo_path.mkdir()

    # Initialiser Git
    subprocess.run(["git", "init"], cwd=repo_path, capture_output=True, check=True)
    subprocess.run(
        ["git", "config", "user.email", "demo@rorchestrator.local"],
        cwd=repo_path,
        capture_output=True,
        check=True
    )
    subprocess.run(
        ["git", "config", "user.name", "RoRchestrator Demo"],
        cwd=repo_path,
        capture_output=True,
        check=True
    )

    # Créer fichiers initiaux
    readme = repo_path / "README.md"
    readme.write_text("# Demo Project\n\nIntegrated RoRchestrator demo.")

    claude_md = repo_path / "CLAUDE.md"
    claude_md.write_text("""# Project Instructions

This is a demo project for RoRchestrator.

## Commands
- Build: `echo "Building..."`
- Test: `echo "Testing..."`
""")

    subprocess.run(["git", "add", "."], cwd=repo_path, capture_output=True, check=True)
    subprocess.run(
        ["git", "commit", "-m", "Initial commit"],
        cwd=repo_path,
        capture_output=True,
        check=True
    )

    # Créer branche master
    subprocess.run(["git", "checkout", "-b", "master"], cwd=repo_path, capture_output=True)

    return repo_path


def create_mock_claude_script(temp_dir: Path) -> Path:
    """Crée un script bash qui simule Claude CLI.

    Ce script retourne un JSON valide simulant une exécution réussie.
    """
    mock_script = temp_dir / "mock_claude.sh"

    script_content = """#!/bin/bash
# Mock Claude CLI pour démonstration

# Simuler un délai d'exécution
sleep 0.1

# Retourner un JSON valide
cat <<EOF
{
  "type": "result",
  "subtype": "success",
  "total_cost_usd": 0.001,
  "duration_ms": 100,
  "num_turns": 2,
  "result": "Feature implemented successfully (simulated)",
  "session_id": "mock-session-$(date +%s)"
}
EOF
"""

    mock_script.write_text(script_content)
    mock_script.chmod(0o755)

    return mock_script


async def main():
    """Fonction principale de démonstration."""

    print_section("RoRchestrator - Démonstration Intégrée")

    # 1. Setup
    print("\n🔧 Préparation de l'environnement...")
    repo_path = setup_demo_repo()
    mock_claude = create_mock_claude_script(repo_path.parent)
    print(f"  ✅ Repo temporaire: {repo_path}")
    print(f"  ✅ Mock Claude CLI: {mock_claude}")

    # 2. Définir les features (exemple GS1 simplifié)
    features = [
        {"id": "auth", "name": "Authentication", "depends_on": []},
        {"id": "api", "name": "API Endpoint", "depends_on": ["auth"]},
        {"id": "batch", "name": "Batch Import", "depends_on": ["auth"]},
        {"id": "ui", "name": "UI Dashboard", "depends_on": ["api", "batch"]},
    ]

    # 3. Initialiser les composants
    print_section("Initialisation des Composants")

    dag = DAGResolver(features)
    worktree_mgr = WorktreeManager(repo_path)
    runner = ClaudeRunner(
        max_parallel=2,
        claude_binary=str(mock_claude)
    )
    reporter = Reporter(verbose=True)

    print("  ✅ DAG Resolver")
    print("  ✅ Worktree Manager")
    print("  ✅ Claude Runner (max 2 parallèle)")
    print("  ✅ Reporter")

    # 4. Valider le DAG
    print_section("Validation du DAG")

    errors = dag.validate()
    if errors:
        print("  ❌ Erreurs détectées:")
        for error in errors:
            print(f"    • {error}")
        return

    print("  ✅ DAG valide!")

    # 5. Calculer les vagues
    waves = dag.get_execution_waves()
    features_dict = {f["id"]: f for f in features}
    reporter.display_dag(waves, features_dict)

    # 6. Exécution des vagues
    print_section("Exécution des Features")

    try:
        for wave_num, wave in enumerate(waves, 1):
            print(f"\n  ▶️  VAGUE {wave_num} - {len(wave)} feature(s)")

            # Créer les worktrees pour cette vague
            tasks = []
            for feature_id in wave:
                worktree_path = worktree_mgr.create(feature_id, base_branch="master")
                prompt = f"Implement feature: {features_dict[feature_id]['name']}"
                tasks.append((worktree_path, prompt, feature_id))

            # Exécuter en parallèle
            results = await runner.run_wave(
                tasks,
                on_progress=reporter.display_progress
            )

            # Enregistrer les résultats
            reporter.add_results(results)

    except Exception as e:
        print(f"\n  ❌ Erreur lors de l'exécution: {e}")
        return

    # 7. Générer et afficher le rapport
    print_section("Génération du Rapport")

    report = reporter.generate_report("DemoProject", waves)
    reporter.display_report(report)

    # 8. Sauvegarder les rapports
    print_section("Sauvegarde des Rapports")

    output_dir = repo_path.parent / "reports"
    output_dir.mkdir(exist_ok=True)

    report_path = output_dir / "execution_report.json"
    results_path = output_dir / "results.json"

    reporter.save_report(report, report_path)
    reporter.save_results(results_path)

    print(f"  ✅ Rapport sauvegardé: {report_path}")
    print(f"  ✅ Résultats sauvegardés: {results_path}")

    # 9. Afficher l'état des worktrees et branches
    print_section("État du Repo")

    active_worktrees = worktree_mgr.list_active()
    print(f"\n  📁 Worktrees actifs: {len(active_worktrees)}")
    for fid, info in active_worktrees.items():
        print(f"    • {fid} → {info.branch_name}")

    # Lister les branches créées
    result = subprocess.run(
        ["git", "branch", "-a"],
        cwd=repo_path,
        capture_output=True,
        text=True
    )
    branches = [
        line.strip().lstrip('*').strip()
        for line in result.stdout.split("\n")
        if "feature/" in line
    ]

    print(f"\n  🌿 Branches créées: {len(branches)}")
    for branch in branches:
        print(f"    • {branch}")

    # 10. Cleanup
    print_section("Nettoyage")

    print("\n  🧹 Suppression des worktrees...")
    worktree_mgr.cleanup_all()
    print("  ✅ Worktrees supprimés")

    print(f"\n  🗑️  Suppression du repo temporaire...")
    shutil.rmtree(repo_path.parent)
    print("  ✅ Cleanup complet")

    print("\n" + "═" * 60)
    print("  ✨ Démonstration terminée avec succès!")
    print("═" * 60 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
