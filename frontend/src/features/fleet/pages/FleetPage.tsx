import React, { useState, useEffect } from 'react';
import { Plus, Truck, Pencil, Trash2, AlertCircle, MapPin, Clock, RefreshCw } from 'lucide-react';
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

export const FleetPage = () => {
  const [vehicles, setVehicles] = useState<Vehicle[]>([]);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [isDeleteModalOpen, setIsDeleteModalOpen] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [editingVehicle, setEditingVehicle] = useState<Vehicle | null>(null);
  const [deletingVehicle, setDeletingVehicle] = useState<Vehicle | null>(null);
  const [refreshingLocationId, setRefreshingLocationId] = useState<number | null>(null);

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
    setRefreshingLocationId(vehicleId);
    try {
      const { data } = await apiClient.post<Vehicle>(`/fleet/${vehicleId}/refresh-location`);
      setVehicles(prev => prev.map(v => v.id === vehicleId ? data : v));
    } catch (err) {
      console.error('Failed to refresh location', err);
    } finally {
      setRefreshingLocationId(null);
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
                <span className={`px-2 py-1 rounded text-xs font-medium ${
                  vehicle.status === 'Free' ? 'bg-green-100 text-green-800' : 
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
                         className="p-1 text-gray-500 hover:text-blue-600 hover:bg-blue-50 dark:hover:bg-blue-900/30 rounded"
                         title="Обновить локацию из GPS"
                       >
                         <RefreshCw size={14} className={refreshingLocationId === vehicle.id ? 'animate-spin' : ''} />
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
              </div>
            </div>
          ))}
        </div>
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
