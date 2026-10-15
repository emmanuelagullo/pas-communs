# Pas communs — #SOC1

**Pas communs**, le socle technique de Petits Pas et de Pas à Pas — Accompagnement.

Projet de composants communs à **Petits Pas** et **Pas à Pas — Accompagnement**.
Ce dépôt ouvre le chantier ; il ne fournit encore aucune bibliothèque à installer.
Les deux applications restent indépendantes. La première extraction est #SOC2.

Le cadrage est fondé sur Petits Pas `main`, commit
`7b259d4ca20d20bd25cc05190cbcbd536370c1a8` (miroir GitHub).
Aucun changement de Petits Pas n'est nécessaire pour #SOC1.

- [Contrats et limites](CONTRATS.md)
- [Jalons et mode de contribution](JALONS.md)
- [Consignes des agents](AGENTS.md)

## Pourquoi pas de bibliothèque vide ?

Le premier consommateur CHRS démarre avec Django et ses propres migrations.
Il permet de confronter les extractions à un second usage réel. Nous ne créons
ni moteur de plugins, ni modèles universels, ni copie de Petits Pas.
Le futur module Python portera le nom `pas_communs`.
Une bibliothèque versionnée apparaîtra avec le premier composant effectivement
extrait, ses tests et son adoption par les deux applications.

## Organisation

Trois dépôts voisins sont pratiques en développement :

```text
petits-pas/
pas-communs/
pas-a-pas-accompagnement/
```

Ce ne sont pas des sous-modules. Les emplacements ci-dessus sont une convention
de travail, pas des dépendances d'exécution. Les publications épingleront une
version précise du futur paquet commun ; pas de dépendance à une branche mobile.

Code et documentation de ce nouveau dépôt : AGPL-3.0-or-later, voir LICENSE.
