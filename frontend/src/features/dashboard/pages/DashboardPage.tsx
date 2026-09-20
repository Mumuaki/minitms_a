import { useEffect, useState } from 'react';
import { apiClient } from '@/infrastructure/api/client';

type StatCard = { plan: number; fact: number; unit: string; status_color: string };
type Dash = { revenue: StatCard; margin: StatCard; distance: StatCard; avg_rate: number };

const COLOR: Record<string, string> = { green: '#22c55e', yellow: '#eab308', red: '#ef4444' };

function pct(fact: number, plan: number): string {
  if (!plan) return '—';
  return Math.round((fact / plan) * 100) + '%';
}

export const DashboardPage = () => {
  const [data, setData] = useState<Dash | null>(null);
  const [orders, setOrders] = useState<number | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    (async () => {
      try {
        const [d, o] = await Promise.all([
          apiClient.get<Dash>('/reports/dashboard-stats'),
          apiClient.get<any[]>('/orders/'),
        ]);
        setData(d.data);
        setOrders(o.data.length);
      } catch (e: any) {
        setError(e && e.message ? e.message : 'Failed to load dashboard');
      }
    })();
  }, []);

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">Дашборд</h1>
      {error && <div className="auth-error mb-4"><span>{error}</span></div>}
      {!data && !error ? (
        <p className="text-muted">Загрузка…</p>
      ) : data ? (
        <>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            <div className="bg-card p-6 rounded-lg shadow-sm border border-border">
              <h3 className="text-sm font-medium text-muted">Выручка (План/Факт)</h3>
              <div className="mt-2 text-2xl font-bold">€ {data.revenue.fact} <span className="text-sm text-muted">/ {data.revenue.plan}</span></div>
              <p className="text-xs mt-1" style={{ color: COLOR[data.revenue.status_color] || '#888' }}>{pct(data.revenue.fact, data.revenue.plan)} выполнения</p>
            </div>
            <div className="bg-card p-6 rounded-lg shadow-sm border border-border">
              <h3 className="text-sm font-medium text-muted">Маржа (План/Факт)</h3>
              <div className="mt-2 text-2xl font-bold">€ {data.margin.fact} <span className="text-sm text-muted">/ {data.margin.plan}</span></div>
              <p className="text-xs mt-1" style={{ color: COLOR[data.margin.status_color] || '#888' }}>{pct(data.margin.fact, data.margin.plan)} выполнения</p>
            </div>
            <div className="bg-card p-6 rounded-lg shadow-sm border border-border">
              <h3 className="text-sm font-medium text-muted">Пробег (План/Факт)</h3>
              <div className="mt-2 text-2xl font-bold">{data.distance.fact} <span className="text-sm text-muted">/ {data.distance.plan} км</span></div>
              <p className="text-xs mt-1" style={{ color: COLOR[data.distance.status_color] || '#888' }}>{pct(data.distance.fact, data.distance.plan)} выполнения</p>
            </div>
            <div className="bg-card p-6 rounded-lg shadow-sm border border-border">
              <h3 className="text-sm font-medium text-muted">Средняя ставка</h3>
              <div className="mt-2 text-2xl font-bold">€ {data.avg_rate.toFixed(2)} / км</div>
              <p className="text-xs text-muted mt-1">Факт</p>
            </div>
          </div>
          <div className="bg-card p-6 rounded-lg shadow-sm border border-border">
            <h2 className="text-lg font-medium mb-4">Заказы</h2>
            <p className="text-muted text-sm">{orders === null ? 'Загрузка…' : orders + ' заказов за период'}</p>
          </div>
        </>
      ) : null}
    </div>
  );
};
