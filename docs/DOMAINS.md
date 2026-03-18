# Domaines — Pourquoi les seuils varient

> Un score de similarite de 0.88 est "identique" dans une conversation quotidienne
> mais "changement significatif" dans un contrat legal. SDE s'adapte au contexte.

---

## Le probleme du seuil universel

Imagine ce changement dans un contrat :

```
AVANT : "Le vendeur DOIT livrer sous 30 jours."
APRES : "Le vendeur PEUT livrer dans un delai raisonnable."
```

La similarite cosinus entre ces deux phrases = ~0.82.

```
Avec un seuil unique de 0.80 :
  0.82 >= 0.80 -> [identical]        FAUX, c'est un vrai changement juridique !

Avec le profil legal (seuil identical = 0.96) :
  0.82 < 0.96  -> [semantic_shift]   CORRECT
```

---

## Tableau des seuils

```
+------------+-----------+---------+---------------+-----------------------------+
| Domaine    | identical | shift   | contradiction | Pourquoi ces seuils ?       |
+------------+-----------+---------+---------------+-----------------------------+
| default    |  >= 0.92  | >= 0.75 |    < 0.40     | Equilibre general           |
| legal      |  >= 0.96  | >= 0.85 |    < 0.50     | "shall" vs "may" = juridique|
| medical    |  >= 0.95  | >= 0.82 |    < 0.45     | 10mg vs 100mg = vital       |
| code       |  >= 0.90  | >= 0.70 |    < 0.35     | Refactoring = variation OK  |
| journalism |  >= 0.91  | >= 0.72 |    < 0.38     | Spin vs faits               |
+------------+-----------+---------+---------------+-----------------------------+
```

---

## Domaine `legal` — Le plus strict

**Seuil identical = 0.96**

Les changements qui "sembleraient" mineurs sont souvent fondamentaux en droit :

```
Changement de modal :
  "Le prestataire DOIT livrer"   (obligatoire)
  "Le prestataire PEUT livrer"   (optionnel)
  Score ~ 0.88
    -> profil legal   : [semantic_shift]   correct
    -> profil default : [identical]        DANGEREUX

Changement de quantificateur :
  "30 jours"           (delai precis, opposable)
  "delai raisonnable"  (vague, sujet a interpretation)
  Score ~ 0.75 -> [semantic_shift]

Changement de portee :
  "y compris"   vs   "limite a"
  Score ~ 0.60 -> [contradiction]

Changement de responsabilite :
  "Limite aux dommages directs"
  "Etendue a tous les dommages y compris indirects et punitifs"
  Score ~ 0.45 -> [contradiction]
```

---

## Domaine `medical` — Precision vitale

**Seuil identical = 0.95**

```
Dosage :
  "Administrer 10mg deux fois par jour"
  "Administrer 100mg deux fois par jour"
  Difference x10 -> potentiellement fatal

Contre-indication :
  "Deconseille chez les patients avec insuffisance renale"
  "Recommande chez les patients avec insuffisance renale"
  Inversion complete -> risque vital

Voie d'administration :
  "Administrer par voie orale"
  "Administrer par voie intraveineuse"
  Completement different cliniquement

Frequence :
  "Une fois par jour"   vs   "Deux fois par jour"
  Doublement de la dose quotidienne
```

---

## Domaine `code` — Le plus souple

**Seuil identical = 0.90** (le plus bas)

Le code refactored a naturellement plus de variation lexicale tout en conservant la logique :

```python
# Version A                      # Version B (identique semantiquement)
for i in range(len(items)):      for item in items:
    print(items[i])                  print(item)
```

Ces deux fonctions font la meme chose. Le seuil souple evite de faux "semantic_shift".

```
Mais ceci est une vraie contradiction :
  return True   ->   return False
  Score ~ 0.20  -> [contradiction]   correct !
```

---

## Domaine `journalism` — Spin vs faits

**Seuil modere** pour distinguer le style editorial des faits :

```
Memes faits, ton different :
  "Le ministre a defendu la decision, citant la necessite economique."
  "Le ministre s'est explique sur cette decision controversee."
  Score ~ 0.75 -> [semantic_shift]   changement de framing

Paraphrase simple :
  "L'entreprise annonce une hausse de 15% de son CA."
  "La societe fait etat d'une progression de 15% de ses revenus."
  Score ~ 0.92 -> [identical]   correct, meme info

Inversion factuelle :
  "Le verdict a ete 'non coupable'."
  "L'accuse a ete reconnu coupable."
  Score ~ 0.30 -> [contradiction]   correct !
```

---

## Ajouter un domaine personnalise

```python
# Dans core/domain_profiles.py, ajouter :
_PROFILES["finance"] = DomainProfile(
    name="finance",
    identical_threshold=0.94,
    shift_threshold=0.80,
    contradiction_threshold=0.45,
    alignment_threshold=0.18,
    rationale="Precision elevee pour taux, montants et conditions.",
)
```

Puis ajouter `"finance"` dans l'enum de [api/schemas.py](../api/schemas.py) et relancer le serveur.
