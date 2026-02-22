
export const DashboardPage = () => {
  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">Дашборд</h1>
      
      {/* KPI Cards Placeholder - FR-PLAN-005 */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="bg-card p-6 rounded-lg shadow-sm border border-border">
          <h3 className="text-sm font-medium text-muted">Выручка (План/Факт)</h3>
          <div className="mt-2 text-2xl font-bold">€ 0 / € 0</div>
          <p className="text-xs text-muted mt-1">0% выполнения</p>
        </div>
        
        <div className="bg-card p-6 rounded-lg shadow-sm border border-border">
          <h3 className="text-sm font-medium text-muted">Маржа (План/Факт)</h3>
          <div className="mt-2 text-2xl font-bold">€ 0 / € 0</div>
          <p className="text-xs text-muted mt-1">0% выполнения</p>
        </div>
        
        <div className="bg-card p-6 rounded-lg shadow-sm border border-border">
          <h3 className="text-sm font-medium text-muted">Пробег (План/Факт)</h3>
          <div className="mt-2 text-2xl font-bold">0 / 0 км</div>
          <p className="text-xs text-muted mt-1">0% выполнения</p>
        </div>
        
        <div className="bg-card p-6 rounded-lg shadow-sm border border-border">
          <h3 className="text-sm font-medium text-muted">Средняя ставка</h3>
          <div className="mt-2 text-2xl font-bold">€ 0.00 / км</div>
          <p className="text-xs text-muted mt-1">Текущий показатель</p>
        </div>
      </div>

      <div className="bg-card p-6 rounded-lg shadow-sm border border-border">
        <h2 className="text-lg font-medium mb-4">Активные рейсы</h2>
        <p className="text-muted text-sm">Нет активных рейсов</p>
      </div>
    </div>
  );
};
