# Feature: Task Model

## Objectif

Créer le modèle de données `Task` pour représenter une tâche dans l'application TODO.

## Spécifications

### 1. Créer src/task.py

Implémenter une classe `Task` avec :

**Attributs :**
- `id` (str) : UUID unique de la tâche
- `title` (str) : Titre/description de la tâche
- `done` (bool) : Statut (True = complétée, False = à faire)
- `created_at` (str) : Date de création en format ISO (YYYY-MM-DDTHH:MM:SS)

**Méthodes :**
- `to_dict()` : Convertit l'objet en dictionnaire pour JSON
- `from_dict(data)` : Crée un Task depuis un dictionnaire (classmethod)
- `__str__()` : Représentation string lisible

**Exemple d'implémentation :**
```python
from dataclasses import dataclass
from datetime import datetime
import uuid

@dataclass
class Task:
    id: str
    title: str
    done: bool
    created_at: str

    @classmethod
    def create(cls, title: str) -> "Task":
        """Crée une nouvelle tâche."""
        return cls(
            id=str(uuid.uuid4()),
            title=title,
            done=False,
            created_at=datetime.now().isoformat()
        )
```

### 2. Créer tests/test_task.py

Tests requis :
- ✅ Création d'une tâche avec Task.create()
- ✅ Conversion to_dict() retourne un dict valide
- ✅ Reconstruction from_dict() fonctionne
- ✅ Roundtrip : Task → dict → Task préserve les données
- ✅ Validation des attributs requis

## Structure des Fichiers

Créer :
- `src/task.py` (nouveau)
- `src/__init__.py` (nouveau, vide)
- `tests/test_task.py` (nouveau)
- `tests/__init__.py` (nouveau, vide)

## Critères de Succès

- [ ] `python -m unittest tests/test_task.py` passe
- [ ] Tous les attributs sont documentés
- [ ] Type hints présents
- [ ] Aucune dépendance externe (stdlib uniquement)

## Notes

Cette feature est la **base** pour les autres features. Elle doit être simple et robuste.
