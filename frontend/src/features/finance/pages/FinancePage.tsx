import { useEffect, useState } from 'react';
import { apiClient } from '@/infrastructure/api/client';

export const FinancePage = () => {
  const [plans, setPlans] = useState<any[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [msg, setMsg] = useState<string | null>(null);
  const [f, setF] = useState({ vehicle_id: '1', period_start: '', period_end: '', revenue_target: '', margin_target: '', distance_target: '' });

  const load = async () => {
    try {
      const r = await apiClient.get('/financial/plans');
      setPlans(r.data);
    } catch (e: any) {
      setError(e && e.message ? e.message : 'Failed to load plans');
    }
  };
  useEffect(() => { load(); }, []);

  return (
    <div className="page-container">
      <h1 className="text-2xl font-bold mb-6">Финансы и Планирование</h1>
      {error && <div className="auth-error mb-4"><span>{error}</span></div>}
      <div className="card mb-4">
        <h2 className="text-lg font-medium mb-3">Новый план</h2>
        <form className="flex flex-wrap gap-2" onSubmit={async (e) => {
          e.preventDefault();
          setMsg(null);
          try {
            await apiClient.post('/financial/plans', {
              vehicle_id: Number(f.vehicle_id),
              period_start: f.period_start,
              period_end: f.period_end,
              revenue_target: Number(f.revenue_target),
              margin_target: Number(f.margin_target),
              distance_target: Number(f.distance_target),
            });
            setMsg('План создан');
            load();
          } catch (err: any) {
            setMsg(err && err.response && err.response.data && err.response.data.detail ? err.response.data.detail : 'Ошибка');
          }
        }}>
          <input className="auth-input" placeholder="ТС id" value={f.vehicle_id} onChange={(e) => setF({ ...f, vehicle_id: e.target.value })} />
          <input className="auth-input" type="date" value={f.period_start} onChange={(e) => setF({ ...f, period_start: e.target.value })} />
          <input className="auth-input" type="date" value={f.period_end} onChange={(e) => setF({ ...f, period_end: e.target.value })} />
          <input className="auth-input" placeholder="Выручка €" value={f.revenue_target} onChange={(e) => setF({ ...f, revenue_target: e.target.value })} />
          <input className="auth-input" placeholder="Маржа €" value={f.margin_target} onChange={(e) => setF({ ...f, margin_target: e.target.value })} />
          <input className="auth-input" placeholder="Пробег км" value={f.distance_target} onChange={(e) => setF({ ...f, distance_target: e.target.value })} />
          <button className="btn btn-primary" type="submit">Создать</button>
        </form>
        {msg && <p className="text-xs mt-2 text-muted">{msg}</p>}
      </div>
      <div className="card">
        <h2 className="text-lg font-medium mb-3">Планы</h2>
        {plans.length === 0 ? (
          <p className="text-muted">Нет планов</p>
        ) : (
          <table className="w-full text-sm">
            <thead><tr className="text-left text-muted"><th>ТС</th><th>Период</th><th>Выручка</th><th>Маржа</th><th>Пробег</th></tr></thead>
            <tbody>
              {plans.map((p) => (
                <tr key={p.id} className="border-t border-border">
                  <td className="py-2">{p.vehicle_id}</td>
                  <td>{p.period_start} — {p.period_end}</td>
                  <td>€{p.revenue_target}</td>
                  <td>€{p.margin_target}</td>
                  <td>{p.distance_target} км</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
};
