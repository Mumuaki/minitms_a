"""Маппинг заказа в строку Google Sheets (25 столбцов, FR-GSHEET-002/003/011/012)."""

SHEETS_HEADERS = [
    "Дата загрузки", "Источник", "Заказчик", "Номер заявки", "Сумма в инвойс",
    "Номер инвойса", "Место загрузки", "Место выгрузки", "Дистанция", "OSM min distances",
    "Номер СМР", "Дата выгрузки", "Вес груза", "Маршрут OSM", "€/км",
    "Контакт контрагента", "Сканы документов туда", "Оригиналы документов", "Кол-во дней", "По эл почте",
    "(резерв)", "Оригиналы клиенту", "Дата поступления клиенту почтой", "Дата ЕТР", "Дата АТР",
]


def _fmt(v):
    if v is None:
        return ""
    return str(v)


def build_order_row(order, cargo, row_index):
    """Возвращает 25 значений строки заказа. row_index — номер строки (для формул)."""
    loading_date = ""
    unloading_date = ""
    external_id = ""
    loading_place = ""
    unloading_place = ""
    distance_trans_eu = ""
    distance_osm = ""
    weight = ""
    route_polyline = ""
    revenue = ""

    if cargo is not None:
        loading_date = _fmt(getattr(cargo, "loading_date", None) or "")
        unloading_date = _fmt(getattr(cargo, "unloading_date", None) or "")
        external_id = _fmt(getattr(cargo, "external_id", "") or "")
        lp = getattr(cargo, "loading_place", None)
        up = getattr(cargo, "unloading_place", None)
        if isinstance(lp, dict):
            loading_place = lp.get("address", "")
        if isinstance(up, dict):
            unloading_place = up.get("address", "")
        distance_trans_eu = _fmt(getattr(cargo, "distance_trans_eu", None) or "")
        distance_osm = _fmt(getattr(cargo, "distance_osm", None) or "")
        weight = _fmt(getattr(cargo, "weight", None) or "")
        route_polyline = _fmt(getattr(cargo, "route_polyline", None) or "")

    if order is not None:
        revenue = _fmt(getattr(order, "revenue", None) or "")
        if not loading_date:
            loading_date = _fmt(getattr(order, "start_date", None) or "")
        if not unloading_date:
            unloading_date = _fmt(getattr(order, "end_date", None) or "")

    row = [
        loading_date,       # A Дата загрузки
        "trans.eu",         # B Источник
        "",                 # C Заказчик (не хранится в Order)
        external_id,        # D Номер заявки
        revenue,            # E Сумма в инвойс
        "",                 # F Номер инвойса (ручное)
        loading_place,      # G Место загрузки
        unloading_place,    # H Место выгрузки
        distance_trans_eu,  # I Дистанция
        distance_osm,       # J OSM min distances
        "",                 # K Номер СМР (ручное)
        unloading_date,     # L Дата выгрузки
        weight,             # M Вес груза
        route_polyline,     # N Маршрут OSM
        "=E%d/J%d" % (row_index, row_index),  # O €/км
        "",                 # P Контакт контрагента
        "",                 # Q Сканы документов (ручное)
        "",                 # R Оригиналы документов (ручное)
        "=L%d-A%d" % (row_index, row_index),  # S Кол-во дней
        "",                 # T По эл почте (ручное)
        "",                 # U резерв
        "",                 # V Оригиналы клиенту (ручное)
        "",                 # W Дата поступления (ручное)
        "",                 # X Дата ЕТР
        "",                 # Y Дата АТР
    ]
    assert len(row) == len(SHEETS_HEADERS)
    return row
