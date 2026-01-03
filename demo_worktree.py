#!/usr/bin/env python3
"""Script de démonstration du Worktree Manager.

Ce script crée un repo Git temporaire pour démontrer le WorktreeManager.
Les worktrees sont créés puis nettoyés automatiquement.
"""

import tempfile
import shutil
import subprocess
from pathlib import Path
from core.worktree import WorktreeManager


def print_section(title: str):
    """Affiche un titre de section."""
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60)


def setup_demo_repo() -> Path:
    """Crée un repo Git temporaire pour la démo."""
    temp_dir = Path(tempfile.mkdtemp(prefix="rorchestrator_demo_"))
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

    # Créer un commit initial
    readme = repo_path / "README.md"
    readme.write_text("# Demo Repository\n\nCréé pour démonstration RoRchestrator.")

    claude_md = repo_path / "CLAUDE.md"
    claude_md.write_text("# Project Instructions\n\nDemo project for worktree testing.")

    subprocess.run(["git", "add", "."], cwd=repo_path, capture_output=True, check=True)
    subprocess.run(
        ["git", "commit", "-m", "Initial commit"],
        cwd=repo_path,
        capture_output=True,
        check=True
    )

    # Créer la branche master
    subprocess.run(
        ["git", "checkout", "-b", "master"],
        cwd=repo_path,
        capture_output=True
    )

    return repo_path


def main():
    """Fonction principale de démonstration."""

    print_section("RoRchestrator - Démonstration Worktree Manager")

    # Créer un repo de démo
    print("\n🔧 Création d'un repo Git temporaire pour la démo...")
    repo_path = setup_demo_repo()
    print(f"✅ Repo créé: {repo_path}")

    # Créer le manager
    print("\n🔧 Initialisation du Worktree Manager...")
    manager = WorktreeManager(repo_path)
    print(f"✅ Worktrees seront créés dans: {manager.worktrees_base}")

    # Lister les worktrees existants avant
    print_section("Worktrees Existants (avant)")
    all_wts_before = manager.list_all_worktrees()
    if all_wts_before:
        for wt in all_wts_before:
            branch = wt.get("branch", "N/A")
            path = wt.get("path", "N/A")
            print(f"  • {branch}")
            print(f"    {path}")
    else:
        print("  (aucun worktree trouvé)")

    # Créer des worktrees de démonstration
    print_section("Création de Worktrees")

    features = ["demo-auth", "demo-api", "demo-ui"]

    for feature_id in features:
        print(f"\n📍 Création de '{feature_id}'...")
        try:
            worktree_path = manager.create(feature_id, base_branch="master")
            print(f"  ✅ Créé: {worktree_path}")
            print(f"  📝 Branche: feature/{feature_id}")

            # Vérifier que CLAUDE.md a été copié
            claude_md = worktree_path / "CLAUDE.md"
            if claude_md.exists():
                print(f"  📄 CLAUDE.md copié avec contexte feature")
        except Exception as e:
            print(f"  ❌ Erreur: {e}")

    # Lister les worktrees actifs
    print_section("Worktrees Actifs Gérés")
    active = manager.list_active()
    print(f"\n🎯 {len(active)} worktrees actifs:")
    for feature_id, info in active.items():
        print(f"\n  • {feature_id}")
        print(f"    Path   : {info.path}")
        print(f"    Branch : {info.branch_name}")
        print(f"    Exists : {info.path.exists()}")

    # Lister tous les worktrees Git
    print_section("Tous les Worktrees Git")
    all_wts = manager.list_all_worktrees()
    print(f"\n📊 {len(all_wts)} worktrees Git au total:")
    for wt in all_wts:
        branch = wt.get("branch", "N/A")
        path = wt.get("path", "N/A")
        is_demo = "demo-" in path
        marker = "🔹" if is_demo else "  "
        print(f"{marker} {branch}")
        if is_demo:
            print(f"   {path}")

    # Statistiques
    print_section("Statistiques")

    demo_worktrees = [wt for wt in all_wts if "demo-" in wt.get("path", "")]
    total_size = sum(
        sum(f.stat().st_size for f in Path(wt["path"]).rglob("*") if f.is_file())
        for wt in demo_worktrees
    )

    print(f"""
  Worktrees de démo créés : {len(demo_worktrees)}
  Taille totale sur disque: {total_size / 1024:.1f} KB
    """)

    # Nettoyage
    print_section("Nettoyage")
    print("\n🧹 Suppression des worktrees de démonstration...")

    for feature_id in features:
        try:
            result = manager.remove(feature_id, force=True)
            status = "✅" if result else "⏭️"
            print(f"  {status} {feature_id}")
        except Exception as e:
            print(f"  ❌ Erreur lors de la suppression de {feature_id}: {e}")

    # Vérifier que tout est nettoyé
    remaining = manager.list_active()
    if not remaining:
        print("\n✨ Tous les worktrees de démonstration ont été nettoyés!")
    else:
        print(f"\n⚠️  {len(remaining)} worktrees restants: {list(remaining.keys())}")

    # Cleanup final du repo temporaire
    print_section("Cleanup Final")
    print(f"\n🗑️  Suppression du repo temporaire: {repo_path.parent}")

    try:
        shutil.rmtree(repo_path.parent)
        print("✅ Repo temporaire supprimé")
    except Exception as e:
        print(f"⚠️  Erreur lors du cleanup: {e}")
        print(f"   Vous pouvez supprimer manuellement: {repo_path.parent}")

    print("\n" + "=" * 60)
    print("✅ Démonstration terminée!")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    main()
