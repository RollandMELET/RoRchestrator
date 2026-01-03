# Contexte Projet GS1 France - Module Traçabilité

## Stack technique

- **Backend** : Ruby 3.2.2, Rails 7.1.3
- **Base de données** : PostgreSQL 15
- **Frontend** : Hotwire (Turbo + Stimulus)
- **Tests** : RSpec
- **Linting** : Rubocop

## Standards GS1

### Identifiants clés
- **GTIN** : Global Trade Item Number (8, 12, 13 ou 14 chiffres)
- **GLN** : Global Location Number (13 chiffres)
- **SSCC** : Serial Shipping Container Code (18 chiffres)

### Règles de validation
- GTIN utilise un digit de contrôle (modulo 10)
- GLN suit le même algorithme que GTIN-13
- Tous les identifiants doivent être numériques uniquement

## Conventions projet

### Nommage
- **Modèles** : en français (`Produit`, `Emplacement`, `Mouvement`)
- **API REST** : en anglais (`/api/v1/products`, `/api/v1/locations`)
- **Tests** : un fichier `_spec.rb` par classe

### Format commits
```
feat(#id): description courte

- Détail changement 1
- Détail changement 2

🤖 Generated with Claude Code
```

## Structure existante

```
app/
├── controllers/
│   ├── api/v1/          # API REST endpoints
│   └── ...
├── models/
│   ├── product.rb       # Modèle Produit
│   ├── location.rb      # Modèle Emplacement
│   └── movement.rb      # Modèle Mouvement
├── services/            # Business logic
└── views/              # Templates Hotwire
```

## Règles de qualité

1. **Tests obligatoires** : Chaque feature doit avoir des tests RSpec
2. **Standards GS1** : Respecter strictement les formats d'identifiants
3. **Documentation inline** : Méthodes publiques documentées avec YARD
4. **Rubocop** : Le code doit passer `bundle exec rubocop` sans erreur
5. **I18n** : Messages utilisateur en français, code en anglais
