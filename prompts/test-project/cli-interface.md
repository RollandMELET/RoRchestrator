# Feature: CLI Interface

## Contexte

Cette feature **dépend de** :
- ✅ task-model : Classe Task disponible
- ✅ task-storage : Classe TaskStorage disponible

## Objectif

Créer une interface en ligne de commande pour gérer les tâches.

## Spécifications

### 1. Créer src/cli.py

Implémenter un CLI avec argparse supportant :

**Commandes requises :**

```bash
# Ajouter une tâche
python src/cli.py add "Acheter du lait"

# Lister toutes les tâches
python src/cli.py list

# Marquer une tâche comme complétée
python src/cli.py done <task-id>

# Supprimer une tâche
python src/cli.py delete <task-id>
```

**Format d'affichage pour 'list' :**
```
TODO Tasks:
  [ ] abc-123 - Acheter du lait (créée le 2026-01-02)
  [✓] def-456 - Apprendre Python (créée le 2026-01-01)

2 tâches (1 complétée, 1 à faire)
```

**Exemple d'implémentation :**
```python
import argparse
from storage import TaskStorage
from task import Task

def cmd_add(args):
    """Ajoute une nouvelle tâche."""
    storage = TaskStorage()
    task = Task.create(title=args.title)
    storage.add(task)
    print(f"✅ Tâche ajoutée: {task.title}")

def cmd_list(args):
    """Liste toutes les tâches."""
    storage = TaskStorage()
    tasks = storage.get_all()

    if not tasks:
        print("Aucune tâche.")
        return

    print("TODO Tasks:")
    for task in tasks:
        status = "[✓]" if task.done else "[ ]"
        print(f"  {status} {task.id[:8]} - {task.title}")

    done_count = sum(1 for t in tasks if t.done)
    print(f"\n{len(tasks)} tâches ({done_count} complétée(s))")

def main():
    parser = argparse.ArgumentParser(description="Simple TODO CLI")
    subparsers = parser.add_subparsers(dest="command")

    # add
    add_parser = subparsers.add_parser("add", help="Ajouter une tâche")
    add_parser.add_argument("title", help="Titre de la tâche")

    # list
    list_parser = subparsers.add_parser("list", help="Lister les tâches")

    # done
    done_parser = subparsers.add_parser("done", help="Marquer complétée")
    done_parser.add_argument("task_id", help="ID de la tâche")

    # delete
    delete_parser = subparsers.add_parser("delete", help="Supprimer")
    delete_parser.add_argument("task_id", help="ID de la tâche")

    args = parser.parse_args()

    if args.command == "add":
        cmd_add(args)
    elif args.command == "list":
        cmd_list(args)
    # ... etc

if __name__ == "__main__":
    main()
```

### 2. Créer tests/test_cli.py

Tests requis :
- ✅ add crée une tâche
- ✅ list affiche les tâches
- ✅ done marque une tâche comme complétée
- ✅ delete supprime une tâche
- ✅ Commande sans argument affiche l'aide

**Note :** Pour tester le CLI, utiliser `subprocess` ou parser directement.

### 3. Rendre le CLI exécutable

Créer un wrapper à la racine :

**todo.py :**
```python
#!/usr/bin/env python3
import sys
from src.cli import main

if __name__ == "__main__":
    sys.exit(main())
```

Puis :
```bash
chmod +x todo.py
```

## Structure des Fichiers

Créer :
- `src/cli.py` (nouveau)
- `tests/test_cli.py` (nouveau)
- `todo.py` (nouveau, à la racine)

## Critères de Succès

- [ ] `python -m unittest tests/test_cli.py` passe
- [ ] `python todo.py add "Test"` fonctionne
- [ ] `python todo.py list` affiche la tâche
- [ ] `python todo.py done <id>` marque comme complétée
- [ ] `python todo.py delete <id>` supprime
- [ ] Aide affichée avec `python todo.py --help`

## Workflow de Test Manuel

```bash
# Ajouter des tâches
python todo.py add "Tâche 1"
python todo.py add "Tâche 2"

# Lister
python todo.py list

# Marquer complétée (copier l'ID depuis list)
python todo.py done abc-123

# Lister à nouveau
python todo.py list

# Supprimer
python todo.py delete abc-123
```

## Notes

- Gérer proprement les IDs partiels (accepter les 8 premiers caractères)
- Messages clairs en cas d'erreur (tâche inexistante, etc.)
- Interface user-friendly
