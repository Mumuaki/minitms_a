import { MapContainer, TileLayer, CircleMarker, Popup } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';

export interface MapVehicle {
  id: string;
  name: string;
  license_plate?: string;
  lat?: number;
  lon?: number;
  speed?: number;
  status: string;
}

export const VehicleMap = ({ vehicles }: { vehicles: MapVehicle[] }) => {
  const withPos = vehicles.filter((v) => v.lat != null && v.lon != null);
  if (withPos.length === 0) {
    return null;
  }
  const center: [number, number] = [withPos[0].lat as number, withPos[0].lon as number];

  return (
    <MapContainer center={center} zoom={7} style={{ height: 380, width: '100%' }}>
      <TileLayer
        attribution="&copy; OpenStreetMap contributors"
        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
      />
      {withPos.map((v) => (
        <CircleMarker
          key={v.id}
          center={[v.lat as number, v.lon as number]}
          radius={8}
          pathOptions={{ color: '#2563eb', fillColor: '#2563eb', fillOpacity: 0.8 }}
        >
          <Popup>{v.name}{v.license_plate ? ' (' + v.license_plate + ')' : ''}</Popup>
        </CircleMarker>
      ))}
    </MapContainer>
  );
};
