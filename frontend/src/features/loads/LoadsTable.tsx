import { useState } from 'react';
import { MapPin, EyeOff, CheckCircle } from 'lucide-react';
import { apiClient } from '../../infrastructure/api/client';

interface Cargo {
  id: string;
  external_id: string;
  loading_place?: { address: string; country_code: string };
  unloading_place?: { address: string; country_code: string };
  loading_date: string;
  unloading_date?: string;
  weight: number;
  body_type: string;
  price: number;
  distance_trans_eu: number;
  distance_osm?: number;
  profitability?: { rate_per_km: number | null; empty_run_km?: number | null; total_distance?: number | null; color_code: string };
}

interface LoadsTableProps {
  loads: Cargo[];
  isLoading: boolean;
  onSelect?: (cargo: Cargo) => void;
  onChanged?: () => void;
}

const DOT_COLOR: Record<string, string> = { RED: '#FF4444', GRAY: '#9E9E9E', YELLOW: '#FFEB3B', GREEN: '#4CAF50' };
const ROW_BG: Record<string, string> = { RED: '#ffecec', GRAY: '#f3f3f3', YELLOW: '#fffbe6', GREEN: '#e6f5e6' };

const flagEmoji = (cc?: string) => {
  if (!cc) return '';
  return [...cc.toUpperCase()].map((c) => String.fromCodePoint(127397 + c.charCodeAt(0))).join('');
};

const desc = (bt?: string) => (bt ? bt.slice(0, 80) : '');

type SortKey = 'rate_per_km' | 'price' | 'loading_place' | 'unloading_place' | 'distance_trans_eu';

export const LoadsTable = ({ loads, isLoading, onSelect, onChanged }: LoadsTableProps) => {
  const [sortKey, setSortKey] = useState<SortKey>('rate_per_km');
  const [asc, setAsc] = useState(false);

  if (isLoading) return <div className="text-center p-4">Загрузка…</div>;
  if (loads.length === 0) return <div className="text-center p-4 text-muted">Нет грузов.</div>;

  const val = (c: Cargo, k: SortKey): any => {
    if (k === 'loading_place') return c.loading_place ? c.loading_place.address : '';
    if (k === 'unloading_place') return c.unloading_place ? c.unloading_place.address : '';
    if (k === 'rate_per_km') return c.profitability && c.profitability.rate_per_km != null ? c.profitability.rate_per_km : 0;
    return c[k] ?? '';
  };

  const sorted = [...loads].sort((a, b) => {
    const va = val(a, sortKey);
    const vb = val(b, sortKey);
    if (va < vb) return asc ? -1 : 1;
    if (va > vb) return asc ? 1 : -1;
    return 0;
  });

  const th = (key: SortKey, label: string) => (
    <th
      className="px-3 py-2 text-left font-medium cursor-pointer select-none whitespace-nowrap"
      onClick={() => { if (sortKey === key) setAsc(!asc); else { setSortKey(key); setAsc(false); } }}
    >
      {label} {sortKey === key ? (asc ? '↑' : '↓') : ''}
    </th>
  );

  const act = async (e: React.MouseEvent, fn: () => Promise<void>) => {
    e.stopPropagation();
    try { await fn(); } catch { /* ignore */ }
    onChanged && onChanged();
  };

  return (
    <div className="overflow-x-auto rounded-lg border border-border shadow-sm">
      <table className="min-w-full divide-y divide-border text-sm">
        <thead className="bg-card">
          <tr>
            <th className="px-3 py-2 text-left font-medium">Рент.</th>
            {th('loading_place', 'Загрузка')}
            {th('unloading_place', 'Выгрузка')}
            <th className="px-3 py-2 text-left font-medium">Описание</th>
            <th className="px-3 py-2 text-left font-medium">Даты</th>
            {th('distance_trans_eu', 'Дист. (км)')}
            <th className="px-3 py-2 text-left font-medium">Подача, км</th>
            {th('price', 'Цена (€)')}
            {th('rate_per_km', '€/км')}
            <th className="px-3 py-2 text-left font-medium">Действия</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-border">
          {sorted.map((load) => {
            const cc = load.profitability ? load.profitability.color_code : undefined;
            const dot = cc ? DOT_COLOR[cc] : '#9E9E9E';
            const bg = cc ? ROW_BG[cc] : undefined;
            return (
              <tr key={load.id} onClick={() => onSelect && onSelect(load)} className="cursor-pointer hover:bg-black/5 dark:hover:bg-white/5" style={bg ? { backgroundColor: bg } : undefined}>
                <td className="px-3 py-2"><span style={{ display: 'inline-block', width: 12, height: 12, borderRadius: '50%', backgroundColor: dot }} /></td>
                <td className="px-3 py-2">{flagEmoji(load.loading_place && load.loading_place.country_code)} {load.loading_place ? load.loading_place.address : '—'}</td>
                <td className="px-3 py-2">{flagEmoji(load.unloading_place && load.unloading_place.country_code)} {load.unloading_place ? load.unloading_place.address : '—'}</td>
                <td className="px-3 py-2 text-muted">{desc(load.body_type)}</td>
                <td className="px-3 py-2 whitespace-nowrap">{load.loading_date || '—'}{load.unloading_date ? ' → ' + load.unloading_date : ''}</td>
                <td className="px-3 py-2 text-right">{load.profitability && load.profitability.total_distance != null ? load.profitability.total_distance.toFixed(0) : (load.distance_trans_eu || '—')}</td>
                <td className="px-3 py-2 text-right">{load.profitability && load.profitability.empty_run_km != null ? load.profitability.empty_run_km.toFixed(0) : '—'}</td>
                <td className="px-3 py-2 text-right font-bold">{load.price || '—'}</td>
                <td className="px-3 py-2 text-right font-semibold">{load.profitability && load.profitability.rate_per_km != null ? load.profitability.rate_per_km.toFixed(2) : '—'}</td>
                <td className="px-3 py-2">
                  <div className="flex gap-1">
                    <button title="Открыть на карте" className="p-1 hover:bg-black/10 rounded" onClick={(e) => { e.stopPropagation(); onSelect && onSelect(load); }}><MapPin size={15} /></button>
                    <button title="Скрыть" className="p-1 hover:bg-black/10 rounded" onClick={(e) => act(e, () => apiClient.patch('/cargos/' + load.id + '/hide'))}><EyeOff size={15} /></button>
                    <button title="Принять (создать заказ)" className="p-1 hover:bg-black/10 rounded" onClick={(e) => act(e, () => apiClient.post('/cargos/' + load.id + '/accept'))}><CheckCircle size={15} /></button>
                  </div>
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
};
