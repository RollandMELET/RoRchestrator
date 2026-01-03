"""Tests unitaires pour le DAG Resolver."""

import unittest
from core.dag import DAGResolver


class TestDAGResolver(unittest.TestCase):
    """Tests pour la classe DAGResolver."""

    def test_simple_linear_graph(self):
        """Test un graphe linéaire simple: A → B → C"""
        features = [
            {"id": "A", "depends_on": []},
            {"id": "B", "depends_on": ["A"]},
            {"id": "C", "depends_on": ["B"]},
        ]
        dag = DAGResolver(features)

        errors = dag.validate()
        self.assertEqual(errors, [], "Le graphe linéaire devrait être valide")

        waves = dag.get_execution_waves()
        self.assertEqual(waves, [["A"], ["B"], ["C"]])

    def test_parallel_execution(self):
        """Test un graphe avec parallélisme: A → [B, C] → D"""
        features = [
            {"id": "A", "depends_on": []},
            {"id": "B", "depends_on": ["A"]},
            {"id": "C", "depends_on": ["A"]},
            {"id": "D", "depends_on": ["B", "C"]},
        ]
        dag = DAGResolver(features)

        errors = dag.validate()
        self.assertEqual(errors, [])

        waves = dag.get_execution_waves()
        self.assertEqual(len(waves), 3)
        self.assertEqual(waves[0], ["A"])
        self.assertEqual(set(waves[1]), {"B", "C"})  # Ordre peut varier
        self.assertEqual(waves[2], ["D"])

    def test_complex_dag(self):
        """Test le graphe exemple de la doc GS1."""
        features = [
            {"id": "auth-gtin", "depends_on": []},
            {"id": "api-lookup", "depends_on": ["auth-gtin"]},
            {"id": "batch-import", "depends_on": ["auth-gtin"]},
            {"id": "dashboard", "depends_on": ["api-lookup", "batch-import"]},
        ]
        dag = DAGResolver(features)

        errors = dag.validate()
        self.assertEqual(errors, [])

        waves = dag.get_execution_waves()
        self.assertEqual(len(waves), 3)
        self.assertEqual(waves[0], ["auth-gtin"])
        self.assertEqual(set(waves[1]), {"api-lookup", "batch-import"})
        self.assertEqual(waves[2], ["dashboard"])

    def test_invalid_dependency_reference(self):
        """Test la détection de références invalides."""
        features = [
            {"id": "A", "depends_on": []},
            {"id": "B", "depends_on": ["A", "nonexistent"]},
        ]
        dag = DAGResolver(features)

        errors = dag.validate()
        self.assertEqual(len(errors), 1)
        self.assertIn("nonexistent", errors[0])
        self.assertIn("inexistantes", errors[0])

    def test_multiple_invalid_dependencies(self):
        """Test plusieurs références invalides."""
        features = [
            {"id": "A", "depends_on": ["X", "Y"]},
            {"id": "B", "depends_on": ["Z"]},
        ]
        dag = DAGResolver(features)

        errors = dag.validate()
        self.assertEqual(len(errors), 2)

    def test_cycle_detection_simple(self):
        """Test la détection d'un cycle simple: A → B → A"""
        features = [
            {"id": "A", "depends_on": ["B"]},
            {"id": "B", "depends_on": ["A"]},
        ]
        dag = DAGResolver(features)

        errors = dag.validate()
        self.assertEqual(len(errors), 1)
        self.assertIn("Cycle", errors[0])

    def test_cycle_detection_complex(self):
        """Test la détection d'un cycle complexe: A → B → C → A"""
        features = [
            {"id": "A", "depends_on": ["C"]},
            {"id": "B", "depends_on": ["A"]},
            {"id": "C", "depends_on": ["B"]},
        ]
        dag = DAGResolver(features)

        errors = dag.validate()
        self.assertEqual(len(errors), 1)
        self.assertIn("Cycle", errors[0])

    def test_no_dependencies(self):
        """Test des features sans dépendances (tout en parallèle)."""
        features = [
            {"id": "A", "depends_on": []},
            {"id": "B", "depends_on": []},
            {"id": "C", "depends_on": []},
        ]
        dag = DAGResolver(features)

        errors = dag.validate()
        self.assertEqual(errors, [])

        waves = dag.get_execution_waves()
        self.assertEqual(len(waves), 1)
        self.assertEqual(set(waves[0]), {"A", "B", "C"})

    def test_get_feature(self):
        """Test la récupération d'une feature par ID."""
        features = [
            {"id": "A", "name": "Feature A", "depends_on": []},
            {"id": "B", "name": "Feature B", "depends_on": ["A"]},
        ]
        dag = DAGResolver(features)

        feature_a = dag.get_feature("A")
        self.assertIsNotNone(feature_a)
        self.assertEqual(feature_a["name"], "Feature A")

        feature_none = dag.get_feature("nonexistent")
        self.assertIsNone(feature_none)

    def test_get_dependencies(self):
        """Test la récupération des dépendances directes."""
        features = [
            {"id": "A", "depends_on": []},
            {"id": "B", "depends_on": ["A"]},
            {"id": "C", "depends_on": ["A", "B"]},
        ]
        dag = DAGResolver(features)

        deps_a = dag.get_dependencies("A")
        self.assertEqual(deps_a, set())

        deps_b = dag.get_dependencies("B")
        self.assertEqual(deps_b, {"A"})

        deps_c = dag.get_dependencies("C")
        self.assertEqual(deps_c, {"A", "B"})

    def test_get_dependents(self):
        """Test la récupération des features dépendantes."""
        features = [
            {"id": "A", "depends_on": []},
            {"id": "B", "depends_on": ["A"]},
            {"id": "C", "depends_on": ["A"]},
            {"id": "D", "depends_on": ["B"]},
        ]
        dag = DAGResolver(features)

        # A est requis par B et C
        dependents_a = dag.get_dependents("A")
        self.assertEqual(dependents_a, {"B", "C"})

        # B est requis par D
        dependents_b = dag.get_dependents("B")
        self.assertEqual(dependents_b, {"D"})

        # D n'est requis par personne
        dependents_d = dag.get_dependents("D")
        self.assertEqual(dependents_d, set())

    def test_get_all_dependencies_transitive(self):
        """Test la récupération des dépendances transitives."""
        features = [
            {"id": "A", "depends_on": []},
            {"id": "B", "depends_on": ["A"]},
            {"id": "C", "depends_on": ["B"]},
            {"id": "D", "depends_on": ["C"]},
        ]
        dag = DAGResolver(features)

        # D dépend de C, B, et A (transitif)
        all_deps_d = dag.get_all_dependencies("D")
        self.assertEqual(all_deps_d, {"A", "B", "C"})

        # C dépend de B et A (transitif)
        all_deps_c = dag.get_all_dependencies("C")
        self.assertEqual(all_deps_c, {"A", "B"})

        # A ne dépend de personne
        all_deps_a = dag.get_all_dependencies("A")
        self.assertEqual(all_deps_a, set())

    def test_get_all_dependencies_diamond(self):
        """Test les dépendances transitives avec un graphe en diamant."""
        features = [
            {"id": "A", "depends_on": []},
            {"id": "B", "depends_on": ["A"]},
            {"id": "C", "depends_on": ["A"]},
            {"id": "D", "depends_on": ["B", "C"]},
        ]
        dag = DAGResolver(features)

        # D dépend de A via deux chemins, mais A ne doit apparaître qu'une fois
        all_deps_d = dag.get_all_dependencies("D")
        self.assertEqual(all_deps_d, {"A", "B", "C"})

    def test_empty_features_list(self):
        """Test avec une liste vide de features."""
        dag = DAGResolver([])

        errors = dag.validate()
        self.assertEqual(errors, [])

        waves = dag.get_execution_waves()
        self.assertEqual(waves, [])

    def test_single_feature(self):
        """Test avec une seule feature sans dépendance."""
        features = [{"id": "A", "depends_on": []}]
        dag = DAGResolver(features)

        errors = dag.validate()
        self.assertEqual(errors, [])

        waves = dag.get_execution_waves()
        self.assertEqual(waves, [["A"]])

    def test_feature_depends_on_itself(self):
        """Test la détection d'une feature qui dépend d'elle-même."""
        features = [{"id": "A", "depends_on": ["A"]}]
        dag = DAGResolver(features)

        errors = dag.validate()
        self.assertEqual(len(errors), 1)
        self.assertIn("Cycle", errors[0])


if __name__ == "__main__":
    unittest.main()
