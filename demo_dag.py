#!/usr/bin/env python3
"""Script de démonstration du DAG Resolver.

Ce script illustre l'utilisation du DAGResolver avec l'exemple
du projet GS1 Traceability Module.
"""

import json
from pathlib import Path
from core.dag import DAGResolver


def print_section(title: str):
    """Affiche un titre de section."""
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60)


def load_features_from_config():
    """Charge les features depuis le fichier exemple."""
    config_path = Path(__file__).parent / "config" / "feature_list.example.json"
    with open(config_path) as f:
        config = json.load(f)
    return config["features"]


def main():
    """Fonction principale de démonstration."""

    print_section("RoRchestrator - Démonstration DAG Resolver")

    # Charger les features
    features = load_features_from_config()
    print(f"\n📋 Features chargées: {len(features)}")
    for f in features:
        deps = f.get("depends_on", [])
        deps_str = f" (dépend de: {', '.join(deps)})" if deps else " (aucune dépendance)"
        print(f"  • {f['id']}: {f['name']}{deps_str}")

    # Créer le resolver
    print("\n🔧 Initialisation du DAG Resolver...")
    dag = DAGResolver(features)

    # Valider le graphe
    print_section("Validation du Graphe")
    errors = dag.validate()

    if errors:
        print("\n❌ Erreurs détectées:")
        for error in errors:
            print(f"  • {error}")
        return

    print("\n✅ Graphe valide! Aucun cycle ni référence invalide détectée.")

    # Calculer les vagues d'exécution
    print_section("Vagues d'Exécution")
    waves = dag.get_execution_waves()

    print(f"\n📊 {len(waves)} vagues d'exécution calculées:")

    for i, wave in enumerate(waves, 1):
        parallel = " [PARALLÈLE]" if len(wave) > 1 else ""
        print(f"\n  VAGUE {i}{parallel}")
        print("  " + "─" * 40)

        for fid in wave:
            feature = dag.get_feature(fid)
            deps = dag.get_dependencies(fid)
            deps_str = f"← dépend de {sorted(deps)}" if deps else "← aucune dépendance"

            print(f"  │ {fid}")
            print(f"  │   {feature['name']}")
            print(f"  │   {deps_str}")

    # Analyse des dépendances
    print_section("Analyse des Dépendances")

    # Feature avec le plus de dépendances
    max_deps_feature = max(
        features,
        key=lambda f: len(dag.get_all_dependencies(f["id"]))
    )
    all_deps = dag.get_all_dependencies(max_deps_feature["id"])

    print(f"\n📌 Feature avec le plus de dépendances totales:")
    print(f"  • {max_deps_feature['id']}: {max_deps_feature['name']}")
    print(f"  • Dépendances transitives: {sorted(all_deps)}")

    # Feature la plus critique (le plus de dependents)
    max_dependents_feature = max(
        features,
        key=lambda f: len(dag.get_dependents(f["id"]))
    )
    dependents = dag.get_dependents(max_dependents_feature["id"])

    print(f"\n🎯 Feature la plus critique (le plus de features en dépendent):")
    print(f"  • {max_dependents_feature['id']}: {max_dependents_feature['name']}")
    print(f"  • Bloque ces features: {sorted(dependents)}")

    # Statistiques
    print_section("Statistiques")

    total_tokens = sum(f.get("estimated_tokens", 0) for f in features)
    parallel_features = sum(len(wave) for wave in waves if len(wave) > 1)
    sequential_features = sum(len(wave) for wave in waves if len(wave) == 1)

    print(f"""
  Total features          : {len(features)}
  Features parallélisables: {parallel_features}
  Features séquentielles  : {sequential_features}
  Vagues d'exécution      : {len(waves)}
  Tokens estimés (total)  : {total_tokens:,}
    """)

    # Simulation du gain de temps
    if len(waves) < len(features):
        sequential_time = len(features)  # En supposant 1 unité de temps par feature
        parallel_time = len(waves)
        speedup = sequential_time / parallel_time

        print(f"  ⚡ Gain théorique de vitesse:")
        print(f"     Temps séquentiel : {sequential_time} unités")
        print(f"     Temps parallèle  : {parallel_time} unités")
        print(f"     Speedup          : {speedup:.1f}x")

    print("\n" + "=" * 60)
    print("✨ Démonstration terminée!")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    main()
