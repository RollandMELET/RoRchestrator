# Feature: Authentification GTIN

## Contexte
Voir `_context.md` pour le contexte complet du projet GS1 France.

## Objectif
Implémenter un système de validation des codes GTIN (Global Trade Item Number) selon les standards GS1 pour le module de traçabilité construction.

## Spécifications

### 1. Service GtinValidator

Créer `app/services/gtin_validator.rb` avec :

**Formats supportés :**
- GTIN-8 : 8 chiffres (EAN-8)
- GTIN-12 : 12 chiffres (UPC-A)
- GTIN-13 : 13 chiffres (EAN-13)
- GTIN-14 : 14 chiffres (ITF-14)

**Méthodes :**
```ruby
class GtinValidator
  # Valide un GTIN et retourne true/false
  def self.valid?(gtin)

  # Calcule le digit de contrôle
  def self.check_digit(gtin_without_check)

  # Normalise le GTIN (retire espaces, tirets)
  def self.normalize(gtin)
end
```

**Algorithme du digit de contrôle (modulo 10) :**
1. De droite à gauche, multiplier les chiffres alternativement par 3 et 1
2. Sommer tous les produits
3. Le digit de contrôle = (10 - (somme % 10)) % 10

### 2. Extension Model Product

Ajouter à `app/models/product.rb` :

```ruby
class Product < ApplicationRecord
  # Validation
  validates :gtin, presence: true, length: { in: 8..14 }
  validate :gtin_must_be_valid

  # Méthode de validation
  def valid_gtin?
    GtinValidator.valid?(gtin)
  end

  # Scope
  scope :with_valid_gtin, -> { where(...) }

  private

  def gtin_must_be_valid
    unless valid_gtin?
      errors.add(:gtin, "n'est pas un GTIN valide selon GS1")
    end
  end
end
```

### 3. Tests RSpec

Créer `spec/services/gtin_validator_spec.rb` :

**Cas de tests requis :**
- ✅ GTIN-8 valide (ex: `12345670`)
- ✅ GTIN-12 valide (ex: `123456789012`)
- ✅ GTIN-13 valide (ex: `1234567890128`)
- ✅ GTIN-14 valide (ex: `12345678901231`)
- ❌ Digit de contrôle invalide
- ❌ Longueur invalide (5, 9, 15 chiffres)
- ❌ Caractères non-numériques
- ✅ Normalisation (avec espaces/tirets)

## Contraintes techniques

- Ruby 3.2+, Rails 7.1+
- **Pas de gem externe** pour la validation GTIN (implémentation native)
- Code documenté avec YARD
- Messages d'erreur en français

## Critères de succès

- [ ] `bundle exec rspec spec/services/gtin_validator_spec.rb` passe
- [ ] `bundle exec rubocop app/services/gtin_validator.rb` sans erreur
- [ ] Documentation YARD complète
- [ ] Tous les formats GTIN supportés
- [ ] Validation ActiveRecord fonctionne sur Product

## Fichiers à créer/modifier

- `app/services/gtin_validator.rb` (nouveau)
- `app/models/product.rb` (modifier)
- `spec/services/gtin_validator_spec.rb` (nouveau)
