import { useState, useEffect } from 'react';
import { useLanguage } from '@/contexts/LanguageContext';
import { RefreshCw, Search, ChevronDown, ChevronUp, Save } from 'lucide-react';
import { LoadsTable } from './LoadsTable';
import { Modal } from '@/components/ui/Modal';
import { apiClient } from '../../infrastructure/api/client';

const fetchLoads = async () => {
  const response = await apiClient.get('/cargos/search', { params: { limit: 50 } });
  return response.data;
};

interface SearchFormData {
  loading: string;
  unloading: string;
  loading_radius: number;
  unloading_radius: number;
  weight_to: string;
  length_to: string;
}

const INITIAL_SEARCH: SearchFormData = {
  loading: '',
  unloading: '',
  loading_radius: 75,
  unloading_radius: 75,
  weight_to: '24.0',
  length_to: '13.6',
};

const SAVED_FILTERS_KEY = 'minitms.loads.searchFilters';

export const LoadsPage = () => {
  const { t } = useLanguage();
  const [loads, setLoads] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [searchForm, setSearchForm] = useState<SearchFormData>(INITIAL_SEARCH);
  const [isSearching, setIsSearching] = useState(false);
  const [searchError, setSearchError] = useState<string | null>(null);
  const [isFormOpen, setIsFormOpen] = useState(true);
  const [filtersSaved, setFiltersSaved] = useState(false);
  const [selectedCargo, setSelectedCargo] = useState<any | null>(null);
  const [countryFilter, setCountryFilter] = useState<string>('all');

  const loadData = async () => {
    setLoading(true);
    try {
      const data = await fetchLoads();
      setLoads(data.items || []);
      setError(null);
      // Сворачиваем форму, если грузы есть
      if ((data.items || []).length > 0) {
        setIsFormOpen(false);
      }
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  // Восстановление сохранённых фильтров (FR-UI-005)
  useEffect(() => {
    try {
      const raw = localStorage.getItem(SAVED_FILTERS_KEY);
      if (!raw) return;
      const parsed = JSON.parse(raw);
      setSearchForm({
        loading: String(parsed.loading ?? ''),
        unloading: String(parsed.unloading ?? ''),
        loading_radius: Number(parsed.loading_radius ?? 75),
        unloading_radius: Number(parsed.unloading_radius ?? 75),
        weight_to: String(parsed.weight_to ?? '24.0'),
        length_to: String(parsed.length_to ?? '13.6'),
      });
    } catch {
      // повреждённые данные игнорируем
    }
  }, []);

  const handleSearchInput = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setSearchForm(prev => ({ ...prev, [name]: value }));
  };

  const handleSaveFilters = () => {
    localStorage.setItem(SAVED_FILTERS_KEY, JSON.stringify(searchForm));
    setFiltersSaved(true);
    window.setTimeout(() => setFiltersSaved(false), 2000);
  };

  const countryCodes = Array.from(
    new Set(
      loads.flatMap((c: any) => [
        c.loading_place?.country_code,
        c.unloading_place?.country_code,
      ]).filter(Boolean)
    )
  ).sort();

  const filteredLoads = countryFilter === 'all'
    ? loads
    : loads.filter((c: any) =>
        c.loading_place?.country_code === countryFilter ||
        c.unloading_place?.country_code === countryFilter
      );

  const handleSearchSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    // Полуавтоматический режим: оператор вручную выполняет поиск в удалённом браузере,
    // а скрапер автоматически парсит и сохраняет результат.
    setIsSearching(true);
    setSearchError(null);

    try {
      // Открываем удалённый браузер (noVNC) в новой вкладке
      window.open('http://89.167.70.67:6080', '_blank');

      await apiClient.post('/scraping/import_trans_eu_manual', null, {
        params: { timeout_seconds: 600 },
        timeout: 650000, // до 10 минут — ручной поиск оператором
      });

      // После импорта — обновляем таблицу
      await loadData();
    } catch (err: any) {
      const detail = err?.response?.data?.detail;
      setSearchError(detail ? String(detail) : `Ошибка импорта: ${err.message}`);
    } finally {
      setIsSearching(false);
    }
  };

  return (
    <div className="page-container">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-bold">{t('loads')}</h1>
        <button
          onClick={loadData}
          disabled={loading}
          className="btn btn-primary flex items-center gap-2"
        >
          <RefreshCw size={16} className={loading ? 'animate-spin' : ''} />
          Обновить
        </button>
      </div>

      {/* Форма поиска грузов на Trans.eu */}
      <div className="card mb-6">
        <button
          type="button"
          onClick={() => setIsFormOpen(!isFormOpen)}
          className="w-full flex items-center justify-between text-left"
        >
          <div className="flex items-center gap-2">
            <Search size={20} className="text-blue-500" />
            <span className="font-semibold text-lg">Поиск грузов на Trans.eu</span>
          </div>
          {isFormOpen ? <ChevronUp size={20} /> : <ChevronDown size={20} />}
        </button>

        {isFormOpen && (
          <form onSubmit={handleSearchSubmit} className="mt-4 space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium mb-1">Загрузка (город) *</label>
                <input
                  type="text"
                  name="loading"
                  className="input w-full"
                  placeholder="Например: München, Warszawa"
                  value={searchForm.loading}
                  onChange={handleSearchInput}
                  required
                />
              </div>
              <div>
                <label className="block text-sm font-medium mb-1">Выгрузка (город)</label>
                <input
                  type="text"
                  name="unloading"
                  className="input w-full"
                  placeholder="Оставьте пустым для любого"
                  value={searchForm.unloading}
                  onChange={handleSearchInput}
                />
              </div>
            </div>

            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div>
                <label className="block text-sm font-medium mb-1">Радиус загр. (км)</label>
                <input
                  type="number"
                  name="loading_radius"
                  className="input w-full"
                  value={searchForm.loading_radius}
                  onChange={handleSearchInput}
                  min={0}
                  max={500}
                />
              </div>
              <div>
                <label className="block text-sm font-medium mb-1">Радиус выгр. (км)</label>
                <input
                  type="number"
                  name="unloading_radius"
                  className="input w-full"
                  value={searchForm.unloading_radius}
                  onChange={handleSearchInput}
                  min={0}
                  max={500}
                />
              </div>
              <div>
                <label className="block text-sm font-medium mb-1">Макс. вес (т)</label>
                <input
                  type="text"
                  name="weight_to"
                  inputMode="decimal"
                  className="input w-full"
                  placeholder="24.0"
                  value={searchForm.weight_to}
                  onChange={handleSearchInput}
                />
              </div>
              <div>
                <label className="block text-sm font-medium mb-1">Макс. длина (м)</label>
                <input
                  type="text"
                  name="length_to"
                  inputMode="decimal"
                  className="input w-full"
                  placeholder="13.6"
                  value={searchForm.length_to}
                  onChange={handleSearchInput}
                />
              </div>
            </div>

            {searchError && (
              <div className="p-3 bg-red-50 dark:bg-red-950/30 border border-red-300 dark:border-red-700 rounded-lg text-sm text-red-700 dark:text-red-300">
                {searchError}
              </div>
            )}

            <div className="flex justify-end gap-3">
              <button
                type="button"
                onClick={handleSaveFilters}
                className="btn flex items-center gap-2"
                title="Сохранить фильтры"
              >
                <Save size={16} />
                {filtersSaved ? 'Сохранено' : 'Сохранить фильтры'}
              </button>
              <button
                type="submit" 
                disabled={isSearching}
                className="btn bg-green-600 text-white hover:bg-green-700 disabled:opacity-60 disabled:cursor-wait flex items-center gap-2 px-6"
              >
                <Search size={16} className={isSearching ? 'animate-spin' : ''} />
                {isSearching ? 'Ждём поиск в браузере... (до 10 мин)' : 'Импорт из Trans.eu'}
              </button>
            </div>
          </form>
        )}
      </div>

      {error && (
        <div className="mb-4 p-3 bg-red-50 dark:bg-red-950/30 border border-red-300 dark:border-red-700 rounded-lg text-sm text-red-700 dark:text-red-300">
          {error}
        </div>
      )}

      {loads.length > 0 && (
        <div className="flex items-center gap-2 mb-4">
          <label className="text-sm font-medium">Страна:</label>
          <select
            className="input w-auto"
            value={countryFilter}
            onChange={(e) => setCountryFilter(e.target.value)}
          >
            <option value="all">Все</option>
            {countryCodes.map((cc) => <option key={cc} value={cc}>{cc}</option>)}
          </select>
        </div>
      )}

      {!loading && loads.length === 0 && !error && (
        <div className="card text-center py-10">
          <p className="text-muted text-lg mb-2">Грузы не найдены</p>
          <p className="text-sm text-gray-500">Заполните форму выше и нажмите «Запустить поиск», или перейдите в раздел «Автопарк» и нажмите «Искать груз» на карточке ТС</p>
        </div>
      )}

      <LoadsTable loads={filteredLoads} isLoading={loading} onSelect={setSelectedCargo} onChanged={loadData} />

      <Modal isOpen={!!selectedCargo} onClose={() => setSelectedCargo(null)} title="Детали груза">
        {selectedCargo && (
          <div className="space-y-2 text-sm">
            <p><b>Заявка:</b> {selectedCargo.external_id || '—'}</p>
            <p><b>Загрузка:</b> {selectedCargo.loading_place?.address || '—'} ({selectedCargo.loading_place?.country_code || '—'})</p>
            <p><b>Выгрузка:</b> {selectedCargo.unloading_place?.address || '—'} ({selectedCargo.unloading_place?.country_code || '—'})</p>
            <p><b>Дата загрузки:</b> {selectedCargo.loading_date || '—'}</p>
            <p><b>Дата выгрузки:</b> {selectedCargo.unloading_date || '—'}</p>
            <p><b>Вес:</b> {selectedCargo.weight != null ? selectedCargo.weight + ' кг' : '—'}</p>
            <p><b>Тип кузова:</b> {selectedCargo.body_type || '—'}</p>
            <p><b>Дистанция Trans.eu:</b> {selectedCargo.distance_trans_eu || '—'} км</p>
            <p><b>Дистанция OSM:</b> {selectedCargo.distance_osm || '—'} км</p>
            <p><b>Ставка €/км:</b> {selectedCargo.profitability?.rate_per_km != null ? selectedCargo.profitability.rate_per_km.toFixed(2) : '—'}</p>
            <p><b>Цена:</b> {selectedCargo.price || '—'} €</p>
          </div>
        )}
      </Modal>
    </div>
  );
};