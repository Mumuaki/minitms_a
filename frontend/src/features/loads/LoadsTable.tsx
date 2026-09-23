import { useState, useRef } from 'react';
import { MapPin, EyeOff, CheckCircle, Contact } from 'lucide-react';
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
  description?: string;
  offer_url?: string;
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

const fmtWeight = (kg?: number | null) => {
  if (kg == null) return '';
  const t = kg / 1000;
  const s = t % 1 === 0 ? t.toFixed(0) : t.toFixed(3).replace(/0+$/, '').replace(/\.$/, '');
  return s + ' т';
};

const calcPrice = (c: Cargo): number | null => {
  if (c.price != null && c.price > 0) return c.price;
  const td = c.profitability?.total_distance;
  if (td != null && td > 0) return Math.round(td * 0.85);
  return null;
};

const desc = (c: Cargo) => {
  const parts: string[] = [];
  if (c.description) parts.push(c.description.slice(0, 60));
  if (c.body_type) parts.push(c.body_type.slice(0, 60));
  const w = fmtWeight(c.weight);
  if (w) parts.push(w);
  return parts.join(' · ');
};

const fmtRate = (r?: number | null) => (r != null ? r.toFixed(2) : '');

type SortKey = 'rate_per_km' | 'price' | 'loading_place' | 'unloading_place' | 'distance_trans_eu' | 'empty_run';

const NumInput = ({ value, onCommit, className }: { value: string; onCommit: (v: number) => void; className?: string }) => {
  const [draft, setDraft] = useState<string | null>(null);
  const shown = draft !== null ? draft : value;
  return (
    <input
      type="text"
      inputMode="decimal"
      className={'w-20 bg-transparent border border-transparent hover:border-border focus:border-blue-500 rounded px-1 py-0.5 text-right ' + (className || '')}
      value={shown}
      onChange={(e) => setDraft(e.target.value)}
      onClick={(e) => e.stopPropagation()}
      onBlur={() => {
        if (draft === null) return;
        const num = parseFloat(draft.replace(',', '.'));
        setDraft(null);
        if (!isNaN(num)) onCommit(num);
      }}
      onKeyDown={(e) => { if (e.key === 'Enter') (e.target as HTMLInputElement).blur(); }}
    />
  );
};

export const LoadsTable = ({ loads, isLoading, onSelect, onChanged }: LoadsTableProps) => {
  const [sortKey, setSortKey] = useState<SortKey>('rate_per_km');
  const [asc, setAsc] = useState(false);
  // Закреплённая (выбранная в работу) строка: не пересортировывается при изменении данных
  const [pinnedId, setPinnedId] = useState<string | null>(null);
  const pinnedIndex = useRef<number | null>(null);

  if (isLoading) return <div className="text-center p-4">Загрузка…</div>;
  if (loads.length === 0) return <div className="text-center p-4 text-muted">Нет грузов.</div>;

  const val = (c: Cargo, k: SortKey): any => {
    if (k === 'loading_place') return (c.loading_place && c.loading_place.country_code ? c.loading_place.country_code : 'zz') + ' ' + (c.loading_place ? c.loading_place.address : '');
    if (k === 'unloading_place') return (c.unloading_place && c.unloading_place.country_code ? c.unloading_place.country_code : 'zz') + ' ' + (c.unloading_place ? c.unloading_place.address : '');
    if (k === 'rate_per_km') return c.profitability && c.profitability.rate_per_km != null ? c.profitability.rate_per_km : -1;
    if (k === 'empty_run') return c.profitability && c.profitability.empty_run_km != null ? c.profitability.empty_run_km : -1;
    if (k === 'price') return calcPrice(c) != null ? calcPrice(c) : -1;
    return c[k] ?? '';
  };

  const compare = (a: Cargo, b: Cargo) => {
    const va = val(a, sortKey);
    const vb = val(b, sortKey);
    if (va < vb) return asc ? -1 : 1;
    if (va > vb) return asc ? 1 : -1;
    return 0;
  };

  const sorted = [...loads].sort(compare);

  // Закреплённая строка остаётся на своём месте до выбора другой строки
  if (pinnedId) {
    const idx = sorted.findIndex((c) => c.id === pinnedId);
    if (idx >= 0) {
      if (pinnedIndex.current == null) pinnedIndex.current = idx;
      if (idx !== pinnedIndex.current) {
        const [item] = sorted.splice(idx, 1);
        sorted.splice(Math.min(pinnedIndex.current, sorted.length), 0, item);
      }
    }
  }

  const pinRow = (id: string) => {
    const idx = sorted.findIndex((c) => c.id === id);
    pinnedIndex.current = idx >= 0 ? idx : null;
    setPinnedId(id);
  };

  const th = (key: SortKey, label: string) => (
    <th
      className="px-3 py-2 text-left font-medium cursor-pointer select-none whitespace-nowrap"
      onClick={() => {
        setPinnedId(null);
        pinnedIndex.current = null;
        if (sortKey === key) setAsc(!asc);
        else { setSortKey(key); setAsc(false); }
      }}
    >
      {label} {sortKey === key ? (asc ? '↑' : '↓') : ''}
    </th>
  );

  const act = async (e: React.MouseEvent, fn: () => Promise<void>) => {
    e.stopPropagation();
    try { await fn(); } catch { /* ignore */ }
    onChanged && onChanged();
  };

  const savePricing = async (load: Cargo, body: { price?: number; rate_per_km?: number }) => {
    // закрепить строку, чтобы она не «убегала» после пересчёта
    pinRow(load.id);
    try { await apiClient.patch('/cargos/' + load.id + '/pricing', body); } catch { /* ignore */ }
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
            {th('empty_run', 'Подача, км')}
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
            const isSelected = load.id === pinnedId;
            const shownPrice = calcPrice(load);
            const isCalc = !(load.price != null && load.price > 0) && shownPrice != null;
            const totalKm = load.profitability && load.profitability.total_distance != null ? load.profitability.total_distance : load.distance_trans_eu;
            return (
              <tr
                key={load.id}
                onClick={() => pinRow(load.id)}
                className={'hover:bg-black/5 dark:hover:bg-white/5' + (isSelected ? ' ring-2 ring-inset ring-blue-500' : '')}
                style={bg ? { backgroundColor: bg } : undefined}
              >
                <td className="px-3 py-2"><span style={{ display: 'inline-block', width: 12, height: 12, borderRadius: '50%', backgroundColor: dot }} /></td>
                <td className="px-3 py-2">{flagEmoji(load.loading_place && load.loading_place.country_code)} {load.loading_place ? load.loading_place.address : '—'}</td>
                <td className="px-3 py-2">{flagEmoji(load.unloading_place && load.unloading_place.country_code)} {load.unloading_place ? load.unloading_place.address : '—'}</td>
                <td className="px-3 py-2 text-muted">{desc(load)}</td>
                <td className="px-3 py-2 whitespace-nowrap">{load.loading_date || '—'}{load.unloading_date ? ' → ' + load.unloading_date : ''}</td>
                <td className="px-3 py-2 text-right">{totalKm != null ? totalKm.toFixed(0) : '—'}</td>
                <td className="px-3 py-2 text-right">{load.profitability && load.profitability.empty_run_km != null ? load.profitability.empty_run_km.toFixed(0) : '—'}</td>
                <td className="px-3 py-2 text-right font-bold">
                  <NumInput
                    value={shownPrice != null ? String(shownPrice) : ''}
                    onCommit={(v) => savePricing(load, { price: v })}
                  />
                  {isCalc && <span className="text-muted font-normal text-xs">(расч.)</span>}
                </td>
                <td className="px-3 py-2 text-right font-semibold">
                  <NumInput
                    value={fmtRate(load.profitability && load.profitability.rate_per_km)}
                    onCommit={(v) => savePricing(load, { rate_per_km: v })}
                  />
                </td>
                <td className="px-3 py-2">
                  <div className="flex gap-1">
                    <button
                      title="Показать на карте"
                      className="p-1 hover:bg-black/10 rounded"
                      onClick={(e) => { e.stopPropagation(); pinRow(load.id); onSelect && onSelect(load); }}
                    ><MapPin size={15} /></button>
                    <button
                      title="Контакт (карточка на Trans.eu)"
                      className="p-1 hover:bg-black/10 rounded"
                      onClick={(e) => {
                        e.stopPropagation();
                        // Карточка открывается в браузере скрапера (noVNC) — там активна сессия Trans.eu
                        window.open('http://89.167.70.67:6080', 'minitms_novnc');
                        apiClient.post('/scraping/open_offer', { url: load.offer_url || null }, { timeout: 120000 }).catch(() => {});
                      }}
                    ><Contact size={15} /></button>
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