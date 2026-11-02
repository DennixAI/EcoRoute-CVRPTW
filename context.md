# EcoRoute-CVRP — Complete Project Context, Assignment, Decisions, Resources & History

> **Purpose:** long-form context handoff for the GitHub repository `EcoRoute-CVRP`. This file is designed so that a future teammate, contributor, or AI assistant can resume the project without relying on conversational memory.
>
> **Language policy:** communicate, document, and explain in **English**. The **original French assignment is included in French intentionally**, as a primary source; it must not be silently translated or altered.
>
> **Snapshot date:** 2026-11-02 (conversation context). **Scope of capture:** information visible in this project conversation, the supplied CESI assignment, user instructions, previous assistant deliverable descriptions, and the prior reported notebook-development transcript. **This file cannot assert access to missing messages, files, or source materials that were not visible in the available conversation.**
>
> **Source precedence:** (1) original assignment; (2) explicit, later user decisions for the chosen implementation; (3) tutor feedback when obtained; (4) prior assistant recommendations, which are not binding decisions. Any contradiction must be recorded, not concealed.

## Contents

1. [Complete inventory of known project context](#1-complete-inventory-of-known-project-context)
2. [Project identity and executive context](#2-project-identity-and-executive-context)
3. [French assignment transcription, substantially unabridged](#3-french-assignment-transcription-substantially-unabridged)
4. [Official requirements extracted from the assignment](#4-official-requirements-extracted-from-the-assignment)
5. [Confirmed decisions vs proposals vs unresolved questions](#5-confirmed-decisions-vs-proposals-vs-unresolved-questions)
6. [CVRP modeling: sets, parameters, objective and full ILP](#6-cvrp-modeling-sets-parameters-objective-and-full-ilp)
7. [Parameterization contract: no hard-coded instance values](#7-parameterization-contract-no-hard-coded-instance-values)
8. [Synthetic inputs, VRPLIB and benchmarking conventions](#8-synthetic-inputs-vrplib-and-benchmarking-conventions)
9. [What has been implemented and what has not](#9-what-has-been-implemented-and-what-has-not)
10. [Detailed end-to-end project roadmap](#10-detailed-end-to-end-project-roadmap)
11. [Performance evaluation and statistical protocol](#11-performance-evaluation-and-statistical-protocol)
12. [Architecture, reproducibility, testing and team work](#12-architecture-reproducibility-testing-and-team-work)
13. [Academic and technical references, including all user-given URLs](#13-academic-and-technical-references-including-all-user-given-urls)
14. [Chronological user prompts and explicit instructions](#14-chronological-user-prompts-and-explicit-instructions)
15. [Assistant decisions, suggested approach and corrections](#15-assistant-decisions-suggested-approach-and-corrections)
16. [Open questions, risks, limitations and next action](#16-open-questions-risks-limitations-and-next-action)
17. [Artifact manifest and provenance/verification status](#17-artifact-manifest-and-provenanceverification-status)
18. [2026-11-02 forensic review and correction log](#18-2026-11-02-forensic-review-and-correction-log)

---

## 1. Complete inventory of known project context

This is an inventory; the following sections contain the full details. **User requirements** and **suggestions** are distinguished throughout. The related project-history excerpt also contains earlier user instructions emphasizing algorithm quality and exhaustive review; those are transcribed in Section 14.

- **Identity:** `EcoRoute-CVRP`; descriptive name “EcoRoute — Intelligent Delivery Route Optimization”; CesiCDP; ADEME project; CESI Algorithmics and Optimization 2026–27; four-person team; environmental mobility and urban logistics context.
- **Original material:** long French environmental/assignment introduction; original basic and advanced problem descriptions; organization; first-check modeling rules; final deliverable; oral defense; evaluation criteria; both CESI links and the GitHub VRPLIB link supplied by the user.
- **Original broader domain:** minimize delivery tour duration on a road network taking time-varying traffic into account; this is broader than a static CVRP. The user subsequently chose CVRP only with static **distance** as primary benchmark-aligned objective.
- **Chosen problem:** **Capacitated Vehicle Routing Problem (CVRP, Level B)**, not CVRPTW or time-dependent VRP for the current scope. All customers serviced exactly once by a fleet of identical-capacity trucks, starting and ending at one depot, with payload limitations and no disconnected tours.
- **Math:** sets $V,C,F,A$; data $n,K,Q,q_i,d_{ij}$; arc variables $x_{ijk}$; assignment variables $y_{ik}$; active-truck variables $z_k$; order variables $u_{ik}$; minimize total distance; coverage, flow, depot, capacity, MTZ, domain and self-loop rules; optional symmetry breaking; TSP reduction; decision NP-completeness vs optimization NP-hardness; model sufficiency/necessity.
- **Configurable inputs:** customer count, depot/index mapping, fleet upper bound, shared vehicle capacity, per-customer demand, coordinates, graph, distances and rounding, synthetic generation distribution, seeds, benchmark paths/fleet override, and future solver, experiment and plot parameters. *Rules remain fixed even when data vary.*
- **Data:** synthetic examples plus actual VRPLIB benchmarks; `vrplib` library; `A-n32-k5` illustrative instance (31 customers + 1 depot, published **minimum number of vehicles** 5, capacity 100, proven optimum 784); avoid comparing unrounded costs with rounded reference costs; preserve original source IDs.
- **First notebook:** previous assistant reported an executable 68-cell notebook (39 Markdown, 29 Python code), 19 plotted figures, detailed equations, proof, synthetic generator, sample data, reference-route validation, explicit constraint-equation certification, sensitivity analysis; **no optimization solver**. Tutor approval has **not** been reported.
- **User-specified presentation:** extensive plots, high-detail code comments, extensive story-driven English explanations, notebook format `.ipynb`, academic literature, source links, clear assumptions, parameterized rather than hard-coded modeling.
- **Later code:** build and test initial solution construction, local search, and a metaheuristic, **with ALNS only a recommended candidate**, not yet committed or implemented; scale to realistic hundreds/thousands of customers; optimize code performance; **critically compare multiple competitive algorithms/baselines rather than assuming the first approach is good** (explicit user priority).
- **Experiments:** minimum 20 *different* instances across scenarios; compare to optimal/BKS where available; cost, runtime, feasibility, gap, statistical robustness, standard deviations, sensitivity to capacity/size/distribution/parameters, limitations and interpretations; warning that gaps above roughly 7–10% cap grade at B as stated by the assignment.
- **Deliverables:** mathematical modeling, algorithm design and implementation, experimental study, presentation in English, consolidated final notebook; first check during Prosit 3, final notebook before defense, presentation on final day of block; ADEME “July 12 next” in undated original brief (year not unambiguously stated).
- **Team/repository:** four-member division of responsibility was proposed; `EcoRoute-CVRP` was **suggested by the assistant after the user requested a GitHub-suitable name**, but the user did not explicitly ratify it; **GitHub repository creation is not established**. Previous deliverable filenames are recorded but their bytes are not currently available for inspection in this session.
- **History:** earlier project conversation excerpts (quality and exhaustive-review requirements), original French brief; subsequent English-only instruction; questions about ILP meaning; model + Python request; full checklist and configurability request; request for a large illustrated notebook and clarification; final detailed notebook specification; progress explanations; repository name selection; current context compilation request. Exact wording is retained in Section 14.
- **Unknowns:** exactly $K$ versus at most $K$ active vehicles, tutor approval, whether the distance-objective deviation needs formal tutor consent, final benchmark inventory, exact defense dates, final ALNS/other algorithm choice, software runtime limits and hardware, benchmark fleet metadata for all data, dataset license and provenance, actual GitHub remote URL.

---

## 2. Project identity and executive context

| Item | Recorded value / state | Authority |
|---|---|---|
| Repository name | **`EcoRoute-CVRP`**, working proposal | User asked for a GitHub-suitable name and assistant proposed this one; there is no explicit user acceptance or repository creation record |
| Project title | **EcoRoute — Intelligent Delivery Route Optimization** | Assistant-proposed title |
| Short technical subtitle | Mathematical Modeling and Optimization of the Capacitated Vehicle Routing Problem (CVRP) | Assistant-proposed subtitle |
| Original organization | **CesiCDP** | French brief |
| Funding/stakeholder context | **ADEME**, interest in mobility demonstrators and new solutions | French brief |
| Academic setting | CESI / A3 Algorithmique et optimisation 2026–27 URL path | Provided assignment URL; cohort context implied by path |
| Team size | **4 people** | French brief |
| Intended application | Optimizing delivery vehicle routes | French brief + confirmed user choice |
| Original task objective | **Minimize total travel duration**, considering predicted traffic in different time slots | French brief |
| Current user-selected mathematical objective | **Minimize total traveled distance**, chosen for VRPLIB compatibility | Explicit later user prompt |
| Main problem | **CVRP / capacitated VRP (Level B)** | Explicit user prompt and assignment |
| Advanced alternative | CVRPTW with time windows and waiting, Level A | Original brief only; **outside current work** |
| Requested implementation language | Python | Brief + user |
| Delivery formats | Jupyter notebooks with explanation and code; final oral defense in English | Brief + user |
| First-modeling stage solver | **Not required and explicitly not to be implemented** | Brief + user |
| Final solver implementation | **Required** with metaheuristic and real-size tests | Brief |
| Proposed metaheuristic | ALNS, with other choices eligible | Prior assistant recommendation; **not a final user decision** |
| Current recorded state | Modeling notebook draft reported completed and executed; **awaits tutor review** | Prior assistant statements; artifact bytes not accessible in current session |
| Repository creation | Not established | No GitHub creation action in visible history |

### Environmental and business motivation

Since the 1990s, international and national action to reduce energy consumption and greenhouse gas emissions has highlighted transport as a high-impact sector. The original brief cites the 1997 Kyoto Protocol (in force in 2005), later emission reduction commitments, and the need for public authorities to influence behavior. CesiCDP is positioned as a mobility-research organization responding to an ADEME interest call; improving the efficiency of logistics is the project's demonstration use case. Potential relevant fields mentioned: postal distribution, product delivery, road network maintenance/treatment, waste collection.

### Scope distinction (critical for future AI assistants)

**DO NOT silently upgrade the model to CVRPTW or time-dependent CVRP.** The statement's initial narrative asks for traffic-aware tour-duration optimization, whereas the explicitly selected *current deliverable* is basic CVRP with distance objective and static costs. Both must be retained in the record. If the tutor later requires traffic-dependent travel times, that would be a separately specified extension; it is not already covered by the existing distance-based ILP or benchmark.

---

## 3. French assignment transcription, substantially unabridged

> **Provenance:** this is a near-verbatim transcription of the original user-supplied French brief, preserving the substantive wording, links, unusual HTML entity strings and irregular Markdown where visible. It has **not** been byte-for-byte compared against an export of the original chat or the live CESI webpage. Whitespace, non-breaking spaces and line wrapping may differ. Consult the original source link for official changes. English interpretation does **not** replace this primary source.

```text
Depuis les années 90, il y a eu une véritable prise de conscience mondiale de la nécessité de réduire la consommation d'énergie et des émissions de gaz à effet de serre. Les premiers engagements sont apparus lors de la signature du protocole de Kyoto en 1997. Mais son entrée en vigueur n'a finalement eu lieu qu'en 2005 et de nombreux scientifiques ont jugé les efforts insuffisants pour ralentir le réchauffement climatique. Depuis, d'autres engagements plus ambitieux ont vu le jour (division par 4 des émissions d'ici 2050 pour la France par exemple, engagements de certaines grandes villes comme Paris). Mais la tâche est compliquée. Les pouvoirs publics et les collectivités territoriales n'ont pas la possibilité d'obliger les entreprises et les particuliers à changer leurs habitudes pour atteindre ces objectifs. L'action se porte donc avant tout à faire évoluer les comportements. L'économie et le recyclage des matières premières, l'amélioration des modes de transport et des performances énergétiques des bâtiments doivent devenir des priorités.\
\
&#x20;DESCRIPTION

L’ADEME (Agence de l’Environnement et de la Maîtrise de l’Energie) a récemment lancé un appel à manifestation d’intérêt pour promouvoir la réalisation de démonstrateurs et d’expérimentations de nouvelles solutions de mobilité pour les personnes et les marchandises adaptées à différents types de territoires.

Votre structure CesiCDP est déjà bien implantée dans le domaine. Aidé de nombreux partenaires, vous avez réalisé plusieurs études sur le thème de la Mobilité Multimodale Intelligente. Les nouvelles technologies de transport, plus économiques et moins polluantes ne sont pas sans poser de nouveaux défis notamment d’un point de vue de l’optimisation de la gestion des ressources. Mais ces problèmes de logistique du transport présentent un enjeu majeur pour l’avenir : ces applications sont nombreuses (distribution du courrier, livraison de produits, traitement du réseau routier, ramassage des ordures) et leur impact sur l’environnement peut être véritablement significatif.

Vous faites partie de l’équipe (4 personnes) mise en place par CesiCDP pour répondre à l’appel de l’ADEME. L’enjeu est d’obtenir de nouveaux marchés avec des financements très intéressants pour continuer à développer votre activité.

CesiCDP a décidé d’orienter son étude sur la gestion de tournées de livraison. Le problème algorithmique consiste à calculer sur un réseau routier une tournée permettant de relier entre elles un sous-ensemble de clients, puis de revenir à son point de départ, de manière à minimiser la durée totale de la tournée. Cette optimisation devra tenir compte du trafic prévu sur chaque axe pour les différentes tranches horaires.

L’idée est de proposer une méthode issue de la Recherche Opérationnelle pour générer une tournée de livraison correspondant à ce problème.

Le périmètre reste encore à préciser. Vous avez décrit une version de base du problème. Mais, afin de le rendre plus réaliste et retenir toute l’attention de l’ADEME, vous hésitez à ajouter des contraintes supplémentaires. Il faut s’attendre à ce qu’il soit ainsi plus dur à traiter.



- ***Version de base***
  - Le choix du modèle et le code en Python capable de résoudre des instances de taille importante (plusieurs milliers de villes)
  - Une étude statistique du comportement expérimental de l'algorithme
  * Une flotte de k camions de capacité identique
- **Version avancée**

  Fenêtre de temps de livraison pour chaque objet
  - Interdiction de livrer hors de la fenêtre
  - Possibilité d'attendre sur place l'ouverture de la fenêtre temporelle ORGANISATION

    L’échéance pour le dépôt des projets auprès de l’ADEME est fixée au 12 juillet prochain. Afin de tenir les délais et de préparer tous les rapports nécessaires, vous avez défini la feuille de route suivante :
    1. Modélisation formelle
    2. Conception algorithmique et implémentation
    3. Étude expérimentale
    4. Présentation du travail réalisé à votre équipe (en anglais) avant remise des livrables à l'ADEME
    Chacune de ces étapes aboutira à un livrable que vous présenterez à votre responsable pour suivi et échanges. Ces livrables prendront la forme d’un Notebook présentant à la fois la démarche et le code correspondant (lorsqu’une implémentation est requise). L'aspect story-telling doit être privilégié dans la rédaction de chacun de ces Notebook.

    Le code des différents livrables n'a pas à être au standard d'un code à industrialiser (pas besoin d'une grande modularité). Il doit en revanche rester lisible, commenté, et privilégier la performance. Il est fortement recommandé de suivre les recommandations PEP : [**Livrables attendus**](https://scenari.cesi.fr/scenari/cas/Diffusion_FISE_INFO_A3_Algorithmique_et_optimisation_26_27_ETU/_5_-_Projet.html#)
    - ***Livrable Modélisation (check)***

      **Échéance :** au cours du prosit 3

      **Évaluation :&#x20;**&#x4E;on

      **Objectif :&#x20;**&#x4D;odéliser le problème au travers d'un Notebook Jupyter.

      **Description :&#x20;**&#x43;e premier livrable présente le problème que vous traitez ainsi que son contexte, le reformule de manière formelle, et en étudie les propriétés théoriques, notamment de complexité.

      D’une part, vous devrez proposer une représentation formelle des données, du problème, et de l’objectif à optimiser (en intégrant les contraintes supplémentaires que vous décidez de traiter). Cette formalisation devra permettre d’identifier la structure du problème et de le relier à des problèmes classiques de la littérature, afin d’en établir la complexité théorique (par exemple via une réduction vers un problème NP-difficile ou NP-complet).

      Une première version de la modélisation mathématique sous forme de Programme Linéaire en Nombres Entiers (PLNE) est attendue. Celle-ci devra inclure :
      - les variables de décision,
      - la fonction objectif,
      - l’ensemble des contraintes (y compris spécifiques au problème traité).
      Cette modélisation doit être suffisamment précise et rigoureuse pour être implémentée par la suite, sans pour autant nécessiter d’implémentation à ce stade. Les méthodes de résolution ne sont pas à aborder lors de ce check. Vous aurez l'occasion de les étudier en détails dans les boucles suivantes.

      Le point est réalisé avec le tuteur de projet afin de valider :
      - la pertinence de la formalisation,
      - la validité de la preuve de complexité,
      - la cohérence du modèle PLNE,
      Les éléments pourront ainsi être modifiés avant d'être intégrés dans le livrable final du projet.

      Recommandation :

      Il est fortement recommandé d’intégrer à ce notebook des références bibliographiques vers des articles ou des ouvrages scientifiques.
    * **Livrable final du projet**

      **Échéance : la veille de la soutenance Objectif :** Présenter l’ensemble de la démarche réalisée, la réalisation technique, et conclure sur les résultats obtenus.

      **Description :**
      1. **Modélisation et méthodes de résolution** :

         Cette partie reprend et complète les éléments de modélisation formelle :
         - formalisation des données
         - preuve de complexité
         - modélisation mathématique sous forme de Programme Linéaire en Nombres Entiers (PLNE) complète et corrigée,
         - une présentation de l’utilisation éventuelle de cette approche exacte (résolution directe, benchmark, borne inférieure/supérieure, etc.),
          

         ainsi que :
         - la description de la méthode de résolution heuristique ou métaheuristique choisie,
         - sa formalisation adaptée au problème, incluant par exemple :
         - définition des solutions,
         - structure du voisinage (recherche locale, VNS, LNS, etc.),
         - opérateurs spécifiques (croisement, mutation, insertion, échange…),
         - mécanismes de guidage (ex : phéromones pour ACO, vitesses pour PSO, etc.).
      2. **Implémentation :**

         Cette partie décrit la réalisation technique de la métaheuristique, incluant :
         - le fonctionnement général de l’algorithme,
         - les différentes étapes (initialisation, itérations, critères d’arrêt…),
         - les mécanismes internes (ex : sélection, croisement et mutation pour un algorithme génétique, évaporation des phéromones pour ACO, opérateurs de voisinage pour recherche locale, etc.),
         * l’implémentation des cas de test,
         * une démonstration du fonctionnement sur plusieurs instances (sans nécessité d’exhaustivité).&#x20;
         1. **Étude expérimentale**

            Cette partie analyse les performances de la solution proposée. Elle devra :
            - définir un plan d’expérience structuré, incluant différents scénarios de test (par exemple : taille des instances, répartition géographique, contraintes spécifiques comme les fenêtres de temps, etc.),
            - présenter les résultats expérimentaux (tableaux, indicateurs de performance, comparaisons),
            - analyser le comportement de l’algorithme (qualité des solutions, temps de calcul, robustesse, sensibilité aux paramètres…),
            - identifier les limitations de l’approche,
            - proposer des axes d’amélioration justifiés sur la base des observations.
            - La méthodologie expérimentale, les analyses statistiques et les conclusions devront être argumentées de manière rigoureuse.
         - ***Soutenance***
           - **Échéance :** dernier jour du bloc
           * **Évaluation :** Oui
           * **Objectif :** Démontrer les capacités pour présenter oralement l'état d'avancement d'un projet dans un contexte professionnel
           * **Description :**
             - Elle doit être orientée résultats, avec démonstration de l’exécution du code (sur des cas suffisamment petits pour garder la présentation fluide) et présentation des résultats.

             - Il sera attendu une présentation de l'avancement du projet. Il est donc crucial de rappeler le contexte et les objectifs avant de mettre en valeur les réalisations et les résultats obtenus. Soyez transparents sur les défis rencontrés, mettez en évidence les étapes achevées, celles en cours et celles à venir (un planning/échéancier serait apprécié). [**Modalité**](https://scenari.cesi.fr/scenari/cas/Diffusion_FISE_INFO_A3_Algorithmique_et_optimisation_26_27_ETU/_5_-_Projet.html#)

               **Évaluation du projet (livrable final)**

               **Travail attendu :**

               1. **Modélisation et résolution**

                  Proposer :
                  - un modèle mathématique (PLNE)
                  - une métaheuristique (Recuit Simulé, Tabu Search, ALNS, etc.)
                  - Implémenter en Python un solveur capable de traiter des instances de taille réaliste
                  Livrable : code structuré et documenté (Notebook Jupyter ou script Python)
               2. **Analyse de performance**

                  Évaluer :
                  - la qualité des solutions
                  - le temps de calcul (fonction de la taille de l’instance)
                  - tester l’algorithme sur au moins 20 instances différentes issues de scénarios d’usages différents
                  - Produire des analyses expérimentales (visualisations, statistiques, etc.) permettant de comprendre le comportement de votre approche
                   
               3. **Validation sur instances de référence (VRPLIB)**
                  - Utilisation de la bibliothèque `vrplib` pour charger des instances de référence.
                  - Attendus :
                  - comparaison avec les meilleures solutions connues
                  - calcul du gap (%) défini par : gap = 100 x ((cout de votre solution - cout de la solution optimale) / cout de la solution optimale)
                  - analyse des résultats obtenus





               &#x20;**Choix du problème :**

               - **Niveau B (attendu)** : **CVRP** : véhicules avec capacité (identique pour tous les véhicules)
               - **Niveau A (avancé)** : **CVRPTW** : véhicules avec capacité + **fenêtres de temps**

               **Instances et analyse**

               Des instances sont fournies pour les deux problèmes.

               Les étudiants doivent :

               - tester leur algorithme sur un ensemble varié d’instances,
               - analyser les performances en fonction des caractéristiques des problèmes (sans nécessairement être exhaustif), par exemple :
               - taille des instances,
               - répartition des clients,
               - contraintes du problème (capacité, fenêtres de temps, etc.).

               L’objectif est de mettre en évidence le comportement de la méthod&#x65;**&#x20;**&#x73;elon différents scénarios.

               &#x20;**Critères d’évaluation**

               - Qualité des solutions (gap). Un gap supérieur à 7-10% entrainera une notation maximum de B
               - Temps de calcul
               - Qualité de l’analyse expérimentale
               - Pertinence des conclusions

               **Recommandations**

               Ne pas se limiter à présenter des résultats : les interpréter

               Identifier les forces et limites de votre approche

               Proposer des pistes d’amélioration tutos et exemples de validation ,  [https://github.com/PyVRP/VRPLIB](https://github.com/PyVRP/VRPLIB)
```

### Normalization notes for the original source

- The source contains encoded HTML-space/letter sequences such as `&#x20;`, `&#x4E;`, `&#x4D;`, `&#x43;`, `&#x65;`, `&#x73;`, irregular bullet indentation, and collapsed headings. These were visibly present in the user's pasted text and are retained as source artifacts where visible; they are not extra mathematical requirements.
- The label **“Évaluation : Non”** for modeling appears encoded as `&#x4E;on`; the original formatting should be checked on the live page if needed.
- The phrase **“12 juillet prochain”** supplies a day/month but not a definitive year relative to the date of the assignment. Do not invent the absolute deadline.
- The exact supplied assignment URLs are repeated in the original message and are listed separately below for navigability.

---

## 4. Official requirements extracted from the assignment

### 4.1 Basic version

- Choose a mathematical model and implement **Python code** able to handle substantial instances (the brief mentions *several thousand cities* as ambition).
- Perform a **statistical study of the algorithm's experimental behavior**.
- Use a fleet of $k$ trucks with **identical capacity**.
- Resolve a vehicle-routing optimization problem using Operations Research methods.

### 4.2 Advanced version — archived but currently excluded

- Delivery windows per object/customer.
- No service outside time window.
- Waiting allowed until time window opens.
- Named problem in evaluation section: **CVRPTW** (Level A), versus basic **CVRP** (Level B).
- Time-dependent predicted traffic is also mentioned in the wider introduction, but the brief's Level B/Level A distinction explicitly names CVRP/CVRPTW.

### 4.3 Project stages and checkpoints

1. **Formal mathematical modeling:** Jupyter notebook that introduces context and formalizes data/problem/objective; theoretical complexity; preliminary PLNE variables, objective, complete relevant constraints; no solving method and no solver implementation at this check. Review with tutor (formalization relevance, complexity proof, model coherence). Deadline: during **Prosit 3**; check not graded according to supplied text.
2. **Algorithm design and implementation:** choose an appropriate heuristic/metaheuristic; define solution representation, neighborhoods, operators, adaptive/guidance mechanism, initialization, iteration, stopping, and Python execution.
3. **Experimental study:** structured scenarios, tables, metrics, comparison, quality, runtime, robustness, sensitivity, statistical arguments, limitations and improvements.
4. **English team presentation:** professional explanation of context, objectives, progress and results, with a short live code demonstration and an honest schedule of completed/in-progress/remaining work.

Each stage yields a deliverable in **notebook** form showing reasoning and code where implementation is expected; prioritize **storytelling**. Code need not be industrial production code but should be readable, commented, reasonably performant, and follow PEP guidance.

### 4.4 Final deliverable

- **Due:** day before the defense.
- Include corrected full PLNE, proof of complexity, model data, possible use of exact ILP approach (direct solve, benchmark, bounds, or note if unused).
- Explain and formalize chosen metaheuristic and implement it in Python, with test cases and demonstrations.
- Test on **at least 20 distinct instances** across scenarios; not merely 20 random seeds of the same instance.
- Measure quality and execution time as a function of instance size, including feasibility and sensitivity.
- Use **`vrplib`** to load reference instances, compare with known solutions and compute gaps.
- Oral defense on last day of block; results-oriented, English, sufficiently small live demo; plan/schedule appreciated.

### 4.5 Gap formula and interpretation

Original formula in the brief:

$$\text{gap}(\%)=100\cdot\frac{\text{our cost}-\text{optimal cost}}{\text{optimal cost}}.$$

**Rigorous correction of terminology:** if the denominator is a *proven optimal cost*, this is an optimality gap. If the denominator is merely a **Best-Known Solution (BKS)**, call it “gap to BKS.” A solution can be equal to or better than a previously published BKS; therefore BKS gaps are **not the same** as mathematically certified optimality gaps. Reference costs, distance rounding, and feasibility conventions must align.

### 4.6 Evaluation emphases

- Solution quality, especially gap (brief warns that gap > about **7–10%** limits maximum grade to B).
- Computation time.
- Quality of experimental analysis, interpretation, and justified conclusions.
- Acknowledge strengths, weaknesses, and improvements.

---

## 5. Confirmed decisions vs proposals vs unresolved questions

| Topic | Status | Explanation |
|---|---|---|
| Language | **Explicitly confirmed** | User requested **English only** for responses/documentation (original assignment reproduced in French as evidence). |
| Current model | **Explicitly confirmed** | **CVRP only**, not advanced CVRPTW. |
| Main objective | **Explicitly confirmed** | **Total distance** for VRPLIB benchmark compatibility. Different from initial duration/traffic motivation. |
| Data selection | **Explicitly confirmed** | Both generated synthetic examples **and** VRPLIB benchmark instances. |
| Modeling code scope | **Explicitly confirmed** | Plotting, parsing, constraint illustrations, **feasibility checks**, **no optimization solver**. |
| Modeling deliverable | **Explicitly confirmed** | Detailed `.ipynb`, rigorous ILP/PLNE, all necessary constraints, MTZ, complexity proof, numerous plots, detailed comments, references, verified download. |
| Configurability | **Explicitly confirmed** | **No fixed instance values** baked into the mathematics or future algorithm; capacity/fleet/demand/locations/costs adjustable. |
| Project repository | **User requested a name; assistant proposed one** | `EcoRoute-CVRP` is the current working name, **not explicitly accepted**. Actual remote not created/verified. |
| Vehicle fleet semantics | **Open** | At most $K$ vs exactly $K$ active; existing model uses **at most $K$**. Tutor to validate. |
| Fleet capacities | **Confirmed by brief** | Identical capacities across all trucks within an instance, but $Q$ varies between instances. |
| One depot, visit exactly once, no split | **Model assumption consistent with standard CVRP** | Should still be confirmed with provided problem instance conventions. |
| Zero customer demand | **Model supports it** | Order-based MTZ works even for zero-demand customers. |
| Symmetric Euclidean graph | **Not a universal assumption** | General directed nonnegative cost matrix supported; plots may use Euclidean coordinates. |
| Time-dependent traffic | **Excluded from current model** | Remains documented from original business context. |
| Initial route constructor | **Candidate only** | Greedy insertion / Clarke–Wright Savings previously proposed. |
| Local search | **Candidate only** | 2-opt, relocate, swap, 2-opt*. |
| Metaheuristic | **Recommended, not finalized** | **ALNS** suggested. No algorithm implementation or benchmark performance established. |
| Final benchmarks | **Not selected** | Need minimum 20 diverse instances; one sample A-n32-k5 previously validated. |
| Hardware/time budgets | **Not set** | Needed for experimental fairness, reproducibility and scalability. |
| Tutor approval | **Not established** | Modeling draft reported completed; checkpoint approval still pending. |
| Year of “July 12” | **Unclear** | Do not assume a particular year without confirming current academic scheduling. |

---

## 6. CVRP modeling: sets, parameters, objective and full ILP

### 6.1 General graph and input data

- $C=\{1,2,\dots,n\}$ customers; $0$ depot; $V=C\cup\{0\}$.
- $F=\{1,\dots,K\}$ identical-capacity available trucks.
- $A=\{(i,j):i,j\in V,\ i\ne j\}$ potential directed arcs; complete graph for main ILP, possibly built from shortest paths on the road network.
- $q_i\ge0$ customer demand and $q_0=0$.
- $Q>0$ common truck capacity, **input** not a fixed universal number.
- $d_{ij}\ge0$ fixed distance/cost of driving from $i$ to $j$, **input**. Symmetry is not required.
- Optional $(a_i,b_i)$ customer/depot coordinates, for maps and possibly constructing Euclidean distances; cost matrix remains authoritative.
- $n,K,Q,q_i,d_{ij}$ are **instance parameters**; the ILP equations are unchanged across instances.

### 6.2 Decision variables

$$x_{ijk}\in\{0,1\}:\quad 1 \text{ iff truck } k \text{ uses arc } (i,j).$$
$$y_{ik}\in\{0,1\}:\quad 1 \text{ iff truck } k \text{ serves customer } i.$$
$$z_k\in\{0,1\}:\quad 1 \text{ iff truck } k \text{ is active}.$$
$$u_{ik}\ge0:\quad \text{auxiliary relative visit order for customer } i \text{ on truck } k.$$

**Classification note:** If $u_{ik}$ is continuous, technically this is a **Mixed-Integer Linear Program (MILP)**; setting $u_{ik}\in\mathbb{Z}_{\ge0}$ instead yields an **all-integer PLNE** with the same interpretation. The original conversation used both descriptions; a final report should consistently define its domain.

### 6.3 Objective

**Minimize total traveled distance over all trucks and selected arcs:**

$$\boxed{\min\sum_{k\in F}\sum_{(i,j)\in A}d_{ij}x_{ijk}}.$$

The later empirical comparison must use **the exact benchmark cost convention**. The objective is **not** currently minimizing fleet count, max route length, lateness, time-varying travel duration, or emissions directly.

### 6.4 Complete constraints (at most $K$ active trucks)

**Customer assignment (every customer exactly once):**

$$\boxed{\sum_{k\in F}y_{ik}=1\qquad\forall i\in C.} \tag{M1}$$

**Every assigned truck leaves its customer exactly once:**

$$\boxed{\sum_{j\in V\setminus\{i\}}x_{ijk}=y_{ik}\qquad\forall i\in C,\ k\in F.}\tag{M2}$$

**Every assigned truck enters its customer exactly once:**

$$\boxed{\sum_{j\in V\setminus\{i\}}x_{jik}=y_{ik}\qquad\forall i\in C,\ k\in F.}\tag{M3}$$

**Each active vehicle leaves depot once:**

$$\boxed{\sum_{j\in C}x_{0jk}=z_k\qquad\forall k\in F.}\tag{M4}$$

**Each active vehicle returns to depot once:**

$$\boxed{\sum_{i\in C}x_{i0k}=z_k\qquad\forall k\in F.}\tag{M5}$$

**Per-vehicle carrying capacity:**

$$\boxed{\sum_{i\in C}q_i y_{ik}\le Q z_k\qquad\forall k\in F.}\tag{M6}$$

**Auxiliary ordering variable bounds:**

$$\boxed{y_{ik}\le u_{ik}\le n y_{ik}\qquad\forall i\in C,\ k\in F.}\tag{M7}$$

**MTZ subtour elimination (valid with zero-demand customers):**

$$\boxed{u_{jk}\ge u_{ik}+1-(n+1)(1-x_{ijk})\qquad\forall i,j\in C,\ i\ne j,\ k\in F.}\tag{M8}$$

**Domains:** $x,y,z$ binary; $u\in\mathbb R_{\ge0}$ (or integer nonnegative). No self-loops $x_{iik}$ because $(i,i)\notin A$. 

**Optional symmetry reduction:** $z_k\ge z_{k+1}$ for identical truck indices, if desired; not needed for feasible-model completeness.

### 6.5 Interpretation and validity

- M1 + M2/M3 give one assignment, one arrival and one departure for every customer.
- M4/M5 ensure one depot-out and one depot-in per active truck, zero depot arcs for inactive trucks.
- M6 prevents overloading and links assigned demand to use. With zero-demand customers, M1–M5 and MTZ still enforce the correct route structure.
- M7/M8 exclude disconnected customer-only cycles: traversing each customer-to-customer selected arc must increase order by at least 1; a closed directed customer-only cycle would require a strict increase back to the start, impossible.
- With all core equations, every active truck's selected arcs form **one connected depot tour**. Every physically feasible no-split CVRP tour is expressible by these variables, and every feasible assignment encodes a valid plan.
- If assignment **must use exactly $K$ trucks**, impose $z_k=1$ for all $k$ and check that the instance permits $K$ nonempty tours; this is not currently assumed.
- Other subtour formulations are possible. This specific $n+1$ big-$M$ coefficient is linked to the order bounds ($u\in[0,n]$), not an arbitrary tunable optimization hyperparameter.

### 6.6 Complexity proof

Start with TSP on $n+1$ vertices with distances $d_{ij}$ and budget $B$. In polynomial time, construct CVRP with $0$ as depot, $K=1$, $q_i=1$ for $i\ge1$, and $Q=n$, preserving the original distance matrix. Its single truck can serve all $n$ customers. Feasible CVRP tours are exactly TSP Hamiltonian cycles with the same cost. Thus $\text{TSP}\le_p\text{CVRP}$. The **optimization** CVRP is NP-hard. The **decision** variant (is a feasible set of routes of cost $\le B$ available?) belongs to NP under standard finite integer/rational encoding, because a proposed route list can be verified in polynomial time. The decision problem is therefore NP-complete.

### 6.7 Necessary feasibility diagnostics (not sufficient)

$$\max_{i\in C}q_i\le Q,\qquad\sum_{i\in C}q_i\le KQ.$$

Aggregate lower bound on the number of vehicles: $\lceil\sum_iq_i/Q\rceil$. These conditions are **necessary**, not sufficient for unsplittable demand. Example: demands (6,6,6), $K=2$, $Q=10$. Total demand 18 $\le20$, but each vehicle can hold only one customer, so the instance is infeasible under two trucks.

### 6.8 Mathematical-model scaling

For the complete directed graph with $n$ customers and $K$ trucks:

- Arc binaries: $K(n+1)n$.
- Customer-assignment binaries: $Kn$.
- Vehicle activation binaries: $K$.
- Order auxiliaries: $Kn$.
- MTZ pairwise inequalities: $Kn(n-1)$.
- Total binary variables: $K(n+1)^2$.

Therefore this explicit three-index model has $\Theta(Kn^2)$ arc variables/MTZ inequalities. Mathematical correctness **does not imply** tractability on several-thousand-customer inputs with an exact solver; later heuristic/metaheuristic methods are required for scalability.

---

## 7. Parameterization contract: no hard-coded instance values

### 7.1 Principle

**Do not hard-code data values into the model/algorithm.** “$Q$ is shared across trucks” is a model rule; “$Q=100$” is only an input value for a specific benchmark. The final algorithm should accept multiple instance configurations without rewriting code. Hand-written small examples may of course use numerical demonstration values.

### 7.2 Input and configuration parameters

| Group | Parameter | Notation / coding field | Role | Source/status |
|---|---|---|---|---|
| Problem size | Customers | $n$ / `n_customers` | Number of non-depot nodes | From instance / synthetic configuration |
| Fleet | Available trucks | $K$ / `max_vehicles` | Upper bound on active routes | From metadata or explicit override |
| Capacity | Uniform vehicle capacity | $Q$ / `vehicle_capacity` | Limit per truck | Instance |
| Demand | Customer demands | $q_i$ / `demands` | Nonnegative per-customer delivery load | Instance |
| Geography | Depot location | `depot`, `depot_xy` | One configurable depot; internally reindex to 0 | Instance |
| Geography | Customer locations | `coordinates` | Spatial visualization or distance derivation | Instance/optional |
| Network | Allowed arcs | $A$ | Feasible stop-to-stop connections | Complete graph or derived network |
| Costs | Travel-distance matrix | $d_{ij}$ / `distances` | Primary objective costs | Instance |
| Costs | Rounding convention | `distance_policy` | Align VRPLIB costs with BKS | Benchmark-specific |
| IDs | Original node ID mapping | `original_ids` | Translate depot/customer labels to canonical indices | Parsing |
| Synthetic | Layout type | `layout` | Uniform vs clustered generation | Configuration |
| Synthetic | Demand bounds | `min_demand`, `max_demand` | Generated demand range | Configuration |
| Synthetic | Coordinate range | `coordinate_max` | Geometric data range | Configuration |
| Synthetic | RNG seed | `seed` | Repeatable generation | Configuration |
| Benchmark | VRP/SOL paths | `BENCHMARK_PATH`, `.sol` path | Local files | Configuration |
| Benchmark | Fleet override | `BENCHMARK_FLEET_OVERRIDE` | Explicit maximum fleet when omitted in file | Configuration |
| Algorithm (future) | Maximum iterations | `max_iterations` | Stopping budget | Not yet implemented |
| Algorithm (future) | Time limit | `time_limit_seconds` | Runtime budget | Not yet implemented |
| Algorithm (future) | Random state | `random_seed` | Reproducibility | Not yet implemented |
| Algorithm (future) | Candidate neighbors | `candidate_neighbors` | Local-search acceleration | Not yet implemented |
| Algorithm (future) | Removed customer fraction | `destroy_fraction` | ALNS perturbation strength | Candidate only |
| Algorithm (future) | Operator weights | e.g. `operator_weights` | Adaptive destroy/repair choice | Candidate only |
| Algorithm (future) | Acceptance settings | e.g. `initial_temperature`, `cooling_rate` | Simulated-annealing-type acceptance if chosen | Candidate only |
| Algorithm (future) | No-improvement patience | e.g. `max_stagnation` | Search stopping/restart | Candidate only |
| Experiments | Number of instances | $N_{\text{instances}}\ge20$ | Distinct dataset requirement | Required later |
| Experiments | Repeated runs | $R$ / `n_runs` | Mean, std, robustness | To decide |
| Experiments | Seeds | `run_seeds` | Reproducibility/fairness | To decide |
| Experiments | Hardware and budgets | `cpu`, `ram`, `time_budget` | Fair cross-instance comparisons | To document |
| Plots | Figure options | labels, dimensions, color map | Presentation-only; not optimization | Configurable options |

**Important:** proposed algorithm parameters are planned configuration fields, **not evidence of existing implementation**. Some settings (e.g., ALNS weights and temperature) only apply if the selected search method uses them.

### 7.3 Previously used *demonstration-only* values

The prior notebook-development record shows a synthetic configuration with illustrative defaults:

```python
@dataclass(frozen=True)
class SyntheticConfig:
    n_customers: int = 42
    max_vehicles: int = 8
    vehicle_capacity: float = 35.0
    min_demand: int = 1
    max_demand: int = 9
    coordinate_max: float = 100.0
    depot_xy: tuple[float, float] = (50.0, 50.0)
    layout: str = "uniform"  # or "clustered"
    seed: int = 2026
    distance_policy: str = "raw"  # raw / nearest_integer / ceil
```

A small hand-written teaching example used:

```python
EXAMPLE_COORDS = [
    [50, 50], [14, 70], [21, 42], [35, 16],
    [75, 76], [86, 45], [62, 20],
]
EXAMPLE_DEMANDS = [0, 6, 5, 4, 7, 3, 2]
EXAMPLE_CAPACITY = 16.0
EXAMPLE_MAX_VEHICLES = 3
EXAMPLE_ROUTES = [[1, 2, 3], [4, 5, 6]]  # manually supplied, not optimized
```

These are **examples only**, never universal constants in the math or future solver. The user's explicit requirement was to support arbitrary meaningful capacity, fleet, demand, and customer-count values.

---

## 8. Synthetic inputs, VRPLIB and benchmarking conventions

### 8.1 Required data sources

1. **Synthetic CVRP instances:** configurable number of customers; random seeds; uniform or clustered locations; adjustable demand ranges, depot, capacity and fleet count; cost matrix from coordinates or supplied data. Generation does not construct optimal routes.
2. **VRPLIB instances:** use the actual `vrplib` package to read benchmark files; extract capacity, demand, coordinates/edge weights, depot, and available vehicle limit (if provided). Retain source IDs and map depot to internal index 0.
3. **Reference solutions:** parse `.sol` records when available, validate their feasibility, recompute their cost using the correct edge-weight convention and distinguish a published optimum from an unproven best-known cost.

### 8.2 Benchmark example previously used

| Field | Recorded A-n32-k5 value |
|---|---|
| Benchmark family | Augerat Set A, CVRP |
| Name | `A-n32-k5` |
| Nodes | 32 including one depot |
| Customers | 31 |
| Vehicle count | 5 in the reported reference solution. **CVRPLIB labels `K=5` as the minimum number of vehicles, not as the number of available trucks in every model.** |
| Truck capacity | 100 |
| Edge representation | `EUC_2D` coordinates, rounded to nearest integer for this reference |
| Reference cost | 784, marked **proven optimal** in the CVRPLIB catalog for A-n32-k5 |
| Reference routes | Five externally supplied tours, used as **validation input**, not optimized by notebook; individual route-sequence provenance requires independent checking |
| Prior validation | Published cost recomputed as 784; route feasibility and ILP equations reported as passed |

**Historical reference route sequences (internal IDs):**

```text
Route #1: 21 31 19 17 13 7 26
Route #2: 12 1 16 30
Route #3: 27 24
Route #4: 29 18 8 9 22 15 10 25 5 20
Route #5: 14 28 11 4 23 3 2 6
Cost: 784
```

**Do not infer that `-k5` is automatically an upper bound on available trucks.** The dataset and catalog describe 5 as the *minimum number of vehicles*. The current ILP uses an *at-most-$K$* parameter, which must be chosen consistently with the comparison protocol. For this instance, a feasible five-route reference is reported and its cost matches the cataloged optimum. For other instances, confirm the admissible fleet definition before comparing gaps.

The prior notebook contained an embedded text version of `A-n32-k5.vrp` and `.sol` to work offline; **that original generated binary notebook and sample files are not available in the current runtime** (see artifact manifest). The route sequence and cost above reflect the prior recorded notebook and should be revalidated against the authoritative benchmark if reused.

### 8.3 Distance conventions

For coordinates $p_i=(a_i,b_i)$, raw Euclidean distance is

$$D_{ij}=\sqrt{(a_i-a_j)^2+(b_i-b_j)^2}.$$

The recorded Set A reference used **nearest-integer** distances, as modeled by `floor(D + 0.5)` for nonnegative $D$. The `vrplib` documentation confirms that `EUC_2D` is parsed as **unrounded double-precision Euclidean distances**, so users must explicitly apply the benchmark-family convention where appropriate. Do **not** default to NumPy `round` for all instances (ties-to-even behavior). **Do not apply the same rounding rule to every VRPLIB family without checking it.** Preserve `EXPLICIT` edge weights and distinguish `EUC_2D`, `FLOOR_2D`, `CEIL_2D` and `EXACT_2D` rather than blindly applying a generic rule. Published reference cost must be evaluated with the same conventions as produced solutions, or gaps are meaningless.

### 8.4 Fleet metadata caveat

Not all benchmark files include an explicit **maximum available fleet**. `A-n32-k5` has the $k5$ naming convention and a file comment stating **“Min no of trucks: 5”**; the CVRPLIB catalog likewise identifies **minimum number of vehicles = 5**. This is **not automatically** the same concept as an available-fleet upper bound $K$ in our ILP. For a given instance, determine and document whether the benchmark defines a fleet limit, fixes the number of tours, or merely reports a minimum/known route count. If an upper bound is required but absent, obtain the evaluation convention or set an **explicit, disclosed** override.

Do **not** silently translate arbitrary filename suffixes into universally enforced maximum fleet constraints. Comparing a five-vehicle-restricted solution with an unrestricted reference value can be invalid if route-count constraints differ.

### 8.5 Input validation and solution validation

**Data:** ensure valid depot, matching demand lengths and matrix dimensions, nonnegative finite distances and demands, positive vehicle capacity, valid available fleet, consistent coordinates and source IDs, and $q_i\le Q$.

**Candidate routes:** require valid customer labels, exactly one visit each, no duplicate or skipped customers, capacity per route, active routes $\le K$, start/end at depot, and correct distance recomputation. An independent checker can reconstruct the $x,y,z,u$ variables and evaluate all ILP equations; this still does **not** constitute a route solver.

### 8.6 Synthetic example visualization themes from prior notebook

Customer spatial map with demand-colored or demand-sized points; histograms of demands; capacity lines; aggregate feasibility counterexamples; arc-decision diagrams; distance heatmaps; disconnected subtour visuals; MTZ contradiction diagram; hand-written route maps; vehicle load/slack bars; rejected invalid-route scenarios; zero-demand edge case; reference solution routes; per-route reference costs; rounded/unrounded comparison; $Q$ vs vehicle lower bound; $O(Kn^2)$ variable growth; uniform vs clustered distributions; fleet/capacity condition heatmap.

---

## 9. What has been implemented and what has not

### 9.1 Previously reported modeling notebook

- Name: `CesiCDP_CVRP_Detailed_Modeling.ipynb`.
- **Previously reported:** 68 cells total, 39 Markdown cells, 29 Python cells, 19 figures, end-to-end execution without errors.
- Sections reported: context and assumptions; graph/data notation; configurable synthetic generation; input checks; geometry and demand visuals; decision variables; distance objective; full constraints and MTZ subtour elimination; complexity proof; route validation and direct equation certification; VRPLIB loading; A-n32-k5 reference checks; parameter sensitivity; model scaling; edge cases; tutor checklist; bibliography.
- Reported dependencies: `numpy`, `pandas`, `matplotlib`, `vrplib` (optional fallback for the embedded simple EUC_2D case), Python/Jupyter.
- Key modeling Python constructs: `SyntheticConfig`, `CVRPInstance`, `euclidean_cost_matrix`, `generate_synthetic`, `validate_routes`, `certify_model_equations`, `load_cvrp`, `parse_reference_solution`, and plotting utilities. **These refer to recorded notebook content, not a freshly verified current file.**
- Prior route checker validated existing user/benchmark candidates; **did not construct or optimize routes**.
- Tutor review remains outstanding.

### 9.2 What is definitely NOT completed in the visible conversation

- No coded route-construction optimization algorithm reported.
- No ALNS or other metaheuristic implementation reported.
- No exact ILP solver execution reported.
- No optimization-produced result for A-n32-k5; its cost is a known *reference*.
- No experimental campaign on **at least 20 different instances** reported.
- No empirical algorithm runtime/scalability measurements reported.
- No comparative result gaps from **our own** solver reported.
- No final consolidated notebook or English slide deck/presentation reported.
- No tutor approval or final ADEME submission reported.
- No verified GitHub repository creation, remote URL, pushes or commits recorded.

### 9.3 Meaning of “modeling” in this project

**Modeling** means translating logistics into a mathematical optimization problem: what the input means; what choices may be made; what objective is minimized; what constraints characterize feasible routes; how complexity follows from related NP-hard problems. A modeling notebook may contain plotting, data reading, constraint checkers, and illustrative examples **without containing an optimizer**. Algorithm design, solution search, statistical evaluation and presentation are distinct later deliverables.

---

## 10. Detailed end-to-end project roadmap

The project phases below consolidate the prior 30-step to-do list with the formal assignment. A checked box means the **prior notebook contains a draft of that component**, not that it has passed tutor review.

### Phase 1 — Formal CVRP modeling (current)

- [x] **1. Define problem/context:** sustainable delivery logistics; current CVRP scope; one depot; static distance objective; identical-capacity truck fleet; no split deliveries.
- [x] **2. Define data and sets:** $V,C,A,F,n,K,Q,q_i,d_{ij}$, coordinates and depot mapping; describe domains and assumptions.
- [x] **3. Define decisions:** binary arc $x$, assignment $y$, vehicle-use $z$, auxiliary order $u$.
- [x] **4. Define objective:** total fleet distance, including all departure/return legs.
- [x] **5. Define constraints:** exactly-once service, assignment-flow linkage, depot starts/returns, capacity, vehicle activation, zero self-loops, MTZ disconnected subtour elimination, variable domains.
- [x] **6. Prove NP-hardness:** polynomial-time reduction from TSP; distinction between optimization NP-hard and decision NP-complete.
- [ ] **7. Final independent validation/tutor check:** review equations and edge cases; confirm at-most-$K$ semantics and distance objective; incorporate tutor feedback into corrected final PLNE. The notebook draft reportedly included tests and examples, but independent tutor confirmation is not yet documented.

**Milestone:** Mathematical Modeling Notebook, during Prosit 3, ungraded checkpoint per assignment.

### Phase 2 — Python environment and datasets

- [ ] **8. Project setup:** organize `.ipynb`, source scripts, `data/`, benchmark and results directories; install packages; lock or record dependency versions; document Python environment/PEP conventions.
- [ ] **9. Dataset pipeline:** configure/load synthetic and VRPLIB instances; parse depot, original IDs, coordinates, demands, capacities, fleet constraint and costs; load known solutions; handle missing fleet metadata.
- [ ] **10. Input validation:** dimension and data checks, nonnegative values, single depot, known/explicit cost matrix conventions, necessary feasibility conditions, clear rejection messages.

### Phase 3 — Algorithm design and implementation

- [ ] **11. Solution representation:** routes as variable-length lists of customer IDs, with depot implicit or explicit; route load, distance, fleet use, cost and feasibility.
- [ ] **12. Initial construction:** compare candidate greedy insertion and Clarke–Wright Savings; generate feasible candidate or report construction failure.
- [ ] **13. Local search:** 2-opt, relocate, swap, optional 2-opt*, efficient delta costs, capacity-aware move filtering.
- [ ] **14. Metaheuristic:** choose/justify ALNS or another eligible approach; define destroy and repair operators, adaptive selection, acceptance of improving/worsening moves, best-feasible tracking, stopping criteria.
- [ ] **15. Performance/scaling:** incremental distance evaluation, candidate lists, vectorization where valuable, profiling, memory analysis, robust stopping time, thousands-of-customers trials.
- [ ] **16. Unit/integration testing:** coverage, capacity, depot, no duplicates, exactly-once, cost calculation, deterministic seeds, edge cases and per-operator validity.

**Milestone:** documented Python CVRP algorithm that actually generates and improves routes.

### Phase 4 — Experimental design

- [ ] **17. Curate ≥20 distinct benchmark instances** with varied size, customer distributions, capacity pressure and fleet constraints; use reference costs where available; include synthetic scenarios as warranted.
- [ ] **18. Define protocol:** repeated seeds, uniform hardware/software, runtime or iteration budgets, results schema, parameter tuning split and comparison fairness.
- [ ] **19. Select comparisons:** initial baseline vs metaheuristic; optimal/BKS; optional exact ILP on small cases for proof/bounds; record why each comparison is valid.

### Phase 5 — Benchmark execution, visualization and analysis

- [ ] **20. Execute tests** on ≥20 different instances (with repeated runs of stochastic methods), persist routes and metadata, and track any failures or infeasibility.
- [ ] **21. Assess quality:** cost, feasibility, gap-to-optimum or gap-to-BKS, runtime and difficulty by category; use benchmark-specific distance convention.
- [ ] **22. Analyze statistically:** mean, std, min, max, quartiles, success/feasibility rate, variability between seeds, costs/timing vs size, trends vs capacity/demand/spatial structure, parameter sensitivity.
- [ ] **23. Interpret findings:** explain strengths, weaknesses, difficult scenarios, quality-time trade-offs, scalability, experimental caveats and justified modifications.

**Milestone:** documented experimental-analysis notebook with meaningful data, figures and conclusions.

### Phase 6 — Consolidated final notebook

- [ ] **24. Include corrected formal model** and tutor feedback; explicitly document any use or non-use of an exact solver and valid bounds if applicable.
- [ ] **25. Document chosen algorithm:** solution definition, initialization, operators, neighborhoods, guiding mechanism, iteration, stopping, adjustable settings and technical rationale.
- [ ] **26. Integrate experiment design/results:** reproducible data, reference values, gaps, charts, statistics, interpretation and limitations.
- [ ] **27. Quality assurance:** notebook run-all tests, environment/data dependency manifest, references, coherent storytelling, clean figures, code performance/comment readability, final conclusions.

**Milestone:** final project deliverable, **the day before the defense**.

### Phase 7 — English oral defense

- [ ] **28. Build presentation** with context, objectives, core CVRP formulation, algorithm, results, risks, limitations, accomplishments and future schedule.
- [ ] **29. Live demo** using small instances so execution is fluid; demonstrate loading, optimization, feasibility and route visualization; prepare fallback screenshots/results.
- [ ] **30. Team rehearsal and submission:** divide responsibilities among four members, practice English explanations and anticipated questions, verify final deliverable, conduct oral defense.

**Milestone:** presentation on the last day of the academic block. The brief also mentions an ADEME July 12 submission (exact year/relationship to academic dates needs confirmation).

---

## 11. Performance evaluation and statistical protocol

### 11.1 Mandatory minimum

- **At least 20 distinct instances**. Repeated runs on one instance are valuable but do **not** count as distinct instances.
- **VRPLIB** parsing via `vrplib` and comparison with known reference costs.
- Cost and execution time measurements; experiments across different instance characteristics; visualization and statistical discussion.
- Robust reproducibility: seeds, dependency versions, hardware and resource limits.

### 11.2 Suggested scenario factors (proposed, not grading thresholds)

| Scenario type | Illustrative ranges/settings | Purpose |
|---|---|---|
| Small | 20–100 customers | Debugging, potential exact comparisons |
| Medium | 100–500 customers | Neighborhood/operator effectiveness |
| Large | 500–1000 customers | Runtime and search scalability |
| Very large | 1000+ customers | Investigate requirement ambition “several thousand” |
| Geography | Uniform, clustered, mixed | Spatial-structure sensitivity |
| Demand/capacity | Low/moderate/high capacity pressure | Feasibility and algorithm difficulty |
| Fleet | Different $K$, documented bound source | Fleet usage vs route quality |
| Metaheuristic | Seeds, iteration/runtime budgets, removal fraction, acceptance, neighborhood size | Robustness and tuning |

Ranges are **experimental categories**, not fixed caps built into code. The experiment plan should define actual supported instances and distinguish tuning vs evaluation data.

### 11.3 Required and useful output metrics

- Instance ID/source and characteristics: $n,K,Q$, total demand, demand distribution, coordinates type, reference value and status (optimal/BKS).
- Feasible solution: yes/no, vehicle count used, routes, load per route.
- Best observed total distance from **our algorithm** (when implemented).
- Initial solution cost and relative improvement.
- Best/mean/std/worst final cost across repeated runs, optional quartiles/confidence bands.
- Runtime, including clear exclusion/inclusion of data loading and plotting.
- Gap (%) and whether its reference is proven optimal or only BKS.
- Termination reason, time budget, number of iterations, software/hardware, random seed.
- Sensitivity analysis and explainable limitations.

### 11.4 No unsupported benchmark claims

The modeling notebook validated the **published A-n32-k5 reference route** with cost 784. That does **not** establish that the team's future algorithm finds 784 or any particular gap. All claimed algorithm performance must come from the actual future solver experiment and recorded conditions.

---

## 12. Architecture, reproducibility, testing and team work

### 12.1 Candidate repository structure (recommendation, not current verified tree)

```text
EcoRoute-CVRP/
├── README.md
├── context.md                  # This context handoff
├── requirements.txt            # To create
├── notebooks/
│   ├── 01_cvrp_modeling.ipynb   # Previously produced under a different filename
│   ├── 02_cvrp_algorithm.ipynb  # To build
│   └── 03_experiments.ipynb     # To build
├── src/
│   ├── instances.py            # To build/extract if useful
│   ├── feasibility.py          # To build/extract if useful
│   └── solver.py               # To build
├── data/
│   ├── synthetic/              # To populate
│   └── vrplib/                 # To populate; respect dataset provenance
├── results/                    # To populate
├── figures/                    # To populate
├── references/                 # Optional
└── presentation/               # To create
```

Production-grade modularity is **not mandatory** per assignment. The directory layout is optional; readability, reproducibility and performance are essential.

### 12.2 Already mentioned libraries and tooling

- Python, Jupyter Notebook/IPython.
- `numpy`, `pandas`, `matplotlib` for validation, numerical data and plots.
- `vrplib` for CVRP benchmark reading.
- `dataclasses`, `pathlib`, `math`, `collections.Counter`, `re` and standard Python utilities in recorded notebook.
- A future optimization algorithm can rely on Python scientific tools and carefully designed incremental update operations; no solver library has yet been required or chosen.
- Optional exact ILP packages mentioned in prior explanatory answers: Gurobi, CPLEX, CBC, but **not** implemented and not compulsory for first modeling check.

### 12.3 Testing checklist

- Validate matrix shape, demands, depot, fleet and numerical domains.
- Verify objective cost equals sum of selected route arcs.
- Verify all customers served exactly once, no duplicate/missing labels, capacity constraints, route starts/ends at depot and disconnected subtours excluded.
- Explicitly test zero-demand customers, a customer at capacity, unused trucks, insufficient aggregate capacity, bin-packing counterexamples, one vehicle and one customer, asymmetric and nonmetric distances where supported.
- Check route checks on both hand-written candidate and published reference solutions; never assume a reference route is a solver output.
- Record random seeds; ensure any future numerical tests are deterministic when requested.
- Test algorithm moves and statistics separately once implemented.

### 12.4 Suggested four-person division of work (not assigned to named individuals)

1. **Math/formalization lead:** assumptions, ILP, NP-hardness, correctness, tutor feedback.
2. **Algorithm lead:** initial construction, neighborhood/local search, metaheuristic.
3. **Data/benchmark lead:** VRPLIB, instance metadata, validation, experiments and statistics.
4. **Integration/documentation lead:** notebooks, figures, presentation coordination and reproducibility.

All team members should understand the model, participate in review/testing, and speak during the final presentation as assigned.

---

## 13. Academic and technical references, including all user-given URLs

### 13.1 URLs supplied by the user (highest priority to retain)

**A. CESI official project statement, deliverables (“Livrables attendus”):**

- https://scenari.cesi.fr/scenari/cas/Diffusion_FISE_INFO_A3_Algorithmique_et_optimisation_26_27_ETU/_5_-_Projet.html#

**B. CESI official project modality (“Modalité”):**

- https://scenari.cesi.fr/scenari/cas/Diffusion_FISE_INFO_A3_Algorithmique_et_optimisation_26_27_ETU/_5_-_Projet.html#

**C. User-provided VRPLIB tutorial/examples repository:**

- https://github.com/PyVRP/VRPLIB

These are the **three source-link occurrences** supplied in the original statement; the two CESI references happen to be the same base URL with a trailing hash. The French source text in Section 3 retains the linked labels and context.

### 13.2 Scientific literature cited in prior modeling work

1. **Dantzig, G. B., & Ramser, J. H. (1959).** “The Truck Dispatching Problem.” *Management Science*, 6(1), 80–91. https://doi.org/10.1287/mnsc.6.1.80 . Foundational vehicle-routing work.
2. **Clarke, G., & Wright, J. W. (1964).** “Scheduling of Vehicles from a Central Depot to a Number of Delivery Points.” *Operations Research*, 12(4), 568–581. https://doi.org/10.1287/opre.12.4.568 . Construction-heuristic reference for later work.
3. **Miller, C. E., Tucker, A. W., & Zemlin, R. A. (1960).** “Integer Programming Formulation of Traveling Salesman Problems.” *Journal of the ACM*, 7(4), 326–329. https://doi.org/10.1145/321043.321046 . Classic subtour-elimination concept adapted to vehicle routing.
4. **Toth, P., & Vigo, D. (eds.). (2014).** *Vehicle Routing: Problems, Methods, and Applications* (2nd ed.). SIAM. https://doi.org/10.1137/1.9781611973594 . General VRP reference.
5. **Uchoa, E., Pecin, D., Pessoa, A., Poggi, M., Vidal, T., & Subramanian, A. (2017).** “New Benchmark Instances for the Capacitated Vehicle Routing Problem.” *European Journal of Operational Research*, 257(3), 845–858. https://doi.org/10.1016/j.ejor.2016.08.012 . Benchmark literature.
6. **Augerat, P., Belenguer, J. M., Benavent, E., Corberán, A., Naddef, D., & Rinaldi, G. (1995).** “Computational Results with a Branch and Cut Code for the Capacitated Vehicle Routing Problem.” Research report, Université Joseph Fourier, Grenoble. Classic Augerat instance family.
7. **Laporte, G. (2009).** “Fifty Years of Vehicle Routing.” *Transportation Science*, 43(4), 408–416. https://doi.org/10.1287/trsc.1090.0301 . Previously suggested overview of VRP development.

These were introduced or discussed during notebook development; **the user did not originally supply these papers**. During this review, the **publisher/DOI pages for Dantzig–Ramser, Clarke–Wright, Miller–Tucker–Zemlin, Toth–Vigo, and Laporte**, plus **the Uchoa et al. journal record**, were located. The Augerat report was corroborated through a scholarly reference listing. **This does not mean full-text contents were checked**; recheck bibliography formatting against your academic citation style before submission.

### 13.3 Other data and implementation URLs appearing in prior work

- **CVRPLIB benchmark catalog:** https://galgos.inf.puc-rio.br/cvrplib/
- **Verified A-n32-k5 catalog record** (31 customers, minimum 5 vehicles, capacity 100, proven optimum 784): https://galgos.inf.puc-rio.br/cvrplib/en/plots/4
- **Example A-n32-k5 VRP mirror:** https://github.com/mkalinowski/CVRP/blob/master/dane/A-n32-k5.vrp
- **Prior recorded route-sequence reference document:** https://ltu.diva-portal.org/smash/get/diva2%3A1972726/FULLTEXT01.pdf
- **PyVRP/VRPLIB library:** https://github.com/PyVRP/VRPLIB (also user-supplied above)

**Provenance caveat:** these additional resource URLs primarily reflect prior assistant notebook references. In the 2026-11-02 review, the CVRPLIB page, VRPLIB GitHub documentation and A-n32-k5 VRP GitHub mirror were independently accessed; the LTU PDF route-list attribution was **not independently checked**. The CESI page itself could not be extracted by the web tool because it returned `application/xhtml+xml` unsupported by that reader; the **user-pasted French statement remains the controlling available text**, not a claim of live-page verification. The original user-provided URLs are explicitly isolated in 13.1.

---

## 14. Chronological user prompts and explicit instructions

> **Purpose:** preserve the actual user's instructions so later assistants do not mistake an assistant's suggestion for a user requirement. The original long French prompt is reproduced substantially verbatim in Section 3 and referenced rather than duplicated here. Original spelling/capitalization is retained where visible. Chronology is the visible conversation order; not every message carried an explicit timestamp.

### Earlier messages from the related CESI-PROJECT conversation (source: project-history excerpt)

The project context also includes an earlier discussion titled **“Optimisation des tournées de livraison”** (2026-10-21). The following user messages were **missing from version 1** of this context file. They were visible in the provided project-conversation excerpt and are preserved here. Their associated assistant code or README artifacts are **not independently available for inspection** in this session.

> Create the detailed CVRP mathematical modeling Jupyter

*The preceding prompt is only shown as a truncated excerpt in project history; do not claim it is verbatim complete.*

> did you only do the modeling part? explain what you did so far

> Before I review, just let me know what you've done. Write a brief summary of what you've done. What do you mean by modeling, and also what parameters are modifiable? Go ahead, let me know. Be very concise.

> make a detailed README about what needs to be done , with steps , TODOs, what has already been done, what is yet to be done, if there are things that need validation/ research / approval from me, mark them, KEEP IN MIND WE MUST NOT IGNORE ANY DETAIL, ALL THE THINGS I'VE TOLD YOU TO TURN INTO VARIABLE PARAMETERS,  ALL THE POTENTIAL DETAILS THAT THE PROFESSORS COULD ASK US ABOUT, LEAVE NOTHING TO RANDOMNESS, DONT BE LAZY, no matter how long the run takes, EVEN THE ALGORITHM MUST BE AS OPTIMAL AS POSSIBLE, WE'VE DONE THE MODELING SO FAR, SO NOTE ALL THE NEXT STEPS

> i want you to review the implementation plan for mistakes, the thing we must avoid at all costs, is a bad algorithm or a non optimal one, and missng details, review it go ahead

**Interpretation:** The user requires rigorous **algorithm comparison, parameterization, edge-case coverage and critical reviews**; they do not want an arbitrarily selected or poor-performing heuristic. “As optimal as possible” is a performance goal, **not proof that a metaheuristic can always find the optimum**. No earlier implementation plan or README is claimed verified until its bytes are available.

### Prompt 1 — Original French assignment (full text: Section 3)

User pasted the environmental ADEME/CesiCDP statement and assignment with official links, versions, deliverable requirements, evaluation and VRPLIB reference. **See Section 3 for the near-verbatim source transcription**, subject to the stated whitespace/markup caveat.

### Prompt 2 — Language instruction

> answer in english neve i french, start over

**Effect:** response/documentation language English; only the archived original assignment stays French.

### Prompt 3 — Question about final corrected ILP

> what do they lmean byt htat modélisation mathématique sous forme de Programme Linéaire en Nombres Entiers (PLNE) complète et corrigée,
>
> -

**Effect:** clarify that final PLNE must have decision variables, objective, complete constraints, correct subtour logic, and corrections after tutor review.

### Prompt 4 — Begin with CVRP variables, objective, constraints, conditional code

> so in our modeling we must have a set of potential decisions that the algorithm can make , an objective function (like a cost function we have to minimize) and a set of constraints we have eto follow, lets start with that problem, what are the constraints, objectiv efuction, for now oNLY WORK ON THE CVRP not the advanced version, and give a python implementation of it, ipynb script  (IF REQUIRED BY THE ENONCÉ)

**Effect:** CVRP only; modeling includes decision variables, cost function and constraints; first check excludes a required optimization solver.

### Prompt 5 — End-to-end checklist and full parameterization

> break up the project into steps, like a to do list, explain what step we're at right now, give details, MAKE SURE TO INCLUDE EVERY STEP, we musgt also have a lot of parameters like capacity etc like we mustnt fix anything

**Effect:** comprehensive plan and parameterized model/implementation, no hard-coded capacities/fleet counts/customer counts.

### Prompt 6 — Highly detailed notebook with plots; ask before starting

> go ahead, make a ipynb script, with A LOT OF PLOTTING and HIGHLY DETAILED COMMENTS, DO NOT MISS ANYTHING, for now only do the modeling, go ahead ask me questions before you start

**Effect:** high-detail, visualization-rich modeling notebook; assistant then clarified objective, data and code scope.

### Prompt 7 — All notebook choices explicitly confirmed

> Create the detailed CVRP mathematical modeling Jupyter Notebook (.ipynb) now. Confirmed decisions: primary objective = distance for VRPLIB benchmark compatibility; data = both synthetic examples and VRPLIB benchmarks; Python modeling code = plots, instance parsing, constraint illustrations, and feasibility checks, but no optimization solver. Include complete parametrized CVRP ILP, all necessary constraints and subtour elimination, rigorous complexity proof, extensive explanations and comments, many meaningful visualizations, academic references, and a verified downloadable .ipynb file.

**Effect:** authoritative final specification of the first modeling deliverable, replacing ambiguous prior defaults.

### Prompt 8 — Status question

> did you only do the modeling part? explain what you did so far

**Effect:** explicitly distinguish modeling code/plots from actual optimization algorithm implementation.

### Prompt 9 — Concise progress and configurable parameters

> Before I review, just let me know what you've done. Write a brief summary of what you've done. What do you mean by modeling, and also what parameters are modifiable? Go ahead, let me know. Be very concise.

**Effect:** record the definition of modeling and clearly list configurable input fields.

### Prompt 10 — Project name

> give a name to the project

Assistant proposed “EcoRoute — Intelligent Delivery Route Optimization.”

### Prompt 11 — GitHub repo name

> for a github repo

Assistant proposed `EcoRoute-CVRP`, description: *A Python-based Capacitated Vehicle Routing Problem (CVRP) optimization project featuring mathematical modeling, metaheuristic algorithms, route visualization, and VRPLIB benchmarking*. Suggested URL was `github.com/your-username/EcoRoute-CVRP` — a **placeholder, not a verified repository URL**.

### Prompt 12 — Exhaustive context document (previous instruction)

> i want you to basically give me back all the ressources i gave you at the start of the conversation, the enoncé, the sources, the prompts telling you what to do, and compile them in a context.md file , DO NOT OMIT ANYTHING IT NEEDS TO HAVE EVERYTHING THERE IS TO KNOW ABOUT THE PROJECT, DONT LEAVE ANY DETAIL, FIRST I WANT YOU TO MAKE A LIST OF EVERYTHING THERE IS TO KNOW ABOUT OUR PROJECT, LEAVE NO STONE UNTURNED

**Effect:** compile the complete inventory, original assignment, user sources, chronological prompts, decisions, work status, parameters, roadmap and uncertainties into this file; avoid false claims about unavailable data.

### Prompt 13 — Full accuracy and audit request (2026-11-02)

> verify what you wrote, any mistakes or things you would correct? the file needs to be 10000% accurate, no minor mistakes review it for mistkaes and minor upgrades/ corrections, CHECK EVERYTHING

**Effect:** independently audit and revise the actual `context.md`, check facts against official documentation where possible, fix benchmark/modeling ambiguities, add previously missing project-history prompts and record remaining unverifiable claims rather than asserting absolute certainty.

---

## 15. Assistant decisions, suggested approach and corrections

### 15.1 Earlier explanations that are compatible with the assignment

- A PLNE is a discrete mathematical optimization formulation, specifying legal decisions, cost to minimize and explicit feasibility rules.
- It is not the same thing as an implementation of an algorithm to find high-quality routes.
- The first checkpoint explicitly requires **no solver** or discussion of resolution methods. Modeling code that plots and checks candidate routes is acceptable, so long as it does not claim to satisfy the later solver requirement.
- The original longer problem (traffic-dependent time) is not identical to the standard CVRP benchmark. The user selected distance so that reference comparisons make sense.
- The model's $Q,K,n,q_i,d_{ij}$ are parameters. Numeric demonstrations do not fix them globally.
- A complete final PLNE must incorporate tutor corrections and avoid missing subtour constraints.
- The optimization CVRP is NP-hard. The decision version is NP-complete under usual encoding assumptions.

### 15.2 Prior assistant recommendations (not confirmed requirements)

- Start with a strong static CVRP baseline, then consider optional advanced features only if explicitly approved.
- Use greedy insertion or Clarke–Wright Savings for an initial feasible solution.
- Add 2-opt, relocate, swap, and possibly 2-opt* for local improvement.
- Choose ALNS (adaptive large neighborhood search) as a plausible main metaheuristic; define removal/insertion operators, acceptance and stopping criteria.
- Use `vrplib` and multiple benchmark families; compare to BKS with correct rounding.
- Use a four-person role split and a repository directory organization as suggested in Section 12.
- Make notebook content story-driven, with charts, equations and interpretation.

**These are planning suggestions until approved/implemented.** Do not claim that ALNS is chosen by the user, or that it is already coded. A particularly strong user requirement from the earlier related project conversation is **to critically evaluate alternatives and avoid a weak/noncompetitive algorithm**: compare credible baselines and, where useful, established high-performance approaches (e.g. hybrid genetic search) before finalizing the metaheuristic. ALNS is not proven best by this project record.

### 15.3 Clarifications and potential corrections to keep visible

- **At most $K$ versus exactly $K$:** current model allows unused trucks. Confirm with tutor if exactly $K$ required. Importantly, the *minimum vehicles* field on CVRPLIB is neither interpretation by itself; benchmark comparison must respect the original benchmark constraints.
- **PLNE versus MILP terminology:** if $u$ is continuous, MILP; if integer, all-integer PLNE. Both describe a mixed discrete routing formulation; specify domains consistently.
- **Reference gap terminology:** using a BKS denominator does not certify optimality.
- **Time vs distance:** original narrative's duration/traffic objective is deferred by deliberate user selection; flag for academic consistency.
- **Date precision:** original text supplies “July 12 next” and relative academic milestones, not verified calendar-year deadlines.
- **Large instances:** an exact three-index ILP is a valid specification, but cannot be assumed tractable at thousands of nodes.
- **Reference data:** benchmark routes in the notebook were not generated by our solver.
- **Graph symmetry:** no universal need for $d_{ij}=d_{ji}$, unless an instance specifically provides symmetric Euclidean costs.
- **Feasibility:** $KQ\ge\sum_i q_i$ does not alone imply feasibility due to indivisible deliveries.
- **Degree conditions:** without MTZ or equivalent connectivity cuts, separate customer cycles could satisfy local flow equations but be invalid routes.

---

## 16. Open questions, risks, limitations and next action

### 16.1 Questions to settle with the tutor/team

1. **Does the final CVRP require at most $K$ vehicles, or exactly $K$ used vehicles?**
2. Is using **distance** rather than initial brief's **time-dependent travel duration** accepted for the selected Level B/VRPLIB benchmark scope?
3. Which official datasets are supplied by CESI (file links, instance families, fleet metadata, cost rules), if any beyond the explicitly linked `vrplib` repository?
4. Which algorithm/metaheuristic will the team implement — ALNS or another method? **What evidence/baselines justify its quality and robustness?**
5. What runtime or iterations budget, hardware, seeds and repetitions define a fair experimental protocol?
6. What is the exact submission **year** for July 12 and the actual dates of Prosit 3, final notebook and defense?
7. Which benchmark costs are **proven optimal** and which are **BKS**?
8. Do instances include customer demands of zero, asymmetric road costs, non-Euclidean matrices, fleet constraints or other special conventions?
9. Are there any further tutor corrections to the mathematical constraints/notation?
10. Which teammates own implementation, experiment review, report integration and English presentation?

### 16.2 Risks to monitor

- Incomplete subtour constraints produce mathematically invalid “solutions.”
- Inconsistent rounding yields false reported gaps.
- Confusion between a known reference route and algorithm performance yields unsubstantiated results.
- Treating unprovided fleet metadata as a magic constant undermines reproducibility.
- Testing the same instance 20 times does not satisfy **20 different instances**.
- No benchmark budget controls or seeds makes stochastic comparisons unfair.
- Performance bottlenecks of quadratic dense matrices and expensive local-search operations may make thousands-of-customers ambition difficult.
- Claiming an exact optimum without a certificate or authoritative reference is incorrect.
- Late tutor feedback could require changing fleet semantics or objective.

### 16.3 Immediate action, in order

1. **Review the modeling notebook** and check equations plus the notebook's reported execution on your machine. This context file is not a substitute for the actual `.ipynb`.
2. **Validate with tutor**: fleet semantics, scope/objective, model assumptions, NP-hardness reduction and complete PLNE.
3. **Record tutor corrections** and revise the notebook/model accordingly.
4. **Design/configure instance-loading and solver interfaces** (dynamic $n,K,Q,q,d$ and benchmark metadata).
5. **Implement** the chosen initial heuristic, local search and metaheuristic in the next deliverable, then test and benchmark on at least 20 distinct instances.

---

## 17. Artifact manifest and provenance/verification status

### 17.1 Historically reported generated artifacts

| Filename / record | Prior claim | Availability/verification in this context-compilation session |
|---|---|---|
| `CesiCDP_CVRP_Detailed_Modeling.ipynb` | Detailed 68-cell CVRP modeling notebook; 19 plots, fully executed | **Not mounted or discoverable in current session.** Its content and execution are known only through previous conversation/tool record. |
| `CesiCDP_CVRP_Modeling_Package.zip` | ZIP containing notebook, sample `.vrp`, `.sol` and README | **Not mounted or discoverable in current session**. |
| `A-n32-k5.vrp` | Real benchmark sample in package, also embedded in notebook | **Not mounted in current session**. Reacquire/verify from authoritative source as needed. |
| `A-n32-k5.sol` | Published reference route file in package | **Not mounted in current session**. Route sequence is archived in Section 8. |
| `README_CVRP_Modeling.txt` | Prior package readme | **Not mounted in current session**. |
| `CesiCDP_CVRP_Mathematical_Modeling.ipynb` | Earlier theory-only modeling version | **Not mounted in current session**. |
| `context.md` | **This file** — context handoff and 2026-11-02 forensic audit | **Physically inspected, corrected and structurally checked in this review.** Earlier notebook assets were not recovered. |

Earlier assistant replies linked the notebook and package using sandbox paths. These links are **historical pointers** and must not be treated as guaranteed available in a new runtime. No new links are fabricated here.

### 17.2 Verification notes

- The prior assistant stated that the detailed notebook had **68 cells, 29 code, 39 Markdown and 19 plots**, and that it executed end-to-end and validated the A-n32-k5 reference. This section records **what was reported**, not a claim that the `.ipynb` has been independently re-opened during this file creation.
- A project/conversation file search during initial context compilation returned **no accessible notebook assets**; in the present review, `context.md` itself **is** mounted and inspected, but earlier notebook assets remain unverified. The `context.md` content has therefore been constructed from **the visible conversation and supplied text**, not by silently reading missing artifacts.
- The exact raw encoding/spacing of the original pasted source may differ from a re-downloaded CESI page. This file preserves the *visible user-pasted text* and points to the original URL.
- New additions after this snapshot should be appended under a new dated change note: user decision, tutor correction, algorithm implementation milestone, benchmark result and newly verified source; never overwrite the original assignment section.

---

---

## 18. 2026-11-02 forensic review and correction log

**Purpose:** record discrepancies found when reopening `context.md`, re-reading the user-provided assignment and project-history excerpt, checking the full 3-index CVRP formulation, and consulting primary external documentation. This log documents **what could and could not be verified**, rather than claiming impossible “10000%” certainty.

### 18.1 Corrections applied to this file

1. **Benchmark `K` semantics (material):** CVRPLIB explicitly displays `A-n32-k5` as **31 customers, *minimum* number of vehicles 5, capacity 100**, with **784 marked as proven optimum**. A benchmark's *minimum number of vehicles* is **not** automatically the *maximum available fleet* in our current MILP. The cost comparison is valid only when the solver and published reference share compatible fleet/route-count rules. The original sample file's comment also says `Min no of trucks: 5`.
2. **Provenance of reference tours:** a previous notebook/report recorded five routes whose rounded cost was 784, but the specific external route-list source was **not reverified** in this review. The total optimal **value** is independently corroborated by CVRPLIB, which is not itself a re-verification of the exact route sequences.
3. **Distance parsing/rounding:** the `vrplib` project's documentation says `EUC_2D` returns **unrounded** Euclidean distances. Different historical benchmark sets can follow different conventions. Never apply nearest-integer rounding to all datasets or all `EXPLICIT` edge matrices indiscriminately.
4. **Missing user instructions:** added the earlier CESI-PROJECT messages demanding an exhaustive README, exhaustive review, professor-ready detail, configurable inputs and a **strong rather than casually chosen algorithm**. These are important additional requirements, not optional stylistic requests.
5. **Algorithm quality caution:** ALNS remains **only an untested proposal**. Its superiority is not established; evaluate credible alternatives and reproducible strong baselines. A stochastic metaheuristic does **not** ensure global optimality on every instance.
6. **Repository naming:** `EcoRoute-CVRP` was suggested by the assistant after a naming request; the user did **not explicitly accept** it, and no GitHub remote has been verified. The file no longer treats proposal as an accepted creation event.
7. **French source precision:** retained the source transcription but replaced the absolute label “unabridged, as supplied” with **“substantially unabridged / near-verbatim”**; no byte-for-byte comparison with the original chat export was possible.
8. **Verification transparency:** distinguished the mounted, audited `context.md` from earlier modeling notebooks whose actual files were not available to this review. Corrected wording that could suggest every artifact was re-opened.
9. **Source audit:** added primary CVRPLIB and `vrplib` documentation confirmations, corrected source-check status, and preserved the unresolved ability to validate the live CESI XHTML page.
10. **Prompt chronology:** appended the current audit request and separately archived earlier project-conversation excerpts, preserving their provenance.

### 18.2 Independently checked external facts and source records

| Claim | Review result | Source |
|---|---|---|
| A-n32-k5: 31 customers, five **minimum** vehicles, Q=100, reference 784 | **Confirmed**; CVRPLIB marks the reference as optimal | https://galgos.inf.puc-rio.br/cvrplib/en/plots/4 |
| Example `.vrp` file contains `Min no of trucks: 5` and `Optimal value: 784` | **Confirmed** in an accessible source mirror; original dataset provenance still should be tracked | https://github.com/mkalinowski/CVRP/blob/master/dane/A-n32-k5.vrp |
| Python `vrplib` supports `read_instance` and `read_solution`; computed `EUC_2D` edge weights are unrounded | **Confirmed** from project documentation | https://github.com/PyVRP/VRPLIB |
| Uchoa et al. (2017), EJOR 257(3), 845–858, DOI 10.1016/j.ejor.2016.08.012 | **Confirmed** from journal metadata | https://www.sciencedirect.com/science/article/pii/S0377221716306270 |
| MTZ 1960 publication metadata (JACM 7(4), 326–329, DOI 10.1145/321043.321046) | **Confirmed** in bibliographic listing | https://www.scienceopen.com/document?vid=128b1ab2-8ab1-48bc-a611-6d5ec410a824 |
| Dantzig–Ramser, Clarke–Wright, Laporte and Toth–Vigo DOI destinations | **Confirmed accessible as publisher/book records**; not a full-paper content audit | DOI links in Section 13.2 |
| Augerat et al. research report title/authors, 1995 | **Corroborated** by scholarly references | https://doi.org/10.1007/S10107-003-0481-8 |
| The live CESI assignment page contains exactly the pasted statement | **Not independently verified**; web reader could not extract the page (`application/xhtml+xml`) | User-supplied CESI URL in Section 13.1 |
| Exact five-route sequence cited in earlier notebook PDF | **Not independently verified in this review** | Prior route-list URL in Section 13.3 |
| Earlier notebook execution, charts and exact code implementation | **Historically reported, not independently re-executed in this review** | Prior assistant conversation, Section 17 |

### 18.3 Mathematical consistency review

- **Objective:** $\min\sum_{k,(i,j)} d_{ij}x_{ijk}$ correctly minimizes *total static travel distance* for the basic chosen CVRP. This explicitly differs from the original duration/traffic narrative; tutor approval should be sought.
- **Service:** M1 with M2/M3 assigns every customer to one and only one entering/leaving truck.
- **Depot and fleet:** M4/M5 require exactly one start/return for every **active** vehicle and allow inactive vehicles; this encodes an *at-most-$K$* model, subject to tutor and benchmark convention validation.
- **Capacity:** M6 uses $Qz_k$ so an inactive truck cannot have positive assigned demand. For **zero-demand** assignments, M4/M5 plus MTZ still exclude orphaned subtours and inconsistent vehicle use.
- **Connectivity:** M7/M8 with $u_{ik}\in[0,n]$ when assigned, zero otherwise, and big-$M=n+1$ correctly forbid disconnected customer-only cycles; the coefficient is derived from the stated bounds, **not a free hyperparameter**.
- **Variables:** When $u$ is continuous this is **MILP**; declaring $u$ integer gives a fully integer model matching a strict PLNE interpretation. The report should choose one and be consistent.
- **Completeness:** Under **one depot, at most $K$, nonnegative demands, no split deliveries and a finite complete directed cost graph**, all feasible model assignments correspond to legal CVRP routes and vice versa. No time windows, dynamic traffic or shift constraints are included.
- **Complexity:** TSP reduction with one vehicle, $Q=n$, and unit demands is valid; optimization NP-hard, decision NP-complete with finite/rational input encoding.
- **Size:** $Kn(n+1)$ arc binaries + $Kn$ assignment binaries + $K$ activation binaries = $K(n+1)^2$ total binary variables, plus $Kn$ order variables. MTZ inequality count $Kn(n-1)$ is correct.
- **Lower bounds:** $\lceil\sum_iq_i/Q\rceil$ and $\max_iq_i\le Q$ are **necessary**, not sufficient for unsplittable delivery packing.

### 18.4 Outstanding validation gates: do not silently claim closure

- [ ] Re-open and execute the original modeling `.ipynb` file **when supplied/mounted**, revalidate every chart, cost, parser, rounding policy, route checker, model-certificate check and saved output.
- [ ] Compare the exact five A-n32-k5 route sequences to a canonical `.sol` download or separately documented academic source, not just the final cost 784.
- [ ] Independently confirm the CESI **live** page or obtain the tutor's official assignment PDF/export; retain original wording and update any newer grading rules separately.
- [ ] Settle whether the **selected CVRP benchmark** treats vehicle count as a fixed limit, a minimum count, a route-cost-only objective with unrestricted trucks, or another standard. Ensure **the same feasible set** when computing gaps.
- [ ] Confirm with tutor the departure from original **duration/traffic** wording to **distance** for Level B evaluation.
- [ ] Establish repo creation, final algorithm, benchmark selection, exact deadlines, team ownership and runtime hardware/limits from direct evidence.
- [ ] Record each future correction with date, evidence, effect on code, reviewer and acceptance status.

**Review conclusion:** the core *static CVRP* math is coherent under its explicitly listed assumptions. The critical fixes were **benchmark fleet semantics**, **reference provenance**, **missing project-history instructions**, and **overstated verification/acceptance language**. Absolute certainty about unavailable artifacts and the live CESI site is not defensible; the unresolved checks above remain open.


### 18.5 Professor/tutor defense preparation — questions to be able to answer

This checklist reflects likely technical scrutiny, **not verified examination questions** or extra formal grading rules:

- [ ] Precisely state the basic CVRP scope, one-depot assumption, no split deliveries, fixed distance objective, and why traffic/time windows are excluded despite the broader introductory description.
- [ ] Explain every index and variable ($x_{ijk}$, $y_{ik}$, $z_k$, $u_{ik}$), variable domain, and which values are inputs rather than hard-coded constants.
- [ ] Derive the objective and justify including departures and returns; distinguish total fleet distance from maximum route duration and fleet count.
- [ ] Explain why degree/flow equations alone allow disconnected subtours, and demonstrate the MTZ cycle contradiction.
- [ ] Justify the exact $(n+1)$ big-$M$ coefficient and the order-variable bounds, including zero-demand clients.
- [ ] Prove both directions of model correctness: legal routes ⇒ feasible variables, and feasible variables ⇒ legal routes.
- [ ] Give a valid TSP-to-CVRP polynomial reduction; distinguish NP-hard optimization from NP-complete decision problems.
- [ ] Explain exactly-$K$, at-most-$K$, and CVRPLIB **minimum vehicle count** as different concepts.
- [ ] Explain individual-demand and aggregate-capacity necessary bounds, and why they are not sufficient (bin packing).
- [ ] Explain distance parsing for `EUC_2D`, explicit matrices, nearest-integer reference conventions and why mismatches invalidate reported gaps.
- [ ] Explain **optimal** versus **best-known** references, how negative BKS gaps can arise, and how to verify reference-route feasibility.
- [ ] Justify the chosen metaheuristic with comparisons, neighborhood design, acceptance strategy, runtime/memory considerations, and evidence that it is competitive. **Never claim global optimality from a stochastic solver without proof.**
- [ ] Explain experiment reproducibility (at least 20 different instances, repetitions, seeds, budgets, CPU/hardware), proper statistics, and tuning/test separation.
- [ ] Explain scaling to thousands of customers: why the explicit MILP has $O(Kn^2)$ arc variables, why a dense $n\times n$ `float64` distance matrix uses approximately $8n^2$ bytes, and when sparse/on-demand costs are appropriate.
- [ ] Explain environmental motivation while acknowledging **distance is a proxy**, not an independently measured carbon-emissions model.
- [ ] Explain what has actually been coded, what has only been modeled, what requires tutor approval, and what experimental claims cannot yet be made.

### 18.6 Structural check of the corrected context file

- Markdown code fences paired; source links and heading navigation retained.
- The original assignment transcription is kept in its own fenced source section, rather than overwritten by English paraphrase.
- Mathematical and benchmark corrections are in Sections 6–8 and 18; original source statements remain distinguishable from chosen assumptions.
- Unavailable artifacts, unverified source-route attribution, and inaccessible live CESI source are not presented as confirmed.
- Future users should repeat this audit after integrating tutor decisions, the actual notebooks, or updated official assignment files.

---

## Final scope reminder for future contributors and AI assistants

**Current target:** model, then implement, then benchmark a **parameterized basic CVRP** minimizing **total distance**, with identical-capacity vehicles, unique customer visits, one depot, fleet and capacity restrictions, and disconnected subtour prevention. Current draft modeling included mathematical equations, many plots and candidate-route feasibility checks. **No route-search optimization solver has been implemented yet** in the recorded project work. Advanced windows, waiting and time-dependent traffic remain archived as original assignment context, not part of the selected current formulation. Follow the official CESI grading requirements, including **at least 20 distinct benchmark instances**, and confirm tutor feedback before declaring modeling finished.
