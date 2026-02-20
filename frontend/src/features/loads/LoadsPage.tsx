import { useState, useEffect } from 'react';
import { LoadsTable } from './LoadsTable';
import { apiClient } from '../../infrastructure/api/client';

// Загрузка грузов через apiClient (относительный URL, проксируется через Nginx)
const fetchLoads = async () => {
  const response = await apiClient.get('/cargos/search', { params: { limit: 50 } });
  return response.data;
};

// Импорт грузов из Trans.eu через apiClient
const importLoads = async () => {
  const params = {
    loading: 'PL, Warszawa',
    unloading: 'DE, Berlin',
    weight_to: '24',
    loading_radius: '50',
    unloading_radius: '50'
  };

  const response = await apiClient.post('/cargos/import_trans_eu', null, { params });
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

  const handleImport = async () => {
    setLoading(true);
    try {
      await importLoads();
      await loadData(); // Reload from DB
    } catch (err: any) {
      setError("Import Error: " + err.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  return (
    <div className="p-6">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-bold text-gray-800">Available Loads</h1>
        <div className="space-x-4">
          <button
            onClick={loadData}
            className="px-4 py-2 bg-gray-200 text-gray-700 rounded hover:bg-gray-300"
          >
            Refresh
          </button>
          <button
            onClick={handleImport}
            className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
          >
            Import from Trans.eu (Test)
          </button>
        </div>
      </div>

      {error && (
        <div className="mb-4 p-4 bg-red-100 text-red-700 rounded">
          {error}
        </div>
      )}

      <LoadsTable loads={loads} isLoading={loading} />
    </div>
  );
};
