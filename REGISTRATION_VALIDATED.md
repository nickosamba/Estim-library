# État Validé : Système d'Inscription (22/05/2026)

**ATTENTION : Ce module est considéré comme STABLE et VALIDÉ. Ne pas modifier sans accord explicite.**

## 1. Caractéristiques Validées
- **Champs Essentiels** : Nom d'utilisateur, Email, Mot de passe, Campus, Filière, Niveau.
- **Langue** : 100% Français (réglage global `fr-fr`).
- **Sécurité Serveur** : Validation stricte via `full_clean()` dans `User.save()`.
- **Automatisation** : Le département est automatiquement déduit de la filière.
- **UX** : Affichage/Masquage du mot de passe (icône œil) fonctionnel.

## 2. Contraintes Critiques (À ne pas casser)
- **Email** : Doit rester `unique=True` et obligatoire au niveau du modèle.
- **Filière/Campus/Niveau** : Doivent rester obligatoires (`blank=False`).
- **Accès Admin** : Seul le `is_superuser` peut être `is_staff`. La méthode `save()` de `User` force ce comportement.

## 3. Fichiers concernés
- `accounts/models.py` (Logique de sauvegarde et contraintes)
- `accounts/forms.py` (Structure du formulaire et labels)
- `accounts/templates/accounts/register.html` (Interface et JavaScript de l'œil)
- `library_project/settings.py` (Configuration de la langue)

---
*Dernière vérification par tests automatisés : RÉUSSIE (22/05/2026)*
