# TD 2 — Relecture croisée : le binôme C relit le binôme A (étape 1, vote k-sur-n)

Relecteurs : binôme C. Séance du 18 novembre 2026.
Objet relu : [`../A/README.md`](../A/README.md), `Orchestrateur.vote_k_sur_n` dans
[`../A/scripts/skeleton-multi-llm-en.py`](../A/scripts/skeleton-multi-llm-en.py),
[`../A/scripts/step1_table.py`](../A/scripts/step1_table.py),
[`../A/analysis/csv/step1-table.csv`](../A/analysis/csv/step1-table.csv) et
[`../A/outputs/vote/votes-20-questions-2of3.jsonl`](../A/outputs/vote/votes-20-questions-2of3.jsonl).

Déclaration : relecture préparée avec l'aide de Claude ; les commandes ci-dessous ont été relancées
par le binôme C.

## 1. Ce que nous avons revérifié

| Vérification | Résultat |
|---|---|
| Relance de `step1_table.py` sur `traces-td1.csv` et `reference-td1.csv` | CSV **identique** au fichier commité (hors fins de ligne). Totaux retrouvés : 2-sur-3 = 16 justes / 2 faux (C10, C15) / 2 abstentions ; 3-sur-5 = 16 / 1 (C10) / 3. Décisions qui changent : C02, C15, C19. |
| `votes-20-questions-2of3.jsonl` contre la colonne 2-sur-3 du tableau | 20 lignes, **0 écart** (valeur et nombre de voix). |
| Tableau A contre notre `quorum-by-family-td1.csv`, implémenté indépendamment | **0 écart** sur les 40 décisions (décision, valeur, voix). |
| Lecture de `vote_k_sur_n` contre les 5 points du contrat | Conforme : contrôle `n // 2 < k <= n`, refus des doublons, y compris pour un membre en erreur, seuls les `executed` avec `value is not None` votent, et l'abstention renvoie le plus grand nombre de voix sans inventer de valeur. Comme k est une majorité stricte, une seule valeur peut atteindre k, donc renvoyer la première trouvée est sûr. |

Commande de relance :

```powershell
python td2/A/scripts/step1_table.py --traces td1/data/traces/traces-td1.csv --reference td1/data/references/reference-td1.csv --skeleton td2/A/scripts/skeleton-multi-llm-en.py --out step1-relance.csv
```

## 2. Points forts

- Le cas `0` est bien traité (`is not None`, et non un test de vérité). C'est indispensable ici, car
  les références de C06 et C14 valent 0 : un vote qui ignorerait 0 se tromperait sur deux questions.
- Les trois décisions qui changent (C02, C15, C19) sont expliquées cellule par cellule, avec la cause
  de chaque vote manquant (`sql_invalid` sur C02, `sql_rejected` sur C12, égalité exacte sur C19).
- Le paragraphe sur les marges qui changent sans changer la décision (C08, C09, C11, C12, C10, C17)
  est une vraie valeur ajoutée : il montre où chaque configuration est fragile.
- La lecture finale reste prudente (« batch-specific observation only »).

## 3. Remarques, par ordre d'importance

1. **Les tests annoncés ne sont pas dans le dépôt.** Le README liste des tests (k = 1 sur 3,
   k = 4 sur 3, k = 2 sur 4, doublon, panel vide, partage 2–2 avec un membre indisponible,
   `[0, 0, 3]`) « all as expected », mais `A/scripts/` ne contient aucun fichier de test ni aucun
   `assert`. Un lecteur ne peut donc pas les rejouer. À faire : committer un `test_vote.py` d'une
   vingtaine de lignes, ou au minimum sa sortie.

2. **C02 en 2-sur-3 est juste, mais sans aucune marge.** Cohere est `sql_invalid` : il reste dans n
   et ne vote pas, donc le panel fonctionne en pratique comme un 2-sur-2. La moindre panne
   supplémentaire (un HTTP 429, par exemple, fréquent sur qwen au TD 1) aurait donné une
   abstention. Nous proposons d'ajouter une colonne « votants effectifs / n » au tableau : elle
   montre d'un coup d'œil les décisions prises à la limite. En 2-sur-3, C02 et C12 n'ont que 2
   votants sur 3, et C08, C09 et C11 ne passent qu'avec exactement k = 2 voix.

3. **La « dernière tentative » dépend de l'ordre du fichier.** `step1_table.py` garde la dernière
   ligne lue pour chaque (fournisseur, modèle, question). C'est juste aujourd'hui : les 6 cellules
   relancées (C19 sur 20b, C16, C17, C18, C19 et C20 sur qwen) ont bien leur tentative 2 après la
   tentative 1, en ordre chronologique. Mais un tri ou une fusion du CSV casserait ce calcul sans
   message d'erreur. Il vaut mieux prendre le maximum de la colonne `attempts`. De même, le script
   ne filtre pas `nature == "real"`, contrairement à `atelier-vote.py` et au script du binôme B.
   Les 106 lignes sont `real` aujourd'hui, mais le README affirme ce filtre, donc il faut l'écrire.

4. **C17 mérite une phrase.** La bonne valeur 258180 est en tête (2 voix en 3-sur-5), mais le vote
   s'abstient. C'est le coût de l'abstention : pas de réponse fausse, mais pas de réponse du tout.
   Dans notre règle (section 3.8 du rapport), C17 fait partie des trois questions où aucune
   configuration ne répond juste. Un renvoi vers cette section relierait l'étape 1 à l'étape 3.

5. **Le choix du panel fixe n'est pas justifié.** Le panel A, C, D est celui de `atelier-vote.py`,
   alors il faut le dire. Il faut aussi noter que le seul panel 2-sur-3 juste sur C10 contiendrait
   120b et 20b, c'est-à-dire deux modèles de la même famille, ce que le cours 2 déconseille (voir la
   section 2 du binôme B et la section 3.2 de notre rapport).

6. **Forme.** Le nom du second membre manque encore (« add the second member here »). Les `open()`
   de `step1_table.py` n'ont pas `encoding="utf-8"` : ce n'est pas un bug aujourd'hui (les traces
   sont en ASCII pur, ce que nous avons vérifié), mais c'est un piège sous PowerShell, dont
   l'encodage par défaut est cp1252.

## 4. Questions que nous posons au binôme A (préparation du quiz)

- Pourquoi k doit-il être une majorité stricte ? (Pour que deux valeurs différentes ne puissent pas
  atteindre k en même temps.)
- Pourquoi un membre indisponible reste-t-il dans n ? (Sinon, un 3-sur-5 avec trois pannes
  deviendrait en silence une décision prise par deux modèles.)
- Sur C10, que déciderait le 3-sur-5 si Dots avait été indisponible ? (120b et 20b donnent 558980,
  Cohere et Qwen donnent 119410 : 2 voix contre 2, donc abstention. Une panne aurait rendu le vote
  *plus sûr*, ce qui montre que le nombre de votants ne mesure pas la fiabilité.)

## 5. Avis

Étape 1 complète, conforme au contrat et reproductible : 0 écart avec notre implémentation
indépendante. Avant le rendu, il faut committer les tests (remarque 1), ajouter le second nom et
appliquer les deux corrections de robustesse de la remarque 3.
