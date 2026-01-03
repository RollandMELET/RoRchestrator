# Feature: API Lookup Produit

## Contexte
Voir `_context.md` pour le contexte complet du projet GS1 France.

## Dépendances
Cette feature **dépend de** :
- ✅ `auth-gtin` : GtinValidator doit être implémenté

## Objectif
Créer un endpoint REST pour rechercher un produit par son code GTIN.

## Spécifications

### 1. Controller API

Créer `app/controllers/api/v1/products_controller.rb` :

```ruby
module Api
  module V1
    class ProductsController < ApiController
      # GET /api/v1/products/:gtin
      def show
        gtin = params[:gtin]

        # Valider le GTIN avec GtinValidator
        unless GtinValidator.valid?(gtin)
          render json: { error: "GTIN invalide" }, status: :bad_request
          return
        end

        # Rechercher le produit
        product = Product.find_by(gtin: gtin)

        if product
          render json: product, status: :ok
        else
          render json: { error: "Produit non trouvé" }, status: :not_found
        end
      end
    end
  end
end
```

### 2. Routes

Ajouter à `config/routes.rb` :

```ruby
namespace :api do
  namespace :v1 do
    resources :products, only: [:show], param: :gtin
  end
end
```

### 3. Serializer (optionnel)

Si vous voulez un format JSON spécifique, créer un serializer.
Sinon, Rails utilisera `.as_json` par défaut.

### 4. Tests RSpec

Créer `spec/requests/api/v1/products_spec.rb` :

**Cas de tests requis :**
- ✅ GET avec GTIN valide et produit existant → 200 OK
- ✅ GET avec GTIN valide mais produit inexistant → 404 Not Found
- ❌ GET avec GTIN invalide → 400 Bad Request
- ✅ Format JSON de la réponse correct

## Contraintes techniques

- API REST suivant les conventions Rails
- Utiliser `GtinValidator.valid?()` pour validation
- Réponses JSON avec codes HTTP appropriés
- Tests de requêtes (request specs)

## Critères de succès

- [ ] `bundle exec rspec spec/requests/api/v1/products_spec.rb` passe
- [ ] Endpoint accessible via `curl`
- [ ] Validation GTIN fonctionne
- [ ] Messages d'erreur clairs en français

## Fichiers à créer/modifier

- `app/controllers/api/v1/products_controller.rb` (nouveau)
- `config/routes.rb` (modifier)
- `spec/requests/api/v1/products_spec.rb` (nouveau)

## Exemple de test manuel

```bash
# Produit existant
curl http://localhost:3000/api/v1/products/1234567890128

# GTIN invalide
curl http://localhost:3000/api/v1/products/invalid
# → {"error": "GTIN invalide"}
```
