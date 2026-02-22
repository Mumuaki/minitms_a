interface Cargo {
  id: string;
  external_id: string;
  loading_place: {
    address: string;
    country_code: string;
  };
  unloading_place: {
    address: string;
    country_code: string;
  };
  loading_date: string;
  weight: number;
  body_type: string;
  price: number;
  distance_trans_eu: number;
  company_name?: string; // If we add it later to DTO
  status_color?: string;
}

interface LoadsTableProps {
  loads: Cargo[];
  isLoading: boolean;
}

export const LoadsTable = ({ loads, isLoading }: LoadsTableProps) => {
  if (isLoading) {
    return <div className="text-center p-4">Loading...</div>;
  }

  if (loads.length === 0) {
    return <div className="text-center p-4 text-gray-500">No loads found. Try importing some data.</div>;
  }

  return (
    <div className="overflow-x-auto rounded-lg border border-gray-200 shadow-sm">
      <table className="min-w-full divide-y divide-gray-200 bg-white text-sm">
        <thead className="bg-gray-50">
          <tr>
            <th className="px-4 py-2 text-left font-medium text-gray-900">ID</th>
            <th className="px-4 py-2 text-left font-medium text-gray-900">Loading</th>
            <th className="px-4 py-2 text-left font-medium text-gray-900">Unloading</th>
            <th className="px-4 py-2 text-left font-medium text-gray-900">Date</th>
            <th className="px-4 py-2 text-left font-medium text-gray-900">Params</th>
            <th className="px-4 py-2 text-right font-medium text-gray-900">Price (€)</th>
            <th className="px-4 py-2 text-right font-medium text-gray-900">Dist (km)</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-gray-200">
          {loads.map((load) => (
            <tr key={load.id} className="hover:bg-gray-50">
              <td className="px-4 py-2 font-medium text-gray-900">{load.external_id}</td>
              <td className="px-4 py-2 text-gray-700">{load.loading_place.address}</td>
              <td className="px-4 py-2 text-gray-700">{load.unloading_place.address}</td>
              <td className="px-4 py-2 text-gray-700">{load.loading_date || 'N/A'}</td>
              <td className="px-4 py-2 text-gray-700">
                {load.weight ? `${load.weight} t` : ''} 
                {load.body_type ? `, ${load.body_type}` : ''}
              </td>
              <td className="px-4 py-2 text-right font-bold text-gray-900">{load.price || '-'}</td>
              <td className="px-4 py-2 text-right text-gray-700">{load.distance_trans_eu || '-'}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};
