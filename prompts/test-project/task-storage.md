# Feature: Task Storage

## Contexte

Cette feature **dépend de** :
- ✅ task-model : La classe Task doit exister

## Objectif

Créer un système de persistance JSON pour sauvegarder et charger les tâches.

## Spécifications

### 1. Créer src/storage.py

Implémenter une classe `TaskStorage` avec :

**Méthodes :**
- `__init__(file_path)` : Initialise avec chemin du fichier JSON
- `save(tasks: List[Task])` : Sauvegarde la liste de tasks dans le JSON
- `load() -> List[Task]` : Charge les tasks depuis le JSON
- `add(task: Task)` : Ajoute une task et sauvegarde
- `update(task: Task)` : Met à jour une task existante
- `delete(task_id: str)` : Supprime une task par ID
- `get(task_id: str) -> Optional[Task]` : Récupère une task par ID
- `get_all() -> List[Task]` : Récupère toutes les tasks

**Gestion des erreurs :**
- Si le fichier JSON n'existe pas, créer un fichier vide `{"tasks": []}`
- Si le JSON est corrompu, lever une exception claire

**Exemple d'implémentation :**
```python
import json
from pathlib import Path
from typing import List, Optional
from task import Task

class TaskStorage:
    def __init__(self, file_path: str = "data/tasks.json"):
        self.file_path = Path(file_path)
        self.file_path.parent.mkdir(exist_ok=True)

        # Créer le fichier s'il n'existe pas
        if not self.file_path.exists():
            self._write_empty()

    def _write_empty(self):
        self.file_path.write_text(json.dumps({"tasks": []}, indent=2))
```

### 2. Créer tests/test_storage.py

Tests requis :
- ✅ Création du fichier JSON s'il n'existe pas
- ✅ save() + load() roundtrip fonctionne
- ✅ add() ajoute une task et persiste
- ✅ update() modifie une task existante
- ✅ delete() supprime une task
- ✅ get() récupère une task par ID
- ✅ get_all() retourne toutes les tasks
- ✅ Gestion fichier JSON corrompu

## Structure des Fichiers

Créer :
- `src/storage.py` (nouveau)
- `tests/test_storage.py` (nouveau)
- `data/` directory (sera créé automatiquement)

## Critères de Succès

- [ ] `python -m unittest tests/test_storage.py` passe
- [ ] Persistance fonctionne (redémarrage app = données conservées)
- [ ] Gestion propre des erreurs (fichier manquant, JSON invalide)
- [ ] Code documenté avec docstrings

## Notes

Utiliser `json.dumps(indent=2)` pour un JSON lisible.
Assurer la thread-safety n'est pas requis pour ce MVP.
