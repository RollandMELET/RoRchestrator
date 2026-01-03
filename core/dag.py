"""DAG Resolver for feature dependencies using Python's graphlib."""

from graphlib import TopologicalSorter, CycleError
from typing import List, Dict, Set, Any


class DAGResolver:
    """Résout les dépendances et calcule les vagues d'exécution parallèles.

    Cette classe utilise le TopologicalSorter de Python pour:
    1. Valider qu'il n'y a pas de cycles dans les dépendances
    2. Vérifier que toutes les dépendances référencées existent
    3. Calculer les "vagues" d'exécution où chaque vague contient
       les features qui peuvent s'exécuter en parallèle

    Attributes:
        features (Dict[str, Dict]): Dictionnaire des features indexées par ID
        graph (Dict[str, Set[str]]): Graphe de dépendances (feature_id -> set de dépendances)

    Example:
        >>> features = [
        ...     {"id": "auth", "depends_on": []},
        ...     {"id": "api", "depends_on": ["auth"]},
        ...     {"id": "batch", "depends_on": ["auth"]},
        ...     {"id": "dashboard", "depends_on": ["api", "batch"]}
        ... ]
        >>> dag = DAGResolver(features)
        >>> errors = dag.validate()
        >>> if not errors:
        ...     waves = dag.get_execution_waves()
        ...     # waves = [["auth"], ["api", "batch"], ["dashboard"]]
    """

    def __init__(self, features: List[Dict[str, Any]]):
        """Initialise le resolver avec une liste de features.

        Args:
            features: Liste de dictionnaires représentant les features.
                     Chaque feature doit avoir au minimum:
                     - "id" (str): Identifiant unique
                     - "depends_on" (List[str], optionnel): Liste des IDs de dépendances
        """
        self.features = {f["id"]: f for f in features}
        self.graph = self._build_graph()

    def _build_graph(self) -> Dict[str, Set[str]]:
        """Construit le graphe de dépendances.

        Returns:
            Dictionnaire où chaque clé est un feature_id et la valeur
            est un ensemble des IDs de features dont il dépend.
        """
        return {
            f["id"]: set(f.get("depends_on", []))
            for f in self.features.values()
        }

    def validate(self) -> List[str]:
        """Valide le graphe de dépendances.

        Vérifie:
        1. Que toutes les dépendances référencées existent
        2. Qu'il n'y a pas de cycles dans le graphe

        Returns:
            Liste des erreurs trouvées. Liste vide si tout est valide.
        """
        errors = []

        # Vérifier les références invalides
        all_ids = set(self.features.keys())
        for fid, deps in self.graph.items():
            invalid = deps - all_ids
            if invalid:
                invalid_list = ", ".join(sorted(invalid))
                errors.append(
                    f"Feature '{fid}' dépend de features inexistantes: {invalid_list}"
                )

        # Vérifier les cycles (seulement si pas de références invalides)
        if not errors:
            try:
                sorter = TopologicalSorter(self.graph)
                sorter.prepare()
            except CycleError as e:
                # CycleError contient le cycle dans args[1]
                cycle_info = e.args[1] if len(e.args) > 1 else "cycle détecté"
                errors.append(f"Cycle de dépendances détecté: {cycle_info}")

        return errors

    def get_execution_waves(self) -> List[List[str]]:
        """Calcule les vagues d'exécution parallèles.

        Utilise TopologicalSorter.get_ready() pour identifier à chaque
        étape quelles features peuvent s'exécuter en parallèle (celles
        dont toutes les dépendances sont satisfaites).

        Returns:
            Liste de vagues, où chaque vague est une liste de feature IDs
            qui peuvent s'exécuter en parallèle.

        Raises:
            CycleError: Si le graphe contient un cycle

        Example:
            Pour le graphe: A → [], B → [A], C → [A], D → [B, C]
            Retourne: [["A"], ["B", "C"], ["D"]]
        """
        sorter = TopologicalSorter(self.graph)
        sorter.prepare()

        waves = []
        while sorter.is_active():
            # get_ready() retourne les nodes dont toutes les dépendances
            # ont été marquées comme "done"
            ready = list(sorter.get_ready())
            if ready:
                waves.append(sorted(ready))  # Tri pour cohérence
                for node in ready:
                    sorter.done(node)

        return waves

    def get_feature(self, feature_id: str) -> Dict[str, Any]:
        """Récupère une feature par son ID.

        Args:
            feature_id: L'identifiant de la feature

        Returns:
            Le dictionnaire de la feature, ou None si non trouvée
        """
        return self.features.get(feature_id)

    def get_dependencies(self, feature_id: str) -> Set[str]:
        """Récupère les dépendances directes d'une feature.

        Args:
            feature_id: L'identifiant de la feature

        Returns:
            Ensemble des IDs des features dont dépend cette feature
        """
        return self.graph.get(feature_id, set())

    def get_dependents(self, feature_id: str) -> Set[str]:
        """Récupère les features qui dépendent de cette feature.

        Args:
            feature_id: L'identifiant de la feature

        Returns:
            Ensemble des IDs des features qui dépendent de cette feature
        """
        dependents = set()
        for fid, deps in self.graph.items():
            if feature_id in deps:
                dependents.add(fid)
        return dependents

    def get_all_dependencies(self, feature_id: str) -> Set[str]:
        """Récupère toutes les dépendances (directes et transitives) d'une feature.

        Args:
            feature_id: L'identifiant de la feature

        Returns:
            Ensemble de tous les IDs des features dont dépend cette feature,
            directement ou indirectement
        """
        all_deps = set()
        to_process = list(self.get_dependencies(feature_id))

        while to_process:
            dep = to_process.pop()
            if dep not in all_deps:
                all_deps.add(dep)
                to_process.extend(self.get_dependencies(dep))

        return all_deps
