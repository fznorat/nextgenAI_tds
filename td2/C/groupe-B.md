# TD 2 — Relecture croisée : le binôme C relit le binôme B (étape 2, le faux consensus)

Relecteurs : binôme C. Séance du 18 novembre 2026.
Objet relu : [`../B/README.md`](../B/README.md),
[`../B/scripts/pair_b_wrong_consensus.py`](../B/scripts/pair_b_wrong_consensus.py),
[`../B/scripts/delta_c10.sql`](../B/scripts/delta_c10.sql),
[`../B/scripts/check_c10.sql`](../B/scripts/check_c10.sql) et
[`../B/outputs/wrong-consensus/pair_b_output.txt`](../B/outputs/wrong-consensus/pair_b_output.txt).

## 1. Ce que nous avons revérifié

| Vérification | Résultat |
|---|---|
| Relance de la partie « scan » du script sur `traces-td1.csv` | Les mêmes 4 valeurs fausses partagées (C02, C08, C10, C15), avec les mêmes votes 2-sur-3 et 3-sur-5. C'est cohérent avec le tableau du binôme A et avec notre `quorum-by-family-td1.csv`. |
| Cellules C10 dans les traces | Une seule ligne par modèle, sans nouvelle tentative : « attempt 1 » est exact. |
| Arithmétique du delta | 150260 + 150240 + 118740 + 20330 = **439570** ; 17 + 20 + 18 + 4 = **59 lignes** ; 119410 + 439570 = **558980** = référence. ✔ |
| Exemple C007 (né le 2000-11-30, commande du 2026-01-20) | Différence d'années de 26, anniversaire non atteint, donc 25 ans révolus. ✔ |
| Lecture des trois SQL fautives de C10 dans les traces | Diagnostic confirmé : Cohere et Dots ne testent que le cas (a), et la seconde branche de Qwen (`= 24`, anniversaire non atteint) décrit un client de 23 ans. |
| Partie SQL du script (rejeu, delta, contrôle Python) | **Non relancée par nous** : `boutique.sqlite` n'est pas dans le dépôt (normal, il est dans le kit). Nous avons vérifié la logique des requêtes et les sommes, pas leur exécution. |

## 2. Points forts

- Le diagnostic est posé au bon niveau : trois syntaxes différentes, trois fournisseurs, **une seule
  lacune logique**. C'est exactement le mécanisme du cours 2, montré sur des données réelles.
- Le delta est fait dans les deux sens : lignes manquées (439570) *et* lignes ajoutées à tort (0).
  On peut ainsi affirmer que l'erreur est une pure omission.
- Le contrôle Python ne réutilise pas la fenêtre SQL : c'est un vrai calcul indépendant.
- Les votes ont été recalculés avec le code du binôme A (8 sur 8 identiques), ce qui valide aussi
  l'étape 1.

## 3. Remarques, par ordre d'importance

1. **Les trois autres consensus faux (C02, C08, C15) ne sont pas de même nature que C10, et c'est
   l'enseignement qui manque.** En relisant les SQL des traces, on voit que dans chacun de ces cas,
   les deux modèles d'accord ont des bugs *différents*. Ces bugs ont un point commun : leur filtre
   ne retient aucune ligne, et `COALESCE(SUM(...), 0)` transforme tout filtre vide en 0.
   - **C02** : 20b cherche les naissances entre le 2025-09-25 et le 2026-09-25, soit une fenêtre
     d'âge 0. Dots exige à la fois jour-mois ≤ 09-25 et jour-mois > 09-25, ce qui est impossible.
   - **C08** : Cohere compare `année(naissance) − 2026`, une valeur négative, à 0 ou 1. Dots a une
     condition jour-mois contradictoire (`<= '09-24' AND > '09-24'`), qui se réduit donc à
     « né un 24 septembre », et ne garde que les naissances postérieures au 2001-09-24, soit des
     clients de moins de 25 ans.
   - **C15** : Qwen exige à la fois jour-mois ≤ 09-25 et > 09-25, et n'a même pas de condition sur
     l'année. Les deux branches de Cohere sont contradictoires.

   **0 est donc une valeur « attracteur »** : deux erreurs *indépendantes* tombent sur la même
   valeur sans partager de logique. La phrase de la section 7, « a quorum only protects against
   independent errors », est donc incomplète : sur C15, les erreurs sont bien indépendantes, et le
   2-sur-3 retient quand même 0. Nous proposons d'ajouter au tableau de la section 1 une colonne
   « nature de l'accord » : *logique partagée* (C10) ou *convergence sur 0 par filtre vide* (C02,
   C08, C15).

   Conséquence pratique pour la règle (étape 3) : on ne peut pas écarter 0, puisque C06 et C14
   valent vraiment 0. En revanche, un 0 peut déclencher un contrôle bon marché, par exemple
   `COUNT(*)` du filtre sans la clause d'âge, ou l'exécution du contrôle `reference`.

2. **Le mécanisme de C10 réapparaît sur C15 chez Dots.** Sur C15, Dots renvoie 138920 avec
   « différence d'années = 25 et anniversaire ≤ 25 septembre ». C'est la même omission du cas (b) :
   il manque les clients nés entre le 2000-09-26 et le 2000-12-31, encore âgés de 25 ans au
   2026-09-25. Le trou du cas (b) est donc systématique chez Dots, pas accidentel. *Hypothèse à
   vérifier sur la base* : l'écart 168680 − 138920 = 29760 centimes devrait venir des commandes de
   mars à mai 2026 de C005 (né le 2000-09-26) et de C007 (né le 2000-11-30), qui sont déjà dans le
   delta de C10. Une requête delta de cinq lignes suffit à le confirmer.

3. **Le delta repose sur une condition « canonique », pas sur les trois requêtes réelles.**
   `FAULTY_WHERE` est une réécriture. Les trois requêtes fautives donnent la même *somme* (119410),
   mais cela ne prouve pas qu'elles retiennent les mêmes *lignes*. Pour le prouver, il faut
   exécuter chaque `WHERE` réel de la trace en sélectionnant les lignes de commande, puis vérifier
   que les `EXCEPT` dans les deux sens sont vides par rapport à `FAULTY_WHERE`.

4. **Reproductibilité.** `--db` est obligatoire, si bien que même le scan et la comparaison avec le
   binôme A, qui n'ont besoin que des CSV, ne tournent pas sans la base : le script plante après le
   scan. Nous proposons de rendre `--db` optionnel (et de sauter la partie SQL avec un message), et
   d'indiquer dans la sortie la version du kit qui fournit `boutique.sqlite`.

5. **Le jeu de tests aux bornes (section 7) est proposé mais pas exécuté.** Il serait facile à
   construire sur le modèle de DEMO-VOTE : une table en mémoire avec quelques clients fictifs
   (anniversaire la veille, le jour même et le lendemain de la date ; différence d'années de 25
   contre 26 ; un né le 29 février), sur laquelle on exécute les cinq SQL de C10. La recommandation
   deviendrait une preuve, et ce jeu pourrait servir de contrôle déterministe peu coûteux dans
   notre règle. Il doit être étiqueté « constructed », comme DEMO-VOTE.

## 4. Questions que nous posons au binôme B (préparation du quiz)

- Pourquoi passer de 3 à 5 modèles *aggrave*-t-il C10 ? (Le modèle ajouté, Dots, partage la même
  lacune : on ajoute une voix fausse, pas une voix indépendante.)
- Pourquoi 0 est-il dangereux dans un vote, et pourquoi ne peut-on pas simplement l'exclure ?
  (C'est la sortie de tout filtre vide, mais C06 et C14 valent réellement 0.)
- Écrire de mémoire la fenêtre « 25 ans révolus à la date D » :
  `birth_date > date(D, '-26 years') AND birth_date <= date(D, '-25 years')`.

## 5. Avis

Étape 2 solide : la cause SQL de C10 est démontrée au centime près, dans les deux sens, avec un
contrôle indépendant. Pour la rendre complète, il faut distinguer les deux natures de faux
consensus (remarque 1), ce qui demande une colonne et un paragraphe. La remarque 2 est un bonus
rapide qui renforce la thèse. Les remarques 3 à 5 sont des améliorations de rigueur.
