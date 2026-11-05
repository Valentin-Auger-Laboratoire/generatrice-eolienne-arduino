# Brochage et comportement exact / Pin mapping and exact behaviour

## Montage de 2024 (`code/eolienne_2024`)

| Élément | Raccordement | Rôle |
|---|---|---|
| Génératrice, sortie + | **A0, en direct** | tension lue par le CAN (0 à 1023 pour 0 à 5 V) |
| Génératrice, sortie − | GND | — |
| Module relais 1 voie (KY-019), commande | D8 | HIGH = relais fermé |
| Module relais, alimentation | 5 V / GND | — |
| LED rouge + résistance 220 Ω | entre la sortie **NO** du relais et GND | s'allume quand le relais est fermé, **à condition que COM soit relié au +5 V** (non précisé en 2024) |
| Condensateur | « facultatif » dans la liste de 2024 | — |

Comportement exact :

| Élément | Valeur |
|---|---|
| Seuil | `analogRead(A0) > 100`, soit environ **0,49 V** |
| Hystérésis | aucune |
| Période | `delay(100)` : une lecture toutes les ~100 ms |
| Message série | `Tension lue: 123` (valeur brute 0-1023), à 9600 bauds |
| Tension négative (génératrice alternative) | lue 0 par le CAN, mais **hors des limites de l'entrée** (−0,5 V maximum) |
| Tension > 5 V | lue 1023, **hors des limites de l'entrée** |

## Montage de 2026 (`code/eolienne_2026`)

```
génératrice ~ ──► pont de diodes ──► C 100 µF ──► 33 kΩ ──► A0 ──► 10 kΩ ──► GND
                                                        └─► Zener 5,1 V ──► GND (protection)
D8 ──► commande du module relais        COM du relais ──► +5 V
NO du relais ──► 220 Ω ──► LED ──► GND    D13 (LED de la carte) = recopie de l'état du relais
```

| Élément | Valeur |
|---|---|
| Rapport du pont diviseur | (33 k + 10 k) / 10 k = **4,3**, soit jusqu'à environ 21 V mesurables |
| Conversion | `V = analogRead(A0) × 5 / 1023 × 4,3` (V, après redressement) |
| Lissage logiciel | moyenne glissante sur **8 mesures**, une mesure toutes les **50 ms** |
| Hystérésis | relais **fermé au-dessus de 3,0 V**, **ouvert sous 2,5 V** |
| Anti-claquement | **2 s** minimum entre deux changements d'état |
| Boucle | non bloquante (`millis()`) |
| Sortie série | toutes les 500 ms : `t_ms,tension_V,moyenne_V,relais` (CSV, en-tête à la mise sous tension) |

## Simulation (`simulation/simulation.py`, hypothèses)
- **Vent** : 5 m/s en moyenne, avec des rafales (graine fixe, résultat reproductible).
- **Génératrice** : alternative, 0,9 V crête par m/s et 4 Hz par m/s.
- **Diodes** : chute de 1,4 V dans le pont.
- **Condensateur** : décharge avec une constante de temps de 0,2 s.
- **Résultat sur 120 s** : 608 commutations en 2024, contre 30 en 2026. En 2024, plus de 5 V sur A0 pendant 7 % du temps.
