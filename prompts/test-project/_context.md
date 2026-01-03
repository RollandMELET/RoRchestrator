# Contexte - Test Project TODO App

## Objectif du Projet

Application simple de gestion de tâches (TODO) pour tester RoRchestrator en conditions réelles.

## Stack Technique

- **Python** : 3.9+ (stdlib uniquement, pas de dépendances)
- **Storage** : Fichier JSON local
- **Interface** : CLI (argparse)
- **Tests** : unittest (stdlib)

## Structure du Projet

```
test-project/
├── README.md
├── CLAUDE.md
├── src/
│   ├── task.py       # Modèle Task
│   ├── storage.py    # Persistance JSON
│   └── cli.py        # Interface CLI
├── tests/
│   ├── test_task.py
│   ├── test_storage.py
│   └── test_cli.py
└── data/
    └── tasks.json    # Données persistantes
```

## Conventions

### Nommage
- Classes : PascalCase (`Task`, `TaskStorage`)
- Fonctions : snake_case (`load_tasks`, `save_tasks`)
- Fichiers : snake_case (`task.py`, `test_task.py`)

### Tests
- Un fichier `test_*.py` par module
- Utiliser `unittest.TestCase`
- Coverage minimale : 80%

### Documentation
- Docstrings Google style pour toutes les classes et fonctions publiques
- Type hints pour les signatures

### Format de commit
```
feat(task-model): add Task class with basic attributes

- Create Task dataclass
- Add to_dict/from_dict methods
- Add unit tests

🤖 Generated with Claude Code
```

## Modèle de Données

### Task

```python
@dataclass
class Task:
    id: str              # UUID
    title: str          # Titre de la tâche
    done: bool          # Statut (complétée ou non)
    created_at: str     # ISO datetime
    updated_at: str     # ISO datetime (optionnel)
```

### Format JSON

```json
{
  "tasks": [
    {
      "id": "abc-123",
      "title": "Ma première tâche",
      "done": false,
      "created_at": "2026-01-02T14:30:00"
    }
  ]
}
```

## Critères de Qualité

Pour chaque feature :
1. ✅ Tests unitaires passent
2. ✅ Code documenté avec docstrings
3. ✅ Pas de dépendances externes
4. ✅ Compatible Python 3.9+
