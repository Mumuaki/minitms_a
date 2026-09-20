import { useState } from 'react';

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
  profitability?: { rate_per_km: number | null; color_code: string };
}

interface LoadsTableProps {
  loads: Cargo[];
  isLoading: boolean;
  onSelect?: (cargo: Cargo) => void;
}

const COLOR: Record<string, string> = { RED: '#fecaca', GRAY: '#e5e7eb', YELLOW: '#fef08a', GREEN: '#bbf7d0' };

type SortKey = 'external_id' | 'loading_place' | 'unloading_place' | 'loading_date' | 'weight' | 'price' | 'distance_trans_eu' | 'rate_per_km';

export const LoadsTable = ({ loads, isLoading, onSelect }: LoadsTableProps) => {
  const [sortKey, setSortKey] = useState<SortKey>('price');
  const [asc, setAsc] = useState(false);

  if (isLoading) {
    return <div className="text-center p-4">Загрузка…</div>;
  }
  if (loads.length === 0) {
    return <div className="text-center p-4 text-muted">Нет грузов. Запустите импорт из Trans.eu.</div>;
  }

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
      className="px-4 py-2 text-left font-medium cursor-pointer select-none"
      onClick={() => {
        if (sortKey === key) setAsc(!asc);
        else { setSortKey(key); setAsc(false); }
      }}
    >
      {label} {sortKey === key ? (asc ? '↑' : '↓') : ''}
    </th>
  );

  return (
    <div className="overflow-x-auto rounded-lg border border-border shadow-sm">
      <table className="min-w-full divide-y divide-border text-sm">
        <thead className="bg-card">
          <tr>
            {th('external_id', 'Заявка')}
            {th('loading_place', 'Загрузка')}
            {th('unloading_place', 'Выгрузка')}
            {th('loading_date', 'Дата')}
            {th('weight', 'Вес')}
            {th('distance_trans_eu', 'Дист. (км)')}
            {th('rate_per_km', '€/км')}
            {th('price', 'Цена (€)')}
          </tr>
        </thead>
        <tbody className="divide-y divide-border">
          {sorted.map((load) => {
            const cc = load.profitability ? load.profitability.color_code : undefined;
            const bg = cc ? COLOR[cc] : undefined;
            return (
              <tr
                key={load.id}
                style={bg ? { backgroundColor: bg } : undefined}
                onClick={() => onSelect && onSelect(load)}
                className="cursor-pointer hover:bg-black/5 dark:hover:bg-white/5"
              >
                <td className="px-4 py-2 font-medium">{load.external_id}</td>
                <td className="px-4 py-2">{load.loading_place ? load.loading_place.address : '—'}</td>
                <td className="px-4 py-2">{load.unloading_place ? load.unloading_place.address : '—'}</td>
                <td className="px-4 py-2">{load.loading_date || '—'}</td>
                <td className="px-4 py-2">{load.weight != null ? load.weight + ' кг' : '—'}</td>
                <td className="px-4 py-2 text-right">{load.distance_trans_eu || '—'}</td>
                <td className="px-4 py-2 text-right font-semibold">{load.profitability && load.profitability.rate_per_km != null ? load.profitability.rate_per_km.toFixed(2) : '—'}</td>
                <td className="px-4 py-2 text-right font-bold">{load.price || '—'}</td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
};
