import { useEffect, useState } from 'react';
import { apiClient } from '@/infrastructure/api/client';

const COLOR: Record<string, string> = { green: '#22c55e', yellow: '#eab308', red: '#ef4444' };

export const ReportsPage = () => {
  const [stats, setStats] = useState<any>(null);
  const [fin, setFin] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    (async () => {
      try {
        const y = new Date().getFullYear();
        const [s, f] = await Promise.all([
          apiClient.get('/reports/dashboard-stats'),
          apiClient.get('/reports/financial', { params: { period_start: y + '-01-01', period_end: y + '-12-31' } }),
        ]);
        setStats(s.data);
        setFin(f.data);
      } catch (e: any) {
        setError(e && e.message ? e.message : 'Failed to load reports');
      }
    })();
  }, []);

  return (
    <div className="page-container">
      <h1 className="text-2xl font-bold mb-6">Отчеты</h1>
      {error && <div className="auth-error mb-4"><span>{error}</span></div>}
      {fin && (
        <div className="card mb-4">
          <h2 className="text-lg font-medium mb-2">Финансовый отчёт</h2>
          <p className="text-sm text-muted">
            Заказов: {fin.orders_count} · Выручка: €{fin.total_revenue} · Маржа: €{fin.total_margin} · Пробег: {fin.total_distance} км · Средняя ставка: €{fin.avg_rate.toFixed(2)}/км
          </p>
        </div>
      )}
      {stats && (
        <div className="card">
          <h2 className="text-lg font-medium mb-2">Выполнение плана</h2>
          <table className="w-full text-sm">
            <tbody>
              <tr className="border-b border-border">
                <td className="py-2 text-muted">Выручка</td>
                <td>€{stats.revenue.fact} / €{stats.revenue.plan}</td>
                <td style={{ color: COLOR[stats.revenue.status_color] || '#888' }}>{stats.revenue.status_color}</td>
              </tr>
              <tr className="border-b border-border">
                <td className="py-2 text-muted">Маржа</td>
                <td>€{stats.margin.fact} / €{stats.margin.plan}</td>
                <td style={{ color: COLOR[stats.margin.status_color] || '#888' }}>{stats.margin.status_color}</td>
              </tr>
              <tr>
                <td className="py-2 text-muted">Пробег</td>
                <td>{stats.distance.fact} / {stats.distance.plan} км</td>
                <td style={{ color: COLOR[stats.distance.status_color] || '#888' }}>{stats.distance.status_color}</td>
              </tr>
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
};
