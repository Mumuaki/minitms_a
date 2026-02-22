import { useState, useEffect } from 'react';
import { Navigation, RefreshCw, CheckCircle, XCircle, MapPin } from 'lucide-react';
import { apiClient } from '../../../infrastructure/api/client';

interface GpsStatus {
  connected: boolean;
  provider: string;
  url: string;
  vehicles_count: number;
  last_sync: string | null;
  message: string;
}

interface GpsVehicle {
  id: string;
  name: string;
  license_plate?: string;
  lat?: number;
  lon?: number;
  speed?: number;
  last_update?: string;
  status: string;
}

export const GpsPage = () => {
  const [status, setStatus] = useState<GpsStatus | null>(null);
  const [vehicles, setVehicles] = useState<GpsVehicle[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchGps = async () => {
    setLoading(true);
    setError(null);
    try {
      const [statusRes, vehiclesRes] = await Promise.all([
        apiClient.get<GpsStatus>('/gps/status'),
        apiClient.get<GpsVehicle[]>('/gps/vehicles'),
      ]);
      setStatus(statusRes.data);
      setVehicles(vehiclesRes.data ?? []);
    } catch (e: unknown) {
      const msg = e && typeof e === 'object' && 'response' in e
        ? (e as { response?: { data?: { detail?: string }; status?: number } }).response?.data?.detail
          || `HTTP ${(e as { response?: { status?: number } }).response?.status}`
        : String(e);
      setError(msg || 'Ошибка загрузки GPS');
      setStatus(null);
      setVehicles([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchGps();
  }, []);

  if (loading && !status) {
    return (
      <div className="page-container">
        <h1 className="text-2xl font-bold mb-6 flex items-center gap-2">
          <Navigation size={28} />
          GPS трекер
        </h1>
        <div className="card">
          <p className="text-muted">Загрузка...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="page-container">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold flex items-center gap-2">
          <Navigation size={28} />
          GPS трекер
        </h1>
        <button
          type="button"
          onClick={fetchGps}
          disabled={loading}
          className="btn btn-secondary flex items-center gap-2"
        >
          <RefreshCw size={18} className={loading ? 'animate-spin' : ''} />
          Обновить
        </button>
      </div>

      {error && (
        <div className="card border-l-4 border-red-500 bg-red-50 dark:bg-red-950/20 mb-6">
          <p className="text-red-600 dark:text-red-400">{error}</p>
        </div>
      )}

      {/* Статус подключения к API GPS */}
      {status && (
        <div className="card mb-6">
          <h2 className="text-lg font-semibold mb-4">Подключение к GPS API</h2>
          <div className="flex flex-wrap items-center gap-4">
            {status.connected ? (
              <span className="flex items-center gap-2 text-green-600 dark:text-green-400">
                <CheckCircle size={22} />
                Подключено
              </span>
            ) : (
              <span className="flex items-center gap-2 text-amber-600 dark:text-amber-400">
                <XCircle size={22} />
                Нет подключения
              </span>
            )}
            <span className="text-muted">{status.provider}</span>
            <span className="text-muted">ТС с трекерами: {status.vehicles_count}</span>
            {status.last_sync && (
              <span className="text-muted text-sm">
                Синхронизация: {new Date(status.last_sync).toLocaleString()}
              </span>
            )}
          </div>
          <p className="mt-2 text-muted text-sm">{status.message}</p>
          {!status.connected && (
            <p className="mt-2 text-sm text-amber-600 dark:text-amber-400">
              На сервере в <code className="bg-muted px-1 rounded">backend/.env</code> задайте
              GPS_DOZOR_USERNAME и GPS_DOZOR_PASSWORD (и при необходимости GPS_DOZOR_URL).
            </p>
          )}
        </div>
      )}

      {/* Список ТС с GPS */}
      <div className="card">
        <h2 className="text-lg font-semibold mb-4">Транспорт с трекерами ({vehicles.length})</h2>
        {vehicles.length === 0 ? (
          <p className="text-muted">
            Нет данных от GPS провайдера или учётные данные не настроены.
          </p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full border-collapse">
              <thead>
                <tr className="border-b border-border">
                  <th className="text-left py-2 px-2">Название</th>
                  <th className="text-left py-2 px-2">Гос. номер</th>
                  <th className="text-left py-2 px-2">Координаты</th>
                  <th className="text-left py-2 px-2">Скорость</th>
                  <th className="text-left py-2 px-2">Обновлено</th>
                  <th className="text-left py-2 px-2">Статус</th>
                </tr>
              </thead>
              <tbody>
                {vehicles.map((v) => (
                  <tr key={v.id} className="border-b border-border hover:bg-muted/50">
                    <td className="py-2 px-2">{v.name}</td>
                    <td className="py-2 px-2">{v.license_plate ?? '—'}</td>
                    <td className="py-2 px-2">
                      {v.lat != null && v.lon != null ? (
                        <span className="flex items-center gap-1">
                          <MapPin size={14} />
                          {v.lat.toFixed(5)}, {v.lon.toFixed(5)}
                        </span>
                      ) : (
                        '—'
                      )}
                    </td>
                    <td className="py-2 px-2">{v.speed != null ? `${v.speed} км/ч` : '—'}</td>
                    <td className="py-2 px-2">
                      {v.last_update
                        ? new Date(v.last_update).toLocaleString()
                        : '—'}
                    </td>
                    <td className="py-2 px-2">{v.status}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
};
