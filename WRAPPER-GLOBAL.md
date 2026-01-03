# Wrapper Global RoRchestrator

Documentation du script wrapper global `~/bin/rorchestrator`.

---

## Installation

Le wrapper a été installé dans :
```
~/bin/rorchestrator
```

Et `~/bin` a été ajouté à ton PATH dans `~/.zshrc`.

### Activation Immédiate

Pour cette session terminal :
```bash
export PATH="$HOME/bin:$PATH"
```

Pour les nouvelles sessions :
```bash
# Redémarrer le terminal OU
source ~/.zshrc
```

### Vérification

```bash
which rorchestrator
# → /Users/rollandmelet/bin/rorchestrator

rorchestrator --help
# → Affiche l'aide
```

---

## Utilisation

### Première Utilisation dans un Projet

```bash
# 1. Aller dans ton projet (doit être un repo Git)
cd /path/to/ton/projet

# 2. Lancer rorchestrator (il s'installe automatiquement)
rorchestrator --help
```

**Ce qui se passe :**
```
ℹ️  RoRchestrator n'est pas installé dans ce projet
ℹ️  Installation en cours...

✅ RoRchestrator installé (version 1.0.0-mvp)

⚠️  Configuration requise :
  1. Éditer orchestrator/config/feature_list.json
  2. Créer les prompts dans orchestrator/prompts/
  3. Lancer: rorchestrator plan
```

Un répertoire `orchestrator/` est créé avec tout le nécessaire.

### Configuration

```bash
# 1. Copier le template
cd orchestrator
cp config/feature_list.example.json config/feature_list.json

# 2. Éditer la config
nano config/feature_list.json
```

**Modifier au minimum :**
- `project.name` : Nom de ton projet
- `project.repo_path` : Généralement `..` (parent de orchestrator/)
- `project.base_branch` : `main`, `master`, ou `develop`
- `features` : Tes features avec dépendances

```bash
# 3. Créer les prompts
mkdir -p prompts/mon-module
nano prompts/mon-module/feature-1.md
```

### Workflow Standard

Depuis **n'importe quel projet** avec RoRchestrator installé :

```bash
# Voir le plan
rorchestrator plan

# Vérifier l'état
rorchestrator status

# Exécuter (avec confirmation)
rorchestrator run

# Exécuter sans confirmation
rorchestrator run --yes

# Cleanup après merge
rorchestrator cleanup --merged

# Cleanup total (attention!)
rorchestrator cleanup --all
```

---

## Fonctionnement du Wrapper

### 1. Détection et Installation Auto

```bash
cd MonProjet/
rorchestrator plan
```

Le wrapper :
1. ✅ Vérifie que tu es dans un repo Git
2. ✅ Détecte si `orchestrator/` existe
3. ✅ Si absent, copie depuis `/path/to/101EvolutionLab/orchestrator`
4. ✅ Lance la commande demandée

### 2. Exécution Transparente

Une fois installé, le wrapper est **transparent** :

```bash
rorchestrator plan
# = cd orchestrator && python3 orchestrate.py plan
```

### 3. Mise à Jour

Si tu améliores RoRchestrator dans 101EvolutionLab :

**Les nouveaux projets** bénéficient automatiquement de la dernière version (copie lors de la première installation).

**Les projets existants** gardent leur version. Pour mettre à jour :

```bash
cd MonProjet/
rm -rf orchestrator
rorchestrator --help  # Réinstalle la dernière version
```

---

## Exemples d'Utilisation

### Nouveau Projet GS1

```bash
cd ~/Développement/Projets/GS1-NouveauModule

# Initialiser Git si nécessaire
git init
git add .
git commit -m "Initial commit"

# Installer RoRchestrator
rorchestrator plan
# → Copie automatique, affiche l'aide

# Configurer
cd orchestrator
cp config/feature_list.example.json config/feature_list.json
nano config/feature_list.json

# Adapter les prompts GS1
cp -r prompts/auth-gtin.md prompts/mon-module/
nano prompts/mon-module/auth-gtin.md

# Lancer
cd ..
rorchestrator plan
rorchestrator run --yes
```

### Projet RoRworld Client

```bash
cd ~/Développement/Clients/ClientX-App

# RoRchestrator s'installe au premier appel
rorchestrator status

# Configurer pour React + Node.js
cd orchestrator
nano config/feature_list.json
```

**Config exemple React :**
```json
{
  "project": {
    "name": "ClientX-Frontend",
    "repo_path": "..",
    "base_branch": "develop",
    "max_parallel": 3
  },
  "claude": {
    "allowed_tools": [
      "Read", "Write", "Edit",
      "Bash(npm test)",
      "Bash(npm run lint)"
    ]
  },
  "features": [
    {
      "id": "setup-vite",
      "prompt_file": "setup-vite.md",
      "depends_on": []
    },
    {
      "id": "header-component",
      "prompt_file": "header.md",
      "depends_on": ["setup-vite"]
    }
  ]
}
```

```bash
# Créer les prompts
nano prompts/setup-vite.md

# Lancer
cd ..
rorchestrator run
```

---

## Commandes Disponibles

### rorchestrator plan

Affiche le plan d'exécution sans exécuter.

**Utilise quand :**
- Tu veux vérifier le DAG avant de lancer
- Tu veux voir l'estimation de coût
- Tu veux comprendre l'ordre d'exécution

**Sortie :**
```
PLAN D'EXÉCUTION
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

VAGUE 1
  │ feature-a (aucune dépendance)

VAGUE 2 [PARALLÈLE]
  │ feature-b ← attend ['feature-a']
  │ feature-c ← attend ['feature-a']

💰 Tokens estimés: 120,000
⚡ Speedup: 1.5x
```

### rorchestrator run

Exécute les features.

**Options :**
- `--yes` ou `-y` : Skip la confirmation
- `--sequential` : Mode séquentiel (debugging)
- `--config PATH` : Config custom (défaut: config/feature_list.json)

**Exemples :**
```bash
rorchestrator run              # Avec confirmation
rorchestrator run --yes        # Sans confirmation
rorchestrator run --sequential # Mode debug
```

### rorchestrator cleanup

Nettoie les worktrees.

**Options :**
- `--merged` : Uniquement les worktrees mergés (recommandé)
- `--all` : TOUS les worktrees (attention!)

**Exemples :**
```bash
# Après avoir mergé les features
rorchestrator cleanup --merged

# Nettoyer tout (si tu veux restart)
rorchestrator cleanup --all
```

### rorchestrator status

Affiche l'état du projet.

**Sortie :**
```
STATUT DU PROJET
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📁 Projet : MonProjet
📂 Repo   : /path/to/repo
🌿 Branche: main
📊 Features: 4

🔧 Worktrees actifs: 2
  • feature-a → feature/feature-a
  • feature-b → feature/feature-b

🤖 Claude CLI: ✅ disponible
   Version: 2.0.76
```

---

## Workflow Recommandé

### Setup Initial (une fois par projet)

```bash
cd MonProjet/
rorchestrator plan              # Installe RoRchestrator
cd orchestrator
cp config/feature_list.example.json config/feature_list.json
nano config/feature_list.json   # Adapter à ton projet
```

### Développement (répétable)

```bash
cd MonProjet/

# 1. Planifier
rorchestrator plan

# 2. Exécuter
rorchestrator run --yes

# 3. Attendre (15-20 min selon features)
# Pendant ce temps, tu peux faire autre chose

# 4. Review
cd worktrees/feature-a
code .

# 5. Si OK, merger
cd ..
git checkout main
git merge feature/feature-a
git push

# 6. Cleanup
rorchestrator cleanup --merged
```

---

## Avantages du Wrapper Global

### ✅ Bénéfices

1. **Une seule commande** : `rorchestrator` au lieu de `cd orchestrator && python3 orchestrate.py`

2. **Installation automatique** : Pas besoin de copier manuellement

3. **Toujours à jour** : Nouveaux projets utilisent la dernière version

4. **Cohérence** : Même outil partout (GS1, RoRworld, projets perso)

5. **Workflow simplifié** :
   ```bash
   cd MonProjet
   rorchestrator run --yes
   # C'est tout !
   ```

### Comparaison

**Sans wrapper :**
```bash
cd MonProjet
cp -r /path/to/orchestrator .
cd orchestrator
python3 orchestrate.py plan
cd ..
cd orchestrator
python3 orchestrate.py run
```

**Avec wrapper :**
```bash
cd MonProjet
rorchestrator plan
rorchestrator run
```

---

## Troubleshooting

### "command not found: rorchestrator"

```bash
# Vérifier l'installation
ls -la ~/bin/rorchestrator

# Vérifier le PATH
echo $PATH | grep "$HOME/bin"

# Si absent, activer :
export PATH="$HOME/bin:$PATH"

# Ou redémarrer le terminal
```

### "Source RoRchestrator introuvable"

Le wrapper cherche RoRchestrator dans :
```
/Users/rollandmelet/Développement/Projets/101EvolutionLab/orchestrator
```

Si tu déplaces 101EvolutionLab, éditer `~/bin/rorchestrator` :
```bash
nano ~/bin/rorchestrator
# Modifier la ligne :
# RORCHESTRATOR_SOURCE="/nouveau/chemin/orchestrator"
```

### "Vous n'êtes pas dans un repo Git"

RoRchestrator nécessite Git :
```bash
git init
git add .
git commit -m "Initial commit"
```

---

## Désinstallation

### Retirer le wrapper

```bash
rm ~/bin/rorchestrator
```

### Retirer de projets spécifiques

```bash
cd MonProjet/
rm -rf orchestrator
```

---

## Mises à Jour

### Mettre à jour le wrapper

Quand tu améliores RoRchestrator dans 101EvolutionLab :

1. Le wrapper dans `~/bin/rorchestrator` pointe déjà vers la source
2. Les **nouveaux projets** auront automatiquement la dernière version
3. Les **projets existants** gardent leur version

### Mettre à jour un projet existant

```bash
cd MonProjet/
rm -rf orchestrator
rorchestrator plan  # Réinstalle la dernière version
```

**Attention :** Cela écrase ta config ! Sauvegarde `config/feature_list.json` avant.

```bash
# Meilleure approche :
cp orchestrator/config/feature_list.json /tmp/my-config.json
rm -rf orchestrator
rorchestrator plan
cp /tmp/my-config.json orchestrator/config/feature_list.json
```

---

## Résumé

### Ce qui a été fait

- ✅ Script `~/bin/rorchestrator` créé
- ✅ Permissions exécutables configurées
- ✅ `~/bin` ajouté au PATH dans `~/.zshrc`
- ✅ Installation automatique dans les projets
- ✅ Testé et validé

### Comment l'utiliser maintenant

**Dans n'importe quel projet Git :**

```bash
cd /ton/projet
rorchestrator plan    # Première fois : installe + affiche plan
rorchestrator run     # Exécute les features
```

**C'est disponible globalement, mais :**
- Chaque projet a sa propre copie de RoRchestrator
- Avec sa propre configuration
- Ça évite les conflits entre projets

---

**Le wrapper est prêt ! Tu peux maintenant utiliser `rorchestrator` depuis n'importe quel projet. 🚀**
