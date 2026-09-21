import { MapContainer, TileLayer, CircleMarker, Polyline, Popup } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';

interface CargoRouteMapProps {
  loading: { lat: number; lon: number; address: string };
  unloading: { lat: number; lon: number; address: string };
}

export const CargoRouteMap = ({ loading, unloading }: CargoRouteMapProps) => {
  if (loading.lat == null || loading.lon == null || unloading.lat == null || unloading.lon == null) {
    return <p className="text-sm text-muted p-4">Нет координат для отображения маршрута</p>;
  }
  const center: [number, number] = [(loading.lat + unloading.lat) / 2, (loading.lon + unloading.lon) / 2];
  return (
    <MapContainer center={center} zoom={6} style={{ height: 320, width: '100%' }}>
      <TileLayer
        attribution="&copy; OpenStreetMap contributors"
        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
      />
      <CircleMarker center={[loading.lat, loading.lon]} radius={8} pathOptions={{ color: '#22c55e', fillColor: '#22c55e', fillOpacity: 0.8 }}>
        <Popup>B (загрузка): {loading.address}</Popup>
      </CircleMarker>
      <CircleMarker center={[unloading.lat, unloading.lon]} radius={8} pathOptions={{ color: '#3b82f6', fillColor: '#3b82f6', fillOpacity: 0.8 }}>
        <Popup>C (выгрузка): {unloading.address}</Popup>
      </CircleMarker>
      <Polyline positions={[[loading.lat, loading.lon], [unloading.lat, unloading.lon]]} pathOptions={{ color: '#2563eb', weight: 3 }} />
    </MapContainer>
  );
};
