# RoRchestrator

> Orchestrateur Python léger pour parallélisation de Claude Code via Git Worktrees

**Version:** 1.0.0-mvp
**Statut:** MVP Complet - Toutes phases terminées ✅ (57 tests passent)

## Vue d'ensemble

RoRchestrator automatise l'exécution parallèle de Claude Code sur plusieurs features simultanément, en utilisant :
- **Git Worktrees** pour l'isolation de chaque feature
- **DAG (Directed Acyclic Graph)** pour gérer les dépendances
- **asyncio** pour l'exécution parallèle
- **TopologicalSorter** (Python stdlib) pour calculer l'ordre d'exécution

## Architecture

```
orchestrator/
├── orchestrate.py               # 🔜 CLI principale (Phase 4)
├── config/
│   └── feature_list.example.json  # ✅ Configuration exemple GS1
├── core/
│   ├── dag.py                   # ✅ DAG Resolver (Phase 1)
│   ├── worktree.py              # ✅ Git worktree manager (Phase 2)
│   ├── runner.py                # ✅ Claude CLI async runner (Phase 3)
│   └── reporter.py              # ✅ Logs et métriques (Phase 3)
├── assistants/
│   └── dependencies.py          # 🔜 Questionnaire interactif (Phase 4)
├── prompts/
│   └── *.md                     # Prompts par feature
├── templates/
│   └── *.j2                     # Templates de configuration
├── tests/
│   ├── test_dag.py              # ✅ 16 tests
│   ├── test_worktree.py         # ✅ 17 tests
│   ├── test_runner.py           # ✅ 14 tests
│   └── test_reporter.py         # ✅ 10 tests
└── demo_*.py                    # Scripts de démonstration
```

## Phase 1 - DAG Resolver ✅

### Fonctionnalités implémentées

Le module `core/dag.py` fournit :

- **Validation du graphe de dépendances**
  - Détection des références invalides
  - Détection des cycles

- **Calcul des vagues d'exécution**
  - Identifie les features parallélisables
  - Respecte l'ordre des dépendances

- **Méthodes utilitaires**
  - `get_feature(id)`: Récupère une feature
  - `get_dependencies(id)`: Dépendances directes
  - `get_dependents(id)`: Features qui dépendent de celle-ci
  - `get_all_dependencies(id)`: Toutes les dépendances (transitives)

### Exemple d'utilisation

```python
from core.dag import DAGResolver

features = [
    {"id": "auth-gtin", "depends_on": []},
    {"id": "api-lookup", "depends_on": ["auth-gtin"]},
    {"id": "batch-import", "depends_on": ["auth-gtin"]},
    {"id": "dashboard", "depends_on": ["api-lookup", "batch-import"]}
]

dag = DAGResolver(features)

# Valider le graphe
errors = dag.validate()
if errors:
    for error in errors:
        print(f"❌ {error}")
    exit(1)

# Calculer les vagues d'exécution
waves = dag.get_execution_waves()
# Résultat: [["auth-gtin"], ["api-lookup", "batch-import"], ["dashboard"]]

print(f"✅ Graphe valide avec {len(waves)} vagues d'exécution")
for i, wave in enumerate(waves, 1):
    parallel = "PARALLÈLE" if len(wave) > 1 else ""
    print(f"  Vague {i} {parallel}: {wave}")
```

### Tests

16 tests unitaires couvrent :
- Graphes linéaires et parallèles
- Détection de cycles (simples et complexes)
- Détection de références invalides
- Dépendances transitives (graphe en diamant)
- Cas limites (liste vide, feature unique, self-dependency)

**Exécuter les tests :**
```bash
cd orchestrator
python3 -m unittest tests/test_dag.py -v
```

## Phase 2 - Worktree Manager ✅

### Fonctionnalités implémentées

Le module `core/worktree.py` fournit :

- **Gestion des Git worktrees**
  - Création avec nouvelle branche automatique
  - Suppression (normale et forcée)
  - Validation du repo Git

- **Copie automatique du CLAUDE.md**
  - Ajout du contexte feature dans chaque worktree
  - Préservation des instructions du projet

- **Cleanup intelligent**
  - `cleanup_all()`: Supprime tous les worktrees actifs
  - `cleanup_merged()`: Supprime uniquement les worktrees mergés
  - `cleanup()`: Prune les références Git orphelines

- **Méthodes utilitaires**
  - `exists(id)`: Vérifie l'existence d'un worktree
  - `get_path(id)`: Récupère le chemin
  - `list_active()`: Liste les worktrees gérés
  - `list_all_worktrees()`: Liste tous les worktrees Git

### Exemple d'utilisation

```python
from pathlib import Path
from core.worktree import WorktreeManager

# Initialiser
manager = WorktreeManager(Path("/path/to/repo"))

# Créer des worktrees
auth_path = manager.create("auth-gtin", base_branch="main")
api_path = manager.create("api-lookup", base_branch="main")

# Lister les actifs
active = manager.list_active()
print(f"{len(active)} worktrees actifs")

# Cleanup après merge
cleaned = manager.cleanup_merged("main")
print(f"Nettoyé: {cleaned}")
```

### Tests

17 tests unitaires couvrent :
- Création et suppression de worktrees
- Gestion des erreurs (repo invalide, branche inexistante)
- Copie du CLAUDE.md
- Cleanup (all, merged)
- Gestion des modifications non commitées
- Force recreation

**Exécuter les tests :**
```bash
python3 -m unittest tests/test_worktree.py -v
```

**Exécuter la démo :**
```bash
python3 demo_worktree.py
```

## Phase 3 - Claude Runner & Reporter ✅

### Fonctionnalités implémentées

**Module `core/runner.py`** :

- **Classe `ClaudeResult`**
  - Structure de données pour les résultats d'exécution
  - Méthode `to_dict()` pour sérialisation JSON

- **Classe `ClaudeRunner`**
  - Exécution asynchrone de Claude Code en mode headless
  - `run_single()`: Lance une feature avec timeout et error handling
  - `run_wave()`: Exécution parallèle avec Semaphore
  - `run_sequential()`: Exécution séquentielle (pour debugging)
  - `check_claude_available()`: Vérifie la disponibilité du binaire
  - Parsing du JSON output de Claude

**Module `core/reporter.py`** :

- **Classe `ExecutionReport`**
  - Rapport complet d'exécution
  - Métriques: coûts, durées, succès/échecs

- **Classe `Reporter`**
  - `display_dag()`: Affiche le plan d'exécution
  - `display_progress()`: Progression temps réel
  - `display_report()`: Rapport final formaté
  - `save_report()`: Sauvegarde JSON
  - `generate_report()`: Génère les statistiques

### Exemple d'utilisation

```python
import asyncio
from pathlib import Path
from core.runner import ClaudeRunner
from core.reporter import Reporter

async def run_features():
    runner = ClaudeRunner(max_parallel=3)
    reporter = Reporter(verbose=True)

    tasks = [
        (Path("/wt/auth"), "Implement auth", "auth"),
        (Path("/wt/api"), "Implement API", "api"),
    ]

    results = await runner.run_wave(
        tasks,
        on_progress=reporter.display_progress
    )

    reporter.add_results(results)
    report = reporter.generate_report("MyProject", waves)
    reporter.display_report(report)

asyncio.run(run_features())
```

### Tests

**Runner: 14 tests** couvrant :
- Exécution réussie et erreurs
- Timeouts et JSON parsing
- Mode parallèle et séquentiel
- Vérification binaire Claude

**Reporter: 10 tests** couvrant :
- Génération de rapports
- Sauvegarde JSON
- Affichage DAG et progression

**Exécuter les tests :**
```bash
python3 -m unittest tests/test_runner.py -v
python3 -m unittest tests/test_reporter.py -v
```

**Exécuter la démo intégrée :**
```bash
python3 demo_integrated.py
```

La démo montre :
- Validation du DAG (4 features, 3 vagues)
- Création de 4 worktrees
- Exécution parallèle avec mock Claude CLI
- Rapport final avec speedup de 1.3x
- Cleanup automatique

## Phase 4 - CLI Finale ✅

### Fonctionnalités implémentées

**Module `orchestrate.py`** (~350 lignes) :

- **Classe `OrchestratorConfig`**
  - Chargement et validation de feature_list.json
  - Gestion des paramètres projet et Claude

- **Classe `Orchestrator`**
  - Intégration complète: DAG + Worktree + Runner + Reporter
  - Orchestration de l'exécution par vagues
  - Chargement automatique des prompts

- **Commandes CLI** :
  - `plan` - Affiche le DAG et les estimations
  - `run` - Exécute les features (avec/sans confirmation)
  - `cleanup` - Nettoie les worktrees (--merged, --all)
  - `status` - Affiche l'état du projet et worktrees actifs

### Utilisation

```bash
# Voir le plan d'exécution
python3 orchestrate.py plan

# Vérifier l'état
python3 orchestrate.py status

# Exécuter (avec confirmation)
python3 orchestrate.py run

# Exécuter sans confirmation
python3 orchestrate.py run --yes

# Cleanup après merge
python3 orchestrate.py cleanup --merged
```

### Prompts d'exemple

4 prompts complets pour module GS1 :
- `_context.md` - Contexte projet (stack, standards, conventions)
- `auth-gtin.md` - Validation GTIN selon standards GS1
- `api-lookup.md` - Endpoint REST de recherche
- `batch-import.md` - Import CSV de produits
- `dashboard.md` - Interface Hotwire de visualisation

**Voir le guide complet :** `GUIDE-UTILISATION.md`

## MVP Complet ✅

### Bilan final

| Composant | Lignes | Tests | Statut |
|-----------|--------|-------|--------|
| core/dag.py | ~200 | 16 | ✅ |
| core/worktree.py | ~250 | 17 | ✅ |
| core/runner.py | ~300 | 14 | ✅ |
| core/reporter.py | ~250 | 10 | ✅ |
| orchestrate.py | ~350 | CLI | ✅ |
| **TOTAL** | **~1350** | **57** | **✅** |

### Capacités opérationnelles

RoRchestrator peut maintenant :

1. ✅ Charger une configuration depuis JSON
2. ✅ Valider le graphe de dépendances
3. ✅ Calculer les vagues d'exécution optimales
4. ✅ Créer des worktrees Git isolés
5. ✅ Charger les prompts depuis fichiers .md
6. ✅ Exécuter Claude Code en parallèle (configurable)
7. ✅ Afficher la progression en temps réel
8. ✅ Générer des rapports avec métriques
9. ✅ Sauvegarder les résultats en JSON
10. ✅ Nettoyer automatiquement les worktrees

### Utilisable immédiatement pour

- Projets Rails (GS1 France, RoRworld)
- Projets Node.js/React/Vue
- Projets Python/FastAPI
- Tout projet avec Git + Claude Code CLI

## Configuration

Format minimal de `config/feature_list.json` :

```json
{
  "project": {
    "name": "MonProjet",
    "repo_path": "/chemin/vers/repo",
    "base_branch": "main"
  },
  "features": [
    {
      "id": "feature-a",
      "name": "Feature A",
      "depends_on": [],
      "prompt_file": "prompts/feature-a.md"
    },
    {
      "id": "feature-b",
      "name": "Feature B",
      "depends_on": ["feature-a"],
      "prompt_file": "prompts/feature-b.md"
    }
  ]
}
```

## Ressources

- [Documentation complète](../analyses/2026-01-02-rorchestrator-documentation.md)
- [Claude Code Headless Mode](https://docs.anthropic.com/en/docs/claude-code/headless)
- [Python graphlib](https://docs.python.org/3/library/graphlib.html)

## Licence

Projet interne - Rolland Melet / 101ÉvolutionLab
