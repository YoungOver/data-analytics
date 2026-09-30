"""Анализ продаж интернет-магазина: когорты, RFM, ABC. Демо-данные генерируются, в работе — выгрузка из CRM/1С.
python report.py -> report.html + png"""
import base64
import io
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

rng = np.random.default_rng(11)
OUT = Path(__file__).parent
plt.rcParams.update({'font.family': 'Arial', 'font.size': 11, 'axes.spines.top': False, 'axes.spines.right': False,
                     'axes.edgecolor': '#9aa0a6', 'axes.titleweight': 'bold', 'axes.titlesize': 13})
C1, C2, C3 = '#2f6df6', '#f25c54', '#1fb58f'

# ---------- демо-данные: 6 000 клиентов, заказы за 12 месяцев
n = 6000
first = pd.to_datetime('2025-10-01') + pd.to_timedelta(rng.integers(0, 365, n), unit='D')
chan = rng.choice(['Поиск', 'Таргет', 'Маркетплейс', 'Рассылка'], n, p=[.38, .27, .25, .10])
loy = {'Поиск': .55, 'Таргет': .35, 'Маркетплейс': .25, 'Рассылка': .7}
rows = []
cats = ['Уход за лицом', 'Волосы', 'Тело', 'Наборы', 'Аксессуары']
for i in range(n):
    d, k = first[i], 0
    while d < pd.Timestamp('2026-09-30') and k < 30:
        cat = rng.choice(cats, p=[.34, .22, .2, .14, .1])
        amt = float(rng.lognormal(7.6 if cat != 'Наборы' else 8.2, .45))
        rows.append((i, d, chan[i], cat, round(amt)))
        k += 1
        if rng.random() > loy[chan[i]] * (0.92 ** k):
            break
        d += pd.Timedelta(days=int(rng.gamma(2.2, 24)))
df = pd.DataFrame(rows, columns=['client', 'date', 'channel', 'category', 'amount'])
df['month'] = df['date'].dt.to_period('M')
df['cohort'] = df.groupby('client')['date'].transform('min').dt.to_period('M')
df['age'] = (df['month'] - df['cohort']).apply(lambda x: x.n)


def fig_b64(fig):
    buf = io.BytesIO()
    fig.savefig(buf, format='png', dpi=160, bbox_inches='tight')
    plt.close(fig)
    return base64.b64encode(buf.getvalue()).decode()


# ---------- 1. выручка по месяцам и каналам
m = df.pivot_table(index='month', columns='channel', values='amount', aggfunc='sum').fillna(0) / 1e6
fig, ax = plt.subplots(figsize=(8, 3.6))
m.plot.area(ax=ax, color=[C1, '#8ab4ff', C3, C2], alpha=.9, lw=0)
ax.set_title('Выручка по каналам, млн ₽'); ax.set_xlabel(''); ax.legend(frameon=False, ncol=4, loc='upper left', fontsize=9)
g1 = fig_b64(fig)

# ---------- 2. когортное удержание
coh = df.groupby(['cohort', 'age'])['client'].nunique().unstack(fill_value=0)
ret = coh.div(coh[0], axis=0).iloc[:, :7] * 100
ret = ret.iloc[:-1]
fig, ax = plt.subplots(figsize=(8, 4.2))
im = ax.imshow(ret.values, cmap='Blues', vmin=0, vmax=40, aspect='auto')
ax.set_xticks(range(ret.shape[1]), [f'M{i}' for i in ret.columns]); ax.set_yticks(range(len(ret)), [str(p) for p in ret.index])
for (r, c), v in np.ndenumerate(ret.values):
    if c > 0 and not np.isnan(v) and v > 0:
        ax.text(c, r, f'{v:.0f}%', ha='center', va='center', fontsize=8, color='white' if v > 22 else '#333')
ax.set_title('Удержание по когортам: доля клиентов, вернувшихся через N месяцев')
ax.spines[:].set_visible(False)
g2 = fig_b64(fig)

# ---------- 3. повторные покупки по каналам
rep = df.groupby(['channel', 'client']).size().gt(1).groupby('channel').mean().sort_values() * 100
ltv = df.groupby(['channel', 'client'])['amount'].sum().groupby('channel').mean().reindex(rep.index)
fig, ax = plt.subplots(figsize=(8, 3.2))
bars = ax.barh(rep.index, rep.values, color=[C2 if v < 30 else C1 for v in rep.values])
for b, v, l in zip(bars, rep.values, ltv.values):
    ax.text(v + .8, b.get_y() + b.get_height() / 2, f'{v:.0f}%  ·  LTV {l / 1000:.1f} тыс ₽', va='center', fontsize=10)
ax.set_xlim(0, max(rep.values) * 1.6); ax.set_title('Доля клиентов с повторной покупкой')
g3 = fig_b64(fig)

# ---------- 4. ABC по категориям
abc = df.groupby('category')['amount'].sum().sort_values(ascending=False)
share = abc.cumsum() / abc.sum() * 100
fig, ax = plt.subplots(figsize=(8, 3.2))
ax.bar(abc.index, abc.values / 1e6, color=C1)
ax2 = ax.twinx(); ax2.plot(abc.index, share.values, color=C2, marker='o'); ax2.set_ylim(0, 105); ax2.spines['right'].set_visible(True)
ax.set_title('ABC-анализ категорий: выручка, млн ₽ и накопленная доля, %')
g4 = fig_b64(fig)

# ---------- ключевые цифры
tot = df['amount'].sum()
aov = df['amount'].mean()
clients = df['client'].nunique()
r_all = df.groupby('client').size().gt(1).mean() * 100
best, worst = rep.idxmax(), rep.idxmin()
m3 = ret[3].mean()

html = f'''<!doctype html><html lang="ru"><head><meta charset="utf-8">
<link href="https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@400;600;700&family=IBM+Plex+Mono:wght@500&display=swap" rel="stylesheet">
<style>*{{margin:0;box-sizing:border-box}}body{{width:1500px;background:#f5f6f8;font-family:'IBM Plex Sans';color:#1d2430;padding:60px}}
h1{{font-size:44px;letter-spacing:-1px}}.sub{{color:#5c6675;font-size:19px;margin:10px 0 36px}}
.k{{display:grid;grid-template-columns:repeat(5,1fr);gap:16px;margin-bottom:26px}}.k div{{background:#fff;border-radius:16px;padding:20px}}
.k b{{font-size:34px;display:block}}.k span{{color:#5c6675;font-size:15px}}
.g{{display:grid;grid-template-columns:1fr 1fr;gap:20px}}.c{{background:#fff;border-radius:16px;padding:18px}}.c img{{width:100%}}
.ins{{background:#1d2430;color:#fff;border-radius:16px;padding:28px 32px;margin-top:20px;display:grid;grid-template-columns:repeat(3,1fr);gap:30px;font-size:17px;line-height:1.55}}
.ins b{{display:block;font-size:14px;color:#8ab4ff;font-family:'IBM Plex Mono';margin-bottom:8px}}</style></head><body>
<h1>Продажи интернет-магазина косметики: что удерживает клиентов</h1>
<div class="sub">Отчёт по заказам за 12 месяцев · когорты, повторные покупки, ABC · Python, pandas, matplotlib · демо-данные</div>
<div class="k"><div><b>{f'{tot / 1e6:.1f}'.replace('.', ',')} млн ₽</b><span>выручка за год</span></div><div><b>{f'{clients:_}'.replace('_', ' ')}</b><span>клиентов</span></div>
<div><b>{f'{aov:_.0f}'.replace('_', ' ')} ₽</b><span>средний чек</span></div><div><b>{r_all:.0f}%</b><span>купили повторно</span></div><div><b>{m3:.0f}%</b><span>возвращаются на 3-й месяц</span></div></div>
<div class="g"><div class="c"><img src="data:image/png;base64,{g1}"></div><div class="c"><img src="data:image/png;base64,{g3}"></div>
<div class="c"><img src="data:image/png;base64,{g2}"></div><div class="c"><img src="data:image/png;base64,{g4}"></div></div>
<div class="ins"><div><b>ВЫВОД 1</b>Клиенты из канала «{best}» возвращаются чаще всех ({rep.max():.0f}%), из «{worst}» — реже всех ({rep.min():.0f}%). Бюджет на привлечение стоит считать по LTV, а не по цене первого заказа.</div>
<div><b>ВЫВОД 2</b>Основной отток — между первым и вторым месяцем. Письмо с подборкой ухода на 20–25-й день после покупки закрывает именно эту яму.</div>
<div><b>ВЫВОД 3</b>{abc.index[0]} и {abc.index[1]} дают {share.iloc[1]:.0f}% выручки — категория A. Наборы при меньшей доле поднимают средний чек: их стоит предлагать в корзине.</div></div>
</body></html>'''
(OUT / 'report.html').write_text(html.replace('{0}', ''), encoding='utf-8')
print('ok', len(df), 'заказов')
