import { formatSgd } from '@/lib/exchange-rate';

export default function PriceChart({ prices, rate }: { prices: Record<string, number>; rate: number }) {
  const groups = ['', '-holo'].map(suffix => ({
    name: suffix ? 'Holo average prices' : 'Reference average prices',
    points: [30, 7, 1].map(days => ({ days, value: prices[`avg${days}${suffix}`] * rate }))
      .filter(point => Number.isFinite(point.value) && point.value >= 0),
  })).filter(group => group.points.length);
  if (!groups.length || !Number.isFinite(rate) || rate <= 0) return null;
  return <figure className="average-chart"><figcaption>Average price comparison · SGD</figcaption><p className="market-meta">These are overlapping averages, not daily price history.</p>
    {groups.map(group => {
      const maximum = Math.max(...group.points.map(point => point.value), 1);
      return <div key={group.name}><h4>{group.name}</h4><div className="average-bars" role="img" aria-label={`${group.name} in SGD`}>
        {group.points.map(point => <div className="average-bar" key={point.days}><span>{formatSgd(point.value)}</span><div className="average-bar-track"><div style={{ height: `${point.value / maximum * 100}%` }} /></div><span>{point.days}-day</span></div>)}
      </div></div>;
    })}
  </figure>;
}
