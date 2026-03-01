import { useState, useEffect } from 'react';
import { RefreshCw } from 'lucide-react';
import { LoadsTable } from './LoadsTable';
import { apiClient } from '../../infrastructure/api/client';

const fetchLoads = async () => {
  const response = await apiClient.get('/cargos/search', { params: { limit: 50 } });
  return response.data;
};

export const LoadsPage = () => {
  const [loads, setLoads] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const loadData = async () => {
    setLoading(true);
    try {
      const data = await fetchLoads();
      setLoads(data.items || []);
      setError(null);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  return (
    <div className="page-container">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-bold">Грузы</h1>
        <button
          onClick={loadData}
          disabled={loading}
          className="btn btn-primary flex items-center gap-2"
        >
          <RefreshCw size={16} className={loading ? 'animate-spin' : ''} />
          Обновить
        </button>
      </div>

      {error && (
        <div className="mb-4 p-3 bg-red-50 dark:bg-red-950/30 border border-red-300 dark:border-red-700 rounded-lg text-sm text-red-700 dark:text-red-300">
          {error}
        </div>
      )}

      {!loading && loads.length === 0 && !error && (
        <div className="card text-center py-10">
          <p className="text-muted text-lg mb-2">Грузы не найдены</p>
          <p className="text-sm text-gray-500">Перейдите в раздел "Автопарк" и нажмите "Искать груз" на карточке ТС</p>
        </div>
      )}

      <LoadsTable loads={loads} isLoading={loading} />
    </div>
  );
};
