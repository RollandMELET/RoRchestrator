"""Reporter pour affichage de progression et génération de rapports."""

import json
from dataclasses import dataclass, asdict
from typing import List, Dict, Any
from datetime import datetime
from pathlib import Path

from core.runner import ClaudeResult


@dataclass
class ExecutionReport:
    """Rapport d'exécution complet.

    Attributes:
        project_name: Nom du projet
        started_at: Date/heure de début
        finished_at: Date/heure de fin
        total_features: Nombre total de features
        successful: Nombre de features réussies
        failed: Nombre de features échouées
        total_cost_usd: Coût total en USD
        total_duration_ms: Durée totale en millisecondes
        waves: Structure des vagues d'exécution
        branches_created: Liste des branches créées avec succès
        errors: Liste des erreurs rencontrées
    """
    project_name: str
    started_at: datetime
    finished_at: datetime
    total_features: int
    successful: int
    failed: int
    total_cost_usd: float
    total_duration_ms: int
    waves: List[Dict[str, Any]]
    branches_created: List[str]
    errors: List[Dict[str, str]]

    def to_dict(self) -> Dict[str, Any]:
        """Convertit en dictionnaire pour sérialisation JSON."""
        data = asdict(self)
        data["started_at"] = self.started_at.isoformat()
        data["finished_at"] = self.finished_at.isoformat()
        return data


class Reporter:
    """Génère les rapports et affiche la progression.

    Attributes:
        verbose: Si True, affiche plus de détails
        results: Liste des résultats accumulés
    """

    def __init__(self, verbose: bool = True):
        """Initialise le reporter.

        Args:
            verbose: Active l'affichage détaillé
        """
        self.verbose = verbose
        self.results: List[ClaudeResult] = []

    def display_dag(self, waves: List[List[str]], features: Dict[str, Dict]):
        """Affiche le DAG avant exécution.

        Args:
            waves: Vagues d'exécution calculées
            features: Dictionnaire des features (id -> feature dict)
        """
        print("\n" + "═" * 60)
        print("  PLAN D'EXÉCUTION")
        print("═" * 60)

        total_features = sum(len(wave) for wave in waves)
        print(f"\n  📊 {total_features} features en {len(waves)} vagues")

        for i, wave in enumerate(waves, 1):
            parallel_marker = " [PARALLÈLE]" if len(wave) > 1 else ""
            print(f"\n  VAGUE {i}{parallel_marker}")
            print("  " + "─" * 40)

            for fid in wave:
                feature = features.get(fid, {})
                deps = feature.get("depends_on", [])
                name = feature.get("name", fid)

                deps_str = f"← attend {deps}" if deps else "← aucune dépendance"

                print(f"  │ {fid}: {name}")
                if self.verbose:
                    print(f"  │   {deps_str}")
                    estimated = feature.get("estimated_tokens", 0)
                    if estimated:
                        print(f"  │   ~{estimated:,} tokens")

        print("\n" + "═" * 60)

    def display_progress(self, feature_id: str, status: str):
        """Affiche la progression en temps réel.

        Args:
            feature_id: ID de la feature
            status: Statut ("started", "completed", "failed")
        """
        icons = {
            "started": "🚀",
            "completed": "✅",
            "failed": "❌"
        }
        icon = icons.get(status, "⏳")
        timestamp = datetime.now().strftime("%H:%M:%S")

        if self.verbose or status != "started":
            print(f"  [{timestamp}] {icon} {feature_id}: {status}")

    def add_result(self, result: ClaudeResult):
        """Ajoute un résultat à la liste.

        Args:
            result: Résultat d'exécution Claude
        """
        self.results.append(result)

    def add_results(self, results: List[ClaudeResult]):
        """Ajoute plusieurs résultats.

        Args:
            results: Liste de résultats
        """
        self.results.extend(results)

    def generate_report(
        self,
        project_name: str,
        waves: List[List[str]]
    ) -> ExecutionReport:
        """Génère le rapport final d'exécution.

        Args:
            project_name: Nom du projet
            waves: Structure des vagues utilisée

        Returns:
            ExecutionReport complet
        """
        if not self.results:
            raise ValueError("Aucun résultat à reporter")

        successful = sum(1 for r in self.results if r.success)
        failed = len(self.results) - successful
        total_cost = sum(r.cost_usd for r in self.results)
        total_duration = sum(r.duration_ms for r in self.results)

        branches = [
            f"feature/{r.feature_id}"
            for r in self.results
            if r.success
        ]

        errors = [
            {"feature_id": r.feature_id, "error": r.error or "Unknown error"}
            for r in self.results
            if not r.success
        ]

        # Timestamps
        started_at = min(r.started_at for r in self.results if r.started_at)
        finished_at = max(r.finished_at for r in self.results if r.finished_at)

        return ExecutionReport(
            project_name=project_name,
            started_at=started_at,
            finished_at=finished_at,
            total_features=len(self.results),
            successful=successful,
            failed=failed,
            total_cost_usd=total_cost,
            total_duration_ms=total_duration,
            waves=[{"wave": i, "features": w} for i, w in enumerate(waves, 1)],
            branches_created=branches,
            errors=errors
        )

    def display_report(self, report: ExecutionReport):
        """Affiche le rapport final dans la console.

        Args:
            report: Rapport d'exécution
        """
        print("\n" + "═" * 60)
        print("  RAPPORT D'EXÉCUTION")
        print("═" * 60)

        duration_min = report.total_duration_ms / 60000
        wall_time = (report.finished_at - report.started_at).total_seconds() / 60

        print(f"""
  Projet         : {report.project_name}
  Durée totale   : {duration_min:.1f} minutes (temps CPU)
  Durée réelle   : {wall_time:.1f} minutes (wall time)
  Coût total     : ${report.total_cost_usd:.2f}

  Features       : {report.total_features}
    ✅ Succès     : {report.successful}
    ❌ Échecs     : {report.failed}

  Vagues         : {len(report.waves)}""")

        if report.branches_created:
            print("\n  Branches créées :")
            for branch in report.branches_created:
                print(f"    • {branch}")

        if report.errors:
            print("\n  ❌ Erreurs :")
            for err in report.errors:
                error_msg = err["error"]
                # Tronquer si trop long
                if len(error_msg) > 60:
                    error_msg = error_msg[:57] + "..."
                print(f"    • {err['feature_id']}: {error_msg}")

        # Speedup calculation
        if len(report.waves) > 1:
            sequential_time = report.total_features
            parallel_time = len(report.waves)
            speedup = sequential_time / parallel_time
            print(f"\n  ⚡ Speedup théorique: {speedup:.1f}x")

        print("\n" + "═" * 60)

    def save_report(self, report: ExecutionReport, path: Path):
        """Sauvegarde le rapport au format JSON.

        Args:
            report: Rapport d'exécution
            path: Chemin du fichier de sortie

        Raises:
            IOError: Si l'écriture échoue
        """
        data = report.to_dict()

        with open(path, "w") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def save_results(self, path: Path):
        """Sauvegarde tous les résultats bruts au format JSON.

        Args:
            path: Chemin du fichier de sortie
        """
        data = [r.to_dict() for r in self.results]

        with open(path, "w") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def display_summary(self):
        """Affiche un résumé rapide des résultats actuels."""
        if not self.results:
            print("  📭 Aucun résultat pour le moment")
            return

        successful = sum(1 for r in self.results if r.success)
        failed = len(self.results) - successful
        total_cost = sum(r.cost_usd for r in self.results)

        print(f"\n  📊 Résumé: {successful}✅ / {failed}❌ (${total_cost:.2f})")
