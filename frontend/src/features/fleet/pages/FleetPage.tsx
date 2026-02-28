import React, { useState, useEffect } from 'react';
import { Plus, Truck, Pencil, Trash2, AlertCircle, MapPin, Clock, RefreshCw, Search } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { apiClient } from '../../../infrastructure/api/client';
import { Modal } from '../../../components/ui/Modal';

interface Vehicle {
  id: number;
  license_plate: string;
  vehicle_type: string;
  status: string;
  length: number;
  width: number;
  height: number;
  payload_capacity: number;
  gps_tracker_id?: string;
  current_location?: string;
  gps_last_updated?: string;
}

interface VehicleFormData {
  license_plate: string;
  vehicle_type: string;
  length: number | string;
  width: number | string;
  height: number | string;
  payload_capacity: number | string;
  gps_tracker_id: string;
}

const INITIAL_FORM_DATA: VehicleFormData = {
  license_plate: '',
  vehicle_type: 'Tent',
  length: 13.6,
  width: 2.45,
  height: 2.7,
  payload_capacity: 24000,
  gps_tracker_id: ''
};

const sendFleetDebugLog = (hypothesisId: string, message: string, data: Record<string, unknown>) => {
  // #region agent log
  fetch('http://127.0.0.1:7242/ingest/36d7308b-c83b-4ca3-aaa5-521e1668a539', { method: 'POST', headers: { 'Content-Type': 'application/json', 'X-Debug-Session-Id': 'fa2d8a' }, body: JSON.stringify({ sessionId: 'fa2d8a', runId: 'gps-refresh-button', hypothesisId, location: 'FleetPage.tsx:sendFleetDebugLog', message, data, timestamp: Date.now() }) }).catch(() => { });
  // #endregion
};

export const FleetPage = () => {
  const [vehicles, setVehicles] = useState<Vehicle[]>([]);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [isDeleteModalOpen, setIsDeleteModalOpen] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [editingVehicle, setEditingVehicle] = useState<Vehicle | null>(null);
  const [deletingVehicle, setDeletingVehicle] = useState<Vehicle | null>(null);
  const [refreshingLocationId, setRefreshingLocationId] = useState<number | null>(null);
  const [searchingCargoId, setSearchingCargoId] = useState<number | null>(null);
  const [locationError, setLocationError] = useState<string | null>(null);
  const navigate = useNavigate();

  // Form state
  const [formData, setFormData] = useState<VehicleFormData>(INITIAL_FORM_DATA);

  useEffect(() => {
    loadVehicles();
  }, []);

  const loadVehicles = async () => {
    setIsLoading(true);
    try {
      const response = await apiClient.get('/fleet/');
      console.log('Vehicles loaded:', response.data);
      setVehicles(response.data);
    } catch (error) {
      console.error('Failed to load vehicles', error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    const { name, value } = e.target;
    // Don't cast to Number immediately to allow empty string (clearing input)
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
  };

  const openAddModal = () => {
    setEditingVehicle(null);
    setFormData(INITIAL_FORM_DATA);
    setIsModalOpen(true);
  };

  const openEditModal = (vehicle: Vehicle) => {
    setEditingVehicle(vehicle);
    setFormData({
      license_plate: vehicle.license_plate,
      vehicle_type: vehicle.vehicle_type,
      length: vehicle.length,
      width: vehicle.width,
      height: vehicle.height,
      payload_capacity: vehicle.payload_capacity,
      gps_tracker_id: vehicle.gps_tracker_id || ''
    });
    setIsModalOpen(true);
  };

  const openDeleteModal = (vehicle: Vehicle) => {
    setDeletingVehicle(vehicle);
    setIsDeleteModalOpen(true);
  };

  const refreshVehicleLocation = async (vehicleId: number) => {
    const vehicleBefore = vehicles.find(v => v.id === vehicleId);
    // #region agent log
    sendFleetDebugLog('H1', 'refresh click', {
      vehicleId,
      hasTracker: Boolean(vehicleBefore?.gps_tracker_id),
      trackerId: vehicleBefore?.gps_tracker_id || null,
      locationBefore: vehicleBefore?.current_location || null
    });
    // #endregion
    setRefreshingLocationId(vehicleId);
    setLocationError(null);
    try {
      const { data } = await apiClient.post<Vehicle>(`/fleet/${vehicleId}/refresh-location`);
      // #region agent log
      sendFleetDebugLog('H2', 'refresh api success', {
        vehicleId,
        locationAfter: data?.current_location || null,
        gpsLastUpdated: data?.gps_last_updated || null
      });
      // #endregion
      setVehicles(prev => prev.map(v => v.id === vehicleId ? data : v));
      if (!data?.current_location) {
        setLocationError(`GPS не вернул локацию для ТС #${vehicleId}. Проверьте GPS Tracker ID и подключение к GPS провайдеру.`);
      }
    } catch (err: any) {
      console.error('Failed to refresh location', err);
      // #region agent log
      sendFleetDebugLog('H3', 'refresh api error', {
        vehicleId,
        error: err instanceof Error ? err.message : String(err)
      });
      // #endregion
      const detail = err?.response?.data?.detail;
      setLocationError(detail ? String(detail) : 'Ошибка при обновлении GPS локации');
    } finally {
      setRefreshingLocationId(null);
    }
  };

  const searchCargo = async (vehicle: Vehicle) => {
    if (!vehicle.current_location) {
      setLocationError(`ТС ${vehicle.license_plate}: нет GPS-локации. Сначала обновите местоположение.`);
      return;
    }
    setSearchingCargoId(vehicle.id);
    setLocationError(null);
    try {
      const weightTo = ((vehicle.payload_capacity || 24000) / 1000).toFixed(1);
      const lengthTo = vehicle.length.toString();
      await apiClient.post('/cargos/import_trans_eu', null, {
        params: {
          loading: vehicle.current_location,
          unloading: '',
          weight_to: weightTo,
          length_to: lengthTo,
          loading_radius: 75,
          unloading_radius: 75,
        },
        timeout: 120000,
      });
      navigate('/loads');
    } catch (err: any) {
      const detail = err?.response?.data?.detail;
      setLocationError(
        `Ошибка поиска грузов для ${vehicle.license_plate}: ${detail || err.message}`
      );
    } finally {
      setSearchingCargoId(null);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    // Helper to safe parse numbers (handling comma vs dot)
    const parseNumber = (value: string | number) => {
      if (typeof value === 'number') return value;
      const normalized = value.toString().replace(',', '.');
      const parsed = parseFloat(normalized);
      return isNaN(parsed) ? 0 : parsed;
    };

    // Prepare payload
    const payload = {
      ...formData,
      length: parseNumber(formData.length),
      width: parseNumber(formData.width),
      height: parseNumber(formData.height),
      payload_capacity: parseNumber(formData.payload_capacity),
      // Convert empty string to null for optional field
      gps_tracker_id: formData.gps_tracker_id.trim() === '' ? null : formData.gps_tracker_id.trim()
    };

    try {
      if (editingVehicle) {
        await apiClient.put(`/fleet/${editingVehicle.id}`, payload);
      } else {
        await apiClient.post('/fleet/', payload);
      }
      setIsModalOpen(false);
      loadVehicles();
    } catch (error: any) {
      console.error('Failed to save vehicle', error);
      const message = error.response?.data?.detail
        ? (typeof error.response.data.detail === 'object'
          ? JSON.stringify(error.response.data.detail)
          : error.response.data.detail)
        : 'Ошибка при сохранении транспорта';
      alert(`Ошибка: ${message}`);
    }
  };

  const handleDelete = async () => {
    if (!deletingVehicle) return;
    try {
      await apiClient.delete(`/fleet/${deletingVehicle.id}`);
      setIsDeleteModalOpen(false);
      setDeletingVehicle(null);
      loadVehicles();
    } catch (error) {
      console.error('Failed to delete vehicle', error);
      alert('Ошибка при удалении транспорта');
    }
  };

  return (
    <div className="page-container">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-bold">Автопарк</h1>
        <button
          className="btn btn-primary flex items-center gap-2"
          onClick={openAddModal}
        >
          <Plus size={20} />
          Добавить ТС
        </button>
      </div>

      {isLoading ? (
        <div className="text-center py-10">Загрузка...</div>
      ) : vehicles.length === 0 ? (
        <div className="card text-center py-10">
          <Truck size={48} className="mx-auto text-gray-400 mb-4" />
          <p className="text-muted text-lg">Автопарк пуст</p>
          <p className="text-sm text-gray-500 mb-4">Добавьте ваше первое транспортное средство</p>
          <button
            className="btn btn-primary"
            onClick={openAddModal}
          >
            Добавить ТС
          </button>
        </div>
      ) : (
        <>
          {locationError && (
            <div className="mb-4 p-3 bg-amber-50 dark:bg-amber-950/30 border border-amber-300 dark:border-amber-700 rounded-lg flex items-start gap-2 text-sm text-amber-800 dark:text-amber-300">
              <AlertCircle size={16} className="shrink-0 mt-0.5" />
              <span>{locationError}</span>
              <button onClick={() => setLocationError(null)} className="ml-auto text-amber-500 hover:text-amber-700 shrink-0">✕</button>
            </div>
          )}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {vehicles.map(vehicle => (
              <div key={vehicle.id} className="card hover:shadow-md transition-shadow group relative">
                <div className="absolute top-2 right-2 flex gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                  <button
                    onClick={() => openEditModal(vehicle)}
                    className="p-1.5 text-gray-500 hover:text-blue-600 hover:bg-blue-50 rounded"
                    title="Редактировать"
                  >
                    <Pencil size={16} />
                  </button>
                  <button
                    onClick={() => openDeleteModal(vehicle)}
                    className="p-1.5 text-gray-500 hover:text-red-600 hover:bg-red-50 rounded"
                    title="Удалить"
                  >
                    <Trash2 size={16} />
                  </button>
                </div>

                <div className="flex justify-between items-start mb-4 pr-16">
                  <div className="flex items-center gap-3">
                    <div className="p-2 bg-blue-100 dark:bg-blue-900 rounded-lg text-blue-600 dark:text-blue-300">
                      <Truck size={24} />
                    </div>
                    <div>
                      <h3 className="font-bold text-lg">{vehicle.license_plate}</h3>
                      <span className="text-xs text-muted">{vehicle.vehicle_type}</span>
                    </div>
                  </div>
                  <span className={`px-2 py-1 rounded text-xs font-medium ${vehicle.status === 'Free' ? 'bg-green-100 text-green-800' :
                      vehicle.status === 'In Transit' ? 'bg-blue-100 text-blue-800' :
                        'bg-gray-100 text-gray-800'
                    }`}>
                    {vehicle.status === 'Free' ? 'Свободен' :
                      vehicle.status === 'In Transit' ? 'В рейсе' : vehicle.status}
                  </span>
                </div>

                <div className="space-y-2 text-sm">
                  <div className="flex justify-between">
                    <span className="text-muted">Габариты (ДxШxВ):</span>
                    <span className="font-medium">{vehicle.length} x {vehicle.width} x {vehicle.height} м</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-muted">Грузоподъёмность:</span>
                    <span className="font-medium">{(vehicle.payload_capacity / 1000).toFixed(1)} т</span>
                  </div>
                  {vehicle.gps_tracker_id ? (
                    <div className="mt-3 pt-3 border-t border-gray-100 dark:border-gray-700 space-y-1">
                      <div className="flex justify-between items-center text-xs">
                        <span className="text-muted flex items-center gap-1">
                          <div className="w-2 h-2 rounded-full bg-green-500 animate-pulse"></div>
                          GPS ID: {vehicle.gps_tracker_id}
                        </span>
                        <button
                          type="button"
                          onClick={() => refreshVehicleLocation(vehicle.id)}
                          disabled={refreshingLocationId === vehicle.id}
                          className="flex items-center gap-1 px-2 py-1 text-xs text-gray-600 hover:text-blue-600 hover:bg-blue-50 dark:text-gray-400 dark:hover:bg-blue-900/30 rounded border border-gray-200 dark:border-gray-600"
                          title="Обновить локацию из GPS"
                        >
                          <RefreshCw size={14} className={refreshingLocationId === vehicle.id ? 'animate-spin shrink-0' : 'shrink-0'} />
                          <span>Обновить</span>
                        </button>
                      </div>
                      {vehicle.current_location && (
                        <div className="flex items-start gap-1.5 text-xs mt-1">
                          <MapPin size={14} className="text-blue-500 shrink-0 mt-0.5" />
                          <span className="font-medium text-gray-700 dark:text-gray-300">{vehicle.current_location}</span>
                        </div>
                      )}
                      {vehicle.gps_last_updated && (
                        <div className="flex items-center gap-1.5 text-[10px] text-gray-400">
                          <Clock size={12} className="shrink-0" />
                          <span>Обновлено: {new Date(vehicle.gps_last_updated).toLocaleString()}</span>
                        </div>
                      )}
                    </div>
                  ) : (
                    <div className="mt-3 pt-3 border-t border-gray-100 dark:border-gray-700 text-xs text-gray-400 italic">
                      GPS трекер не установлен
                    </div>
                  )}

                  {vehicle.current_location && (
                    <button
                      type="button"
                      onClick={() => searchCargo(vehicle)}
                      disabled={searchingCargoId === vehicle.id}
                      className="mt-3 w-full flex items-center justify-center gap-2 px-3 py-2 text-sm font-medium text-white bg-green-600 hover:bg-green-700 disabled:opacity-60 disabled:cursor-wait rounded-lg transition-colors"
                    >
                      <Search size={16} className={searchingCargoId === vehicle.id ? 'animate-spin' : ''} />
                      {searchingCargoId === vehicle.id ? 'Поиск грузов...' : 'Искать груз'}
                    </button>
                  )}
                </div>
              </div>
            ))}
          </div>
        </>
      )}

      {/* Edit/Create Modal */}
      <Modal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        title={editingVehicle ? "Редактирование ТС" : "Новое транспортное средство"}
      >
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium mb-1">Госномер</label>
            <input
              type="text"
              name="license_plate"
              required
              className="input w-full"
              placeholder="AA 1234 BB"
              value={formData.license_plate}
              onChange={handleInputChange}
            />
          </div>

          <div>
            <label className="block text-sm font-medium mb-1">Тип кузова</label>
            <select
              name="vehicle_type"
              className="input w-full"
              value={formData.vehicle_type}
              onChange={handleInputChange}
            >
              <option value="Tent">Тент</option>
              <option value="Reefer">Рефрижератор</option>
              <option value="Container">Контейнер</option>
              <option value="Other">Другое</option>
            </select>
          </div>

          <div className="grid grid-cols-3 gap-2">
            <div>
              <label className="block text-sm font-medium mb-1">Длина (м)</label>
              <input
                type="text"
                name="length"
                inputMode="decimal"
                required
                className="input w-full"
                value={formData.length}
                onChange={handleInputChange}
                placeholder="13.6"
              />
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">Ширина (м)</label>
              <input
                type="text"
                name="width"
                inputMode="decimal"
                required
                className="input w-full"
                value={formData.width}
                onChange={handleInputChange}
                placeholder="2.45"
              />
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">Высота (м)</label>
              <input
                type="text"
                name="height"
                inputMode="decimal"
                required
                className="input w-full"
                value={formData.height}
                onChange={handleInputChange}
                placeholder="2.7"
              />
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium mb-1">Грузоподъёмность (кг)</label>
            <input
              type="text"
              name="payload_capacity"
              inputMode="numeric"
              required
              className="input w-full"
              value={formData.payload_capacity}
              onChange={handleInputChange}
              placeholder="24000"
            />
          </div>

          <div>
            <label className="block text-sm font-medium mb-1">GPS Трекер ID (опционально)</label>
            <input
              type="text"
              name="gps_tracker_id"
              className="input w-full"
              placeholder="IMEI или ID"
              value={formData.gps_tracker_id}
              onChange={handleInputChange}
            />
          </div>

          <div className="flex justify-end gap-3 mt-6">
            <button
              type="button"
              className="btn btn-text"
              onClick={() => setIsModalOpen(false)}
            >
              Отмена
            </button>
            <button
              type="submit"
              className="btn btn-primary"
            >
              {editingVehicle ? "Обновить" : "Сохранить"}
            </button>
          </div>
        </form>
      </Modal>

      {/* Delete Confirmation Modal */}
      <Modal
        isOpen={isDeleteModalOpen}
        onClose={() => setIsDeleteModalOpen(false)}
        title="Удаление транспортного средства"
      >
        <div className="space-y-4">
          <div className="flex items-start gap-3 text-amber-600 bg-amber-50 p-3 rounded-lg">
            <AlertCircle className="shrink-0 mt-0.5" />
            <p className="text-sm">
              Вы уверены, что хотите удалить транспортное средство <strong>{deletingVehicle?.license_plate}</strong>? Это действие нельзя отменить.
            </p>
          </div>

          <div className="flex justify-end gap-3 mt-6">
            <button
              type="button"
              className="btn btn-text"
              onClick={() => setIsDeleteModalOpen(false)}
            >
              Отмена
            </button>
            <button
              type="button"
              className="btn bg-red-600 text-white hover:bg-red-700"
              onClick={handleDelete}
            >
              Удалить
            </button>
          </div>
        </div>
      </Modal>
    </div>
  );
};
