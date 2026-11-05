"""Simulation de test : programme 2024 contre programme 2026 (écrite en 2026).

Hypothèses (pas des mesures) :
- vent en rafales autour de 5 m/s pendant 120 s (signal reproductible, graine fixe) ;
- génératrice à aimants et bobine : tension ALTERNATIVE, d'amplitude 0,9 V par m/s,
  de fréquence 4 Hz par m/s (rotation proportionnelle au vent) ;
- 2024 : la génératrice est branchée directement sur A0, comme dans le montage de 2024 (CAN 0-5 V,
  les tensions négatives lisent 0, celles au-dessus de 5 V lisent 1023 et sont dangereuses pour l'entrée) ;
  seuil 100/1023, une lecture toutes les 100 ms ;
- 2026 : pont de diodes (chute 1,4 V), condensateur de lissage (constante de temps 0,2 s), pont
  diviseur 33 k / 10 k, moyenne sur 8 mesures toutes les 50 ms, hystérésis 3,0 / 2,5 V,
  2 s minimum entre deux commutations.
Usage : python simulation.py   (graphique dans images/simulation-2024-2026.png si matplotlib est installé)
"""
import math
import os
import random
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

DUREE = 120.0
DT = 0.0005                      # pas de simulation (s), assez fin pour la sinusoïde
K_AMPL = 0.9                     # V crête par m/s
K_FREQ = 4.0                     # Hz par m/s


def vent(t, _cache={}):
    if not _cache:
        rnd = random.Random(2024)
        _cache["c"] = [(rnd.uniform(0.3, 1.2), rnd.uniform(0.02, 0.25), rnd.uniform(0, 6.3)) for _ in range(8)]
    v = 5.0 + sum(a * math.sin(2 * math.pi * f * t + p) for a, f, p in _cache["c"])
    return max(0.0, v)


def can(volts):
    return max(0, min(1023, int(volts / 5.0 * 1023)))


def simuler():
    t, phase = 0.0, 0.0
    # 2024
    r24, ch24, prochaine24, surtension = False, 0, 0.0, 0.0
    # 2026
    vc, r26, ch26, prochaine26, dernier26, buf = 0.0, False, 0, 0.0, -10.0, []
    journal = []
    while t < DUREE:
        v = vent(t)
        phase += 2 * math.pi * K_FREQ * v * DT
        u_ac = K_AMPL * v * math.sin(phase)
        if u_ac > 5.0:
            surtension += DT
        # 2024 : lecture directe toutes les 100 ms
        if t >= prochaine24:
            prochaine24 += 0.100
            nouveau = can(u_ac) > 100
            if nouveau != r24:
                ch24 += 1
                r24 = nouveau
        # 2026 : redressement + lissage RC (décharge lente dans le pont diviseur)
        u_red = max(0.0, abs(u_ac) - 1.4)
        if u_red > vc:
            vc += (u_red - vc) * min(1.0, DT / 0.002)       # charge rapide par les diodes
        else:
            vc -= vc * DT / 0.2                              # décharge, constante de temps 0,2 s
        if t >= prochaine26:
            prochaine26 += 0.050
            a0 = vc * 10 / 43
            buf = (buf + [can(a0) * 5.0 / 1023 * 4.3])[-8:]
            m = sum(buf) / len(buf)
            if t - dernier26 >= 2.0:
                if not r26 and m > 3.0:
                    r26, ch26, dernier26 = True, ch26 + 1, t
                elif r26 and m < 2.5:
                    r26, ch26, dernier26 = False, ch26 + 1, t
        if int(t / DT) % 200 == 0:
            journal.append((t, v, u_ac, vc, r24, r26))
        t += DT
    return ch24, ch26, surtension, journal


if __name__ == "__main__":
    ch24, ch26, surt, j = simuler()
    print(f"Sur {DUREE:.0f} s de vent simulé (5 m/s en moyenne, rafales) :")
    print(f"  programme 2024 : {ch24} commutations du relais ({ch24/DUREE*60:.0f} par minute)")
    print(f"  programme 2026 : {ch26} commutations du relais ({ch26/DUREE*60:.1f} par minute)")
    print(f"  tension instantanée au-dessus de 5 V sur A0 en 2024 : {surt:.1f} s ({surt/DUREE*100:.0f} % du temps)")
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError:
        raise SystemExit("(matplotlib absent : pas de graphique)")
    T = [e[0] for e in j]
    fig, ax = plt.subplots(4, 1, figsize=(9, 7.5), dpi=110, sharex=True)
    ax[0].plot(T, [e[1] for e in j], color="#3b5b85"); ax[0].set_ylabel("vent (m/s)")
    ax[1].plot(T, [e[2] for e in j], color="#999", lw=0.4, label="tension alternative de la génératrice")
    ax[1].plot(T, [e[3] for e in j], color="#c8102e", lw=1.4, label="après redressement et lissage (2026)")
    ax[1].axhline(5, ls="--", color="#555", lw=0.8); ax[1].text(1, 5.3, "5 V : limite de l'entrée A0", fontsize=8, color="#555")
    ax[1].set_ylabel("tension (V)"); ax[1].legend(fontsize=7, loc="lower right")
    ax[2].step(T, [int(e[4]) for e in j], where="post", color="#e08a00"); ax[2].set_ylabel("relais 2024")
    ax[3].step(T, [int(e[5]) for e in j], where="post", color="#2e8b3a"); ax[3].set_ylabel("relais 2026")
    for a in ax[2:]:
        a.set_yticks([0, 1]); a.set_yticklabels(["ouvert", "fermé"])
    ax[2].set_title(f"2024 : {ch24} commutations en {DUREE:.0f} s", fontsize=9, loc="left")
    ax[3].set_title(f"2026 : {ch26} commutations en {DUREE:.0f} s", fontsize=9, loc="left")
    ax[3].set_xlabel("t (s)")
    for a in ax: a.grid(alpha=.3)
    fig.suptitle("Simulation : même vent, programme 2024 contre programme 2026 (hypothèses dans simulation.py)", fontsize=10)
    fig.tight_layout()
    out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "images", "simulation-2024-2026.png")
    fig.savefig(out); print("graphique :", os.path.normpath(out))
