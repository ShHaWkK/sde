# How SDE Works — Under the Hood

> **TL;DR** : SDE découpe les textes en morceaux, transforme chaque morceau en vecteur numérique, cherche le meilleur appariement possible, puis classe chaque paire selon sa similarité.

---

## Vue d'ensemble du pipeline

```
 Texte A                            Texte B
   |                                   |
   v                                   v
+----------+                    +----------+
| Chunker  |  decoupage         | Chunker  |
+----+-----+  intelligent      +----+-----+
     |                              |
     v                              v
  [chunk_a1]                    [chunk_b1]
  [chunk_a2]   ------------>    [chunk_b2]
  [chunk_a3]    Embedder        [chunk_b3]
     |          (-> vecteurs)        |
     +--------------------+---------+
                          |
                          v
                 +-----------------+
                 | Matrice N x M   |  similarite cosinus
                 | de similarite   |  entre toutes les paires
                 +--------+--------+
                          |
                          v
                 +-----------------+
                 | Algorithme      |  appariement optimal
                 | Hongrois        |  (pas greedy !)
                 +--------+--------+
                          |
                          v
                 +-----------------+
                 | Scorer          |  seuils par domaine
                 | + Explainer     |  -> verdict + explication
                 +--------+--------+
                          |
                          v
                    DiffResult {
                      overall, global_score,
                      delta_index, chunks[]
                    }
```

---

## Etape 1 — Le Chunker : decouper intelligemment

On ne compare pas deux textes entiers d'un coup. On les decoupe d'abord en **unites semantiques independantes**.

### Pourquoi ?

Comparer "Le vendeur doit livrer sous 30 jours. Le paiement est obligatoire." avec "Le vendeur peut livrer a sa convenance." d'un bloc masque *ou* est le changement. En decoupant, on sait exactement quelle clause a change.

### Les 3 strategies

```
+-----------------+--------------------------------------+---------------------+
| Strategie       | Comment                              | Ideal pour          |
+-----------------+--------------------------------------+---------------------+
| sentence        | NLTK sent_tokenize, fusionne les     | Clauses legales,    |
|                 | phrases trop courtes (< 5 mots)      | prescriptions       |
+-----------------+--------------------------------------+---------------------+
| paragraph       | Coupe sur les lignes vides (\n\n)    | Contrats, rapports  |
|                 |                                      | structures          |
+-----------------+--------------------------------------+---------------------+
| sliding_window  | Fenetres glissantes de N phrases     | Textes longs et     |
|                 | (chevauchement configurable)         | continus            |
+-----------------+--------------------------------------+---------------------+

auto -> selectionne automatiquement selon la longueur et la structure
```

### Exemple concret

```
Texte A :
"Le vendeur doit livrer sous 30 jours.
 Le paiement doit etre effectue avant la livraison."

                 | chunk_sentence
                 v

Chunk A1 : "Le vendeur doit livrer sous 30 jours."
Chunk A2 : "Le paiement doit etre effectue avant la livraison."
```

---

## Etape 2 — L'Embedder : transformer du texte en nombres

Chaque chunk est converti en un **vecteur dense** de nombres (ex: 384 dimensions) par un modele de langage neural.

```
"Le vendeur doit livrer sous 30 jours."
            |
            v  all-MiniLM-L6-v2
            |
   [0.23, -0.14, 0.87, 0.03, ... ]  <- 384 nombres
```

**L'idee cle** : deux phrases qui disent la meme chose en mots differents produiront des vecteurs tres proches. Deux phrases contradictoires auront des vecteurs eloignes.

```
"Tu dois payer."          -> [0.12, 0.45, ...]
"Le paiement est requis." -> [0.14, 0.43, ...]  <- proches !
"Aucun paiement requis."  -> [0.89, -0.23, ...] <- loin !
```

**Mesure de proximite** = similarite cosinus :

```
score = cos(angle entre les deux vecteurs)

  1.0  -> identiques semantiquement
  0.7  -> sens similaire, formulation differente
  0.4  -> partiellement lies
  0.1  -> sans rapport ou contradictoires
```

---

## Etape 3 — La Matrice de Similarite

On calcule **toutes les similarites possibles** entre les chunks de A et les chunks de B :

```
         B1      B2      B3
    +----------------------------+
A1  |  0.95    0.21    0.18     |  A1 ressemble beaucoup a B1
A2  |  0.23    0.88    0.15     |  A2 ressemble beaucoup a B2
A3  |  0.19    0.22    0.91     |  A3 ressemble beaucoup a B3
    +----------------------------+
```

Cette matrice a N lignes (chunks de A) x M colonnes (chunks de B).

---

## Etape 4 — L'Algorithme Hongrois : l'appariement optimal

C'est **la piece maitresse** de SDE. On cherche le meilleur appariement global, pas juste le plus proche localement.

### Greedy vs Optimal — pourquoi ca compte

```
Matrice de similarite :
         B1      B2
    +----------------+
A1  |  0.95    0.70  |
A2  |  0.90    0.80  |
    +----------------+

Approche greedy (naive) :
  A1 -> B1 (0.95, le max de la ligne A1)
  A2 -> B2 (0.80, seul restant)
  Total = 1.75

Algorithme Hongrois (optimal) :
  A1 -> B2 (0.70)
  A2 -> B1 (0.90)
  Total = 1.60

Ici le greedy gagne, mais sur de vraies matrices plus complexes,
l'hongrois garantit le maximum global dans *tous* les cas.
```

### Chunks sans correspondance

Les chunks trop dissimilaires (score < seuil d'alignement) sont marques :

```
+----------+     pas de correspondance      +----------+
| Chunk A3 |  --------------------------->  |  removed |
+----------+                               +----------+

             nouvelle clause dans B seule
+----------+  <---------------------------  +----------+
|  added   |                               | Chunk B4 |
+----------+                               +----------+
```

---

## Etape 5 — Le Scorer : classifier avec des seuils par domaine

Chaque paire alignee recoit un **verdict** selon des seuils calibres par domaine :

```
score >= identical_threshold    ->  [identical]      meme sens
score >= shift_threshold        ->  [semantic_shift] sens derive
score <  contradiction_threshold -> [contradiction]  sens inverse
```

### Pourquoi des seuils differents par domaine ?

```
Un score de 0.88 signifie...

  Domaine default  ->  [identical]      assez proche
  Domaine legal    ->  [semantic_shift] trop loin pour du droit !
  Domaine medical  ->  [semantic_shift] un dosage peut avoir change
```

En droit, "doit livrer sous 30 jours" vs "doit livrer sous 31 jours"
peut avoir un impact juridique majeur alors que la similarite sera ~0.97.
D'ou un seuil `identical` a 0.96 pour le legal (vs 0.92 en default).

```
+----------+-----------+---------+-----------------+
| Domaine  | identical | shift   | contradiction   |
+----------+-----------+---------+-----------------+
| default  |   >= 0.92 | >= 0.75 |     < 0.40      |
| legal    |   >= 0.96 | >= 0.85 |     < 0.50      |
| medical  |   >= 0.95 | >= 0.82 |     < 0.45      |
| code     |   >= 0.90 | >= 0.70 |     < 0.35      |
| journalism| >= 0.91  | >= 0.72 |     < 0.38      |
+----------+-----------+---------+-----------------+
```

---

## Etape 6 — L'Explainer : pourquoi ca a change ?

Quand `explain=True`, SDE genere une explication courte **sans appel LLM**, par heuristiques linguistiques :

```
Regle 1 — Modal shift
  "shall / must" (fort) -> "may / can" (faible)
  -> "Une obligation ferme devient conditionnelle."

Regle 2 — Negation
  "shall not subcontract" -> "may subcontract"
  -> "Une negation est supprimee."

Regle 3 — Quantite precise -> vague
  "30 days" -> "reasonable timeframe"
  -> "Un delai precis ('30 days') devient flou."

Regle 4 — Changement de valeur numerique
  "10mg" -> "100mg"
  -> "La quantite change : '10mg' -> '100mg'."
```

**Avantages** : rapide, deterministe, 100% offline, pas de cout API.

---

## Metriques globales

```
global_score = moyenne des scores des paires alignees
             = (0.72 + 0.65 + 0.91) / 3 = 0.76

delta_index  = fraction des chunks qui ont change de sens
             = chunks(shift + contradiction + added + removed)
               ------------------------------------------------
                              total chunks
             = 2/3 = 0.67  -> 67% du contenu a derive
```

**Verdict global** :

```
global_score >= identical_threshold  ET  delta < 10%  ->  identical
global_score <  contradiction_threshold               ->  contradiction
sinon                                                 ->  semantic_shift
```
