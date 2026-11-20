"""Monte Carlo прогноз для ЛР9. Python 3.9+, без сторонніх бібліотек.

Запуск з кореня репозиторію:
    python lr09_forecast/monte_carlo.py
    python lr09_forecast/monte_carlo.py <шлях до lr09_reference_velocity.csv>
Другий варіант додає три прогони на навчальних даних курсу (220 points).
Навчальні дані в репозиторій не копіюються, щоб не змішувати їх з моїми.
"""
import sys
import csv
import math
import random
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SIMS = 10000
SEED = 2026


def sprints_needed(remaining, history, rng):
    """Одна симуляція: тягнемо velocity, поки залишок не стане <= 0."""
    n = 0
    while remaining > 0:
        remaining -= rng.choice(history)
        n += 1
    return n


def percentile_up(values, p):
    """Найменше число, нижче або на рівні якого лежить p частка результатів."""
    s = sorted(values)
    k = math.ceil(p * len(s)) - 1
    return s[max(k, 0)]


def run(remaining, history, sims=SIMS, seed=SEED):
    rng = random.Random(seed)
    res = [sprints_needed(remaining, history, rng) for _ in range(sims)]
    return percentile_up(res, 0.50), percentile_up(res, 0.85)


def read(path):
    with (ROOT / path).open(encoding='utf-8-sig', newline='') as f:
        return list(csv.DictReader(f))


if __name__ == '__main__':
    vel = read('lr09_forecast/velocity.csv')
    mine = [int(r['points_done']) for r in vel]
    est = {r['story_id']: int(r['final_estimate']) for r in read('lr08_poker/estimates.csv')}
    rel1 = [r['story_id'] for r in read('lr06_backlog/backlog.csv') if r['release'] == 'REL-1']
    done = {'S-11', 'S-12', 'S-01', 'S-03', 'S-07', 'S-05'}  # закриті у спринтах 1-2
    total = sum(est[s] for s in rel1)
    left = sum(est[s] for s in rel1 if s not in done)
    print('Моя velocity:', mine)
    print('Весь перший реліз', total, run(total, mine))
    print('Залишок після двох спринтів', left, run(left, mine))
    if len(sys.argv) > 1:
        with open(sys.argv[1], encoding='utf-8-sig', newline='') as f:
            ref = [int(r['points_done']) for r in csv.DictReader(f)]
        print('Навчальні, 12 спринтів', run(220, ref))
        print('Навчальні, спринти 1-2', run(220, ref[0:2]))
        print('Навчальні, спринти 5-6', run(220, ref[4:6]))
