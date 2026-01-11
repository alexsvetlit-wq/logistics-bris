import streamlit as st
import streamlit.components.v1 as components


# =========================
# Logistics калькулятор  =========================

st.set_page_config(
    page_title="Logistics калькулятор",
    layout="wide",
    page_icon="assets/bris_logo.png"
)

# --- Header ---
col1, col2 = st.columns([1, 5])
with col1:
    st.image("assets/bris_logo.png", width=120)
with col2:
    st.title("BRIS Logistics калькулятор")
VAT_PCT_FIXED = 22.0

# =========================
# (Блок 1) Дефолтные ставки фрахта по портам
# =========================

FREIGHT_DEFAULTS = {
    # Индия (старые портовые ставки оставлены как fallback, но для Индии ниже добавлены ставки по линиям)
    ("Индия", "Mundra", "Новороссийск", "20"): 4500.0,
    ("Индия", "Mundra", "Санкт-Петербург", "20"): 5200.0,
    ("Индия", "Mundra", "Владивосток", "20"): 6800.0,
    ("Индия", "Nhava Sheva", "Новороссийск", "20"): 4600.0,
    ("Индия", "Nhava Sheva", "Санкт-Петербург", "20"): 5300.0,
    ("Индия", "Nhava Sheva", "Владивосток", "20"): 6900.0,

    ("Индия", "Mundra", "Новороссийск", "40"): 6200.0,
    ("Индия", "Mundra", "Санкт-Петербург", "40"): 7100.0,
    ("Индия", "Mundra", "Владивосток", "40"): 9300.0,
    ("Индия", "Nhava Sheva", "Новороссийск", "40"): 6400.0,
    ("Индия", "Nhava Sheva", "Санкт-Петербург", "40"): 7200.0,
    ("Индия", "Nhava Sheva", "Владивосток", "40"): 9500.0,

    # Китай
    ("Китай", "Qingdao", "Новороссийск", "20"): 4200.0,
    ("Китай", "Qingdao", "Санкт-Петербург", "20"): 4800.0,
    ("Китай", "Qingdao", "Владивосток", "20"): 2600.0,
    ("Китай", "Shanghai", "Новороссийск", "20"): 4300.0,
    ("Китай", "Shanghai", "Санкт-Петербург", "20"): 4900.0,
    ("Китай", "Shanghai", "Владивосток", "20"): 2700.0,
    ("Китай", "Ningbo", "Новороссийск", "20"): 4350.0,
    ("Китай", "Ningbo", "Санкт-Петербург", "20"): 4950.0,
    ("Китай", "Ningbo", "Владивосток", "20"): 2750.0,
    ("Китай", "Foshan", "Новороссийск", "20"): 4400.0,
    ("Китай", "Foshan", "Санкт-Петербург", "20"): 5000.0,
    ("Китай", "Foshan", "Владивосток", "20"): 2800.0,

    ("Китай", "Qingdao", "Новороссийск", "40"): 5800.0,
    ("Китай", "Qingdao", "Санкт-Петербург", "40"): 6500.0,
    ("Китай", "Qingdao", "Владивосток", "40"): 3400.0,
    ("Китай", "Shanghai", "Новороссийск", "40"): 5900.0,
    ("Китай", "Shanghai", "Санкт-Петербург", "40"): 6600.0,
    ("Китай", "Shanghai", "Владивосток", "40"): 3500.0,
    ("Китай", "Ningbo", "Новороссийск", "40"): 5950.0,
    ("Китай", "Ningbo", "Санкт-Петербург", "40"): 6650.0,
    ("Китай", "Ningbo", "Владивосток", "40"): 3550.0,
    ("Китай", "Foshan", "Новороссийск", "40"): 6000.0,
    ("Китай", "Foshan", "Санкт-Петербург", "40"): 6700.0,
    ("Китай", "Foshan", "Владивосток", "40"): 3600.0,
}

# =========================
# (НОВОЕ) Дефолтные ставки по Индии из таблицы (морские линии + прямой/непрямой)
# =========================
# Применяем для "Море (20фут.контейнер)".
INDIA_LINE_DEFAULTS_20 = {
    # line: {"direct": rate, "indirect": rate}
    "Fesco": {"direct": 2500.0, "indirect": 2300.0},
    "Silmar": {"direct": 2800.0, "indirect": 2600.0},
    "Akkon": {"direct": None,  "indirect": 2400.0},
    "Arkas": {"direct": 2600.0, "indirect": 2350.0},
    "ExpertTrans": {"direct": 2550.0, "indirect": 2400.0},
}

# =========================
# Утилиты
# =========================

def convert_to_usd(amount: float, currency: str, usd_cny: float, usd_inr: float) -> float:
    if currency == "USD":
        return amount
    if currency == "CNY":
        return amount / usd_cny if usd_cny else 0.0
    if currency == "INR":
        return amount / usd_inr if usd_inr else 0.0
    return amount


def infer_hs_and_duty(product_type: str, finish: str):
    if product_type == "Керамогранит":
        if finish == "Неглазурованный":
            return "69072100", 12.0
        return "69072200", 7.5

    if product_type == "Сантехника (унитазы)":
        return "6910900000", 10.0

    return "", 0.0


# =========================
# (НОВОЕ) Ставка 2026 (фикс) по диапазонам таможенной стоимости (RUB)
# =========================
def vat_fee_2026_rub(customs_value_rub: float) -> float:
    if customs_value_rub <= 200_000:
        return 1_231.0
    if customs_value_rub <= 450_000:
        return 2_462.0
    if customs_value_rub <= 1_200_000:
        return 4_924.0
    if customs_value_rub <= 2_700_000:
        return 13_541.0
    if customs_value_rub <= 4_200_000:
        return 18_465.0
    if customs_value_rub <= 5_500_000:
        return 24_620.0
    if customs_value_rub <= 7_000_000:
        return 49_240.0
    if customs_value_rub <= 10_000_000:
        return 49_240.0
    return 73_860.0


def calc_model(
    qty_m2,
    price_per_m2,
    price_currency,
    usd_cny,
    usd_inr,
    freight_usd,
    insurance_usd,
    local_rub,
    usd_rub,
    duty_pct,
    vat_pct,
    incoterms,
    invoice_total,
    invoice_currency,
    containers_qty,
):
    # 1) Товар, USD (как было — по количеству и цене)
    goods_amount = qty_m2 * price_per_m2
    goods_usd = convert_to_usd(goods_amount, price_currency, usd_cny, usd_inr)

    # 2) Таможенная стоимость, USD (НОВАЯ ФОРМУЛА):
    # Тамож.стоимость = стоимость по инвойсу общая + (Фрахт × количество контейнеров)
    # (инвойс переводим в USD, если валюта USD/CNY/INR; RUB переводим по курсу; EUR оставляем как есть)
    if invoice_currency == "RUB":
        invoice_usd = (invoice_total / usd_rub) if usd_rub else 0.0
    else:
        invoice_usd = convert_to_usd(invoice_total, invoice_currency, usd_cny, usd_inr)

    customs_value_usd = invoice_usd + (freight_usd * float(containers_qty))

    # 3) Пошлина (как было)
    duty_usd = customs_value_usd * duty_pct / 100

    # 4) НДС 22% + Ставка 2026 (НОВАЯ ФОРМУЛА):
    # НДС_RUB = (Тамож.стоимость_USD + Пошлина_USD) × курс × 22% + ставка_2026(RUB)
    customs_value_rub = customs_value_usd * usd_rub
    vat_fee_rub = vat_fee_2026_rub(customs_value_rub)

    vat_rub = (customs_value_usd + duty_usd) * usd_rub * (vat_pct / 100) + vat_fee_rub
    vat_usd = (vat_rub / usd_rub) if usd_rub else 0.0  # для отображения в USD

    # 5) Итого затраты (RUB) — учитываем НДС в рублях
    total_rub = (
    (customs_value_usd + duty_usd + vat_usd) * usd_rub
    + local_rub
    + insurance_usd * containers_qty * usd_rub
)


    # 6) Себестоимость за м² (RUB/м²)
    cost_rub_m2 = total_rub / qty_m2 if qty_m2 else 0

    return {
        "goods_usd": goods_usd,
        "customs_value_usd": customs_value_usd,
        "duty_usd": duty_usd,
        "vat_usd": vat_usd,
        "total_rub": total_rub,
        "cost_rub_m2": cost_rub_m2,
    }


# =========================
# Sidebar
# =========================

with st.sidebar:
    st.header("Ввод данных")

    supplier = st.text_input("Фабрика / поставщик (как в инвойсе)")

    # =========================
    # ВСТАВКА: общая стоимость товара по инвойсу (НЕ СВЯЗЫВАЕМ НИ С ЧЕМ)
    # =========================
    inv_c1, inv_c2 = st.columns([2, 1])
    with inv_c1:
        invoice_total = st.number_input(
            "Общая стоимость товара по инвойсу",
            min_value=0.0,
            value=0.0,
            step=100.0,
        )
    with inv_c2:
        invoice_currency = st.selectbox(
            "Валюта (инвойс)",
            ["USD", "CNY", "INR", "RUB", "EUR"],
            index=0
        )

    country = st.selectbox("Страна", ["Индия", "Китай"], index=0)
    incoterms = st.selectbox("Инкотермс", ["EXW", "FOB", "CIF", "DAP"], index=1)

    transport = st.selectbox(
        "Тип доставки",
        ["Море (20фут.контейнер)", "Море (40фут.контейнер)", "ЖД", "Авто"],
    )

    # =========================
    # ВСТАВКА: количество контейнеров (под "Тип доставки")
    # =========================
    containers_qty = st.number_input(
        "Количество контейнеров",
        min_value=1,
        value=1,
        step=1
    )

    st.subheader("Порты")
    c1, c2 = st.columns(2)

    with c1:
        if country == "Индия":
            port_loading = st.selectbox("Порт отгрузки", ["Mundra", "Nhava Sheva"])
        else:
            port_loading = st.selectbox("Порт отгрузки", ["Qingdao", "Shanghai", "Ningbo", "Foshan"])

    with c2:
        port_discharge = st.selectbox(
            "Порт выгрузки",
            ["Новороссийск", "Санкт-Петербург", "Владивосток"]
        )

    # --- Курсы валют ---
    currency_rate = st.number_input("Курс USD→RUB", value=95.0, step=0.1)

    usd_cny = 0.0
    usd_inr = 0.0

    if country == "Китай":
        usd_cny = st.number_input("Курс USD→CNY (RMB)", value=7.20, step=0.01)
        price_currency = st.selectbox("Валюта цены товара", ["CNY", "USD"], index=0)

    elif country == "Индия":
        usd_inr = st.number_input("Курс USD→INR", value=83.0, step=0.1)
        price_currency = st.selectbox("Валюта цены товара", ["USD", "INR"], index=0)

    st.divider()

    # --- Товар ---
    st.subheader("Товар / партия")

    product_type = st.selectbox("Тип товара", ["Керамогранит", "Сантехника (унитазы)"])

    if product_type == "Керамогранит":
        finish = st.selectbox("Поверхность", ["Глазурованный", "Неглазурованный"])
    else:
        finish = "Глазурованный"

    hs_auto, duty_auto = infer_hs_and_duty(product_type, finish)

    hs_code = st.text_input("Код ТН ВЭД (HS Code)", value=hs_auto)

    manual_duty = st.checkbox("Ручная ставка пошлины")
    if manual_duty:
        duty_pct = st.number_input("Пошлина, %", value=duty_auto, step=0.5)
    else:
        duty_pct = duty_auto
        st.text_input("Пошлина, % (авто)", value=str(duty_pct), disabled=True)

    st.text_input("НДС, % (фикс)", value=str(VAT_PCT_FIXED), disabled=True)

    # =========================
    # ВСТАВКА: выбор ед. измерения (шт / м²) — БОЛЬШЕ НИЧЕГО НЕ МЕНЯЕМ
    # =========================
    unit = st.selectbox("Ед. измерения", ["м²", "шт."], index=0)

    if unit == "м²":
        qty_m2 = st.number_input("Кол-во, м²", value=1200.0, step=10.0)
        price_label = f"Цена товара, {price_currency}/м²"
        price_per_m2 = st.number_input(price_label, value=7.5, step=0.1)
    else:
        qty_m2 = st.number_input("Кол-во, шт.", value=1000.0, step=10.0)
        price_label = f"Цена товара, {price_currency}/шт."
        price_per_m2 = st.number_input(price_label, value=7.5, step=0.1)

    st.divider()

    # =========================
    # Логистика + (НОВОЕ) выбор морской линии и прямой/непрямой
    # =========================
    st.subheader("Логистика")

    is_sea = transport.startswith("Море")
    container_size = None
    if transport == "Море (20фут.контейнер)":
        container_size = "20"
    elif transport == "Море (40фут.контейнер)":
        container_size = "40"

    # НОВОЕ: Морская линия + галка прямого/непрямого (только для Индии и моря)
    sea_line = None
    is_direct = False
    if is_sea and country == "Индия":
        sea_line = st.selectbox("Морская линия", ["Fesco", "Silmar", "Akkon", "Arkas", "ExpertTrans"])
        is_direct = st.checkbox("Прямое судно", value=True)  # если выключить — считаем "непрямое"

    use_auto_freight = False
    if is_sea and container_size:
        use_auto_freight = st.checkbox("Фрахт: авто по портам/линиям", value=True)

    auto_val = 0.0

    # 1) Индия + море + 20фут: берём дефолт из таблицы линий
    if is_sea and country == "Индия" and container_size == "20" and sea_line:
        route_key = "direct" if is_direct else "indirect"
        rate = INDIA_LINE_DEFAULTS_20.get(sea_line, {}).get(route_key, None)
        auto_val = float(rate) if rate is not None else 0.0

    # 2) Иначе: fallback на портовые дефолты (как было)
    if auto_val == 0.0 and is_sea and container_size:
        auto_val = FREIGHT_DEFAULTS.get((country, port_loading, port_discharge, container_size), 0.0)

    if is_sea and container_size and use_auto_freight:
        freight_usd = auto_val
        st.number_input("Фрахт, USD (авто)", value=float(freight_usd), disabled=True)

        # предупреждение, если по выбранной линии нет ставки (например Akkon прямой)
        if freight_usd == 0.0:
            st.warning("Для этого выбора нет дефолтной ставки — введи вручную (сними галочку).")
    else:
        # оставляем как было: ручной ввод
        freight_usd = st.number_input("Фрахт, USD/конт.", value=4500.0, step=50.0)

    insurance_usd = st.number_input("DTHC портовые сборы, USD/конт.", value=0.0, step=10.0)

    # Поле "как раньше" (ручной ввод, если детализацию не используем)
    local_costs_rub_input = st.number_input(
        "Локальные расходы РФ, RUB",
        value=300000.0,
        step=1000.0
    )

    # =========================
    # (Блок) Детализация локальных расходов РФ
    # =========================
    st.subheader("Локальные расходы РФ (детализация)")

    lr_ktt_out = st.number_input(
        "Вывоз ктк из порта на СВХ в т.ч сдача в депо, RUB/1 ктк",
        value=24000.0, step=500.0
    )

    lr_restack_cross = st.number_input(
        "Перетарка на СВХ кросс-докинг (из ктк в авто), RUB/1 фура",
        value=9000.0, step=250.0
    )

    lr_prr_mech = st.number_input(
        "ПРР механизированная (из ктк -склад- авто), RUB/паллет",
        value=500.0, step=250.0
    )

    lr_prr_manual = st.number_input(
        "ПРР ручная (из ктк авто/склад) за 1 тн без паллеты, RUB/тонна",
        value=800.0, step=50.0
    )

    lr_restack_ktt = st.number_input(
        "Паллетированние комплекс(вкл.поддон+стрейч+пп лента), RUB/паллет",
        value=1300.0, step=50.0
    )

    lr_restack_terminal = st.number_input(
        "Перетарка на СВХ (с ктквоз снять/поставить), RUB/ктк лифт",
        value=1500.0, step=50.0
    )

    lr_storage = st.number_input(
        "Хранение на СВХ (1 под/сутки начиная с 10 дня), RUB/паллетодень",
        value=30.0, step=5.0
    )

    lr_delivery_rf = st.number_input(
        "Доставка по РФ до склада клиента (авто 20 тонн), RUB/авто",
        value=0.0, step=1000.0
    )

    # --- Сумма локальных расходов РФ (детализация) ---
    local_costs_rub_calc = (
        lr_ktt_out
        + lr_prr_mech
        + lr_prr_manual
        + lr_restack_ktt
        + lr_restack_cross
        + lr_restack_terminal
        + lr_storage
        + lr_delivery_rf
    )

    st.caption(f"Сумма детализации: {local_costs_rub_calc:,.0f} ₽".replace(",", " "))

    # --- Что используем в расчётах ---
    local_costs_rub = local_costs_rub_calc if local_costs_rub_calc > 0 else local_costs_rub_input
    local_rub = local_costs_rub  # совместимость с calc_model(..., local_rub, ...)

    st.caption(
        f"В расчёте используется: {'детализация' if local_costs_rub_calc > 0 else 'ручной ввод'}"
    )

    calc = st.button("Рассчитать", type="primary")

# =========================
# Результат
# =========================

if calc:
    res = calc_model(
        qty_m2,
        price_per_m2,
        price_currency,
        usd_cny,
        usd_inr,
        freight_usd,
        insurance_usd,
        local_rub,
        currency_rate,
        duty_pct,
        VAT_PCT_FIXED,
        incoterms,
        invoice_total,
        invoice_currency,
        containers_qty,
    )

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Товар, USD", f"{res['goods_usd']:,.2f}")
    c2.metric("Тамож. стоимость, USD", f"{res['customs_value_usd']:,.2f}")
    c3.metric("Пошлина, USD", f"{res['duty_usd']:,.2f}")
    c4.metric("НДС 22%+тамож.сбор, USD", f"{res['vat_usd']:,.2f}")

    st.divider()
    c5, c6 = st.columns(2)
    c5.metric("Итого стоимость товара в НВРСК , RUB", f"{res['total_rub']:,.0f}")
    c6.metric("Себестоимость, RUB/м²", f"{res['cost_rub_m2']:,.2f}")

    # =========================
    # (Блок) Печать / PDF (форма)
    # =========================
    st.subheader("Печать / PDF")

    def _fmt_money(x, digits=2):
        try:
            return f"{float(x):,.{digits}f}".replace(",", " ")
        except Exception:
            return str(x)

    def _fmt_int(x):
        try:
            return f"{float(x):,.0f}".replace(",", " ")
        except Exception:
            return str(x)

    # Данные (ввод)
    _print_rows_left = [
        ("Фабрика / поставщик", supplier if supplier else "—"),
        ("Страна", country),
        ("Инкотермс", incoterms),
        ("Тип доставки", transport),
        ("Контейнеров", str(containers_qty)),
        ("Порт отгрузки", port_loading),
        ("Порт выгрузки", port_discharge),
        ("Курс USD→RUB", _fmt_money(currency_rate, 2)),
        ("Инвойс (итого)", f"{_fmt_money(invoice_total, 2)} {invoice_currency}"),
        ("Товар", product_type),
        ("Поверхность", finish),
        ("Код ТН ВЭД", hs_code),
        ("Пошлина, %", _fmt_money(duty_pct, 2)),
        ("НДС, %", _fmt_money(VAT_PCT_FIXED, 2)),
        ("Кол-во", f"{_fmt_money(qty_m2, 2)} {unit}"),
        ("Цена", f"{_fmt_money(price_per_m2, 2)} {price_currency}/{unit}"),
        ("Фрахт", f"{_fmt_money(freight_usd, 2)} USD/конт."),
        ("DTHC портовые сборы", f"{_fmt_money(insurance_usd, 2)} USD/конт."),
        ("Локальные расходы РФ (в расчёте)", f"{_fmt_int(local_rub)} ₽"),
    ]

    # Детализация локальных расходов (если заполнена)
    _print_local_detail = [
        ("Вывоз КТК из порта на СВХ (в т.ч. депо)", lr_ktt_out, "₽"),
        ("Перетарка СВХ кросс-докинг (КТК → авто)", lr_restack_cross, "₽"),
        ("ПРР механизированная", lr_prr_mech, "₽"),
        ("ПРР ручная", lr_prr_manual, "₽"),
        ("Паллетирование комплекс", lr_restack_ktt, "₽"),
        ("Перетарка на СВХ (лифт)", lr_restack_terminal, "₽"),
        ("Хранение на СВХ", lr_storage, "₽"),
        ("Доставка по РФ до склада клиента", lr_delivery_rf, "₽"),
    ]

    # Итоги (результат)
    _print_totals = [
        ("Товар, USD", res["goods_usd"], "USD"),
        ("Тамож. стоимость, USD", res["customs_value_usd"], "USD"),
        ("Пошлина, USD", res["duty_usd"], "USD"),
        ("НДС 22%+тамож.сбор, USD", res["vat_usd"], "USD"),
        ("Итого стоимость товара в НВРСК, RUB", res["total_rub"], "₽"),
        ("Себестоимость, RUB/м²", res["cost_rub_m2"], "₽"),
    ]

    _rows_left_html = "".join(
        f"<tr><td>{k}</td><td style='text-align:right'>{v}</td></tr>"
        for k, v in _print_rows_left
    )

    _rows_local_html = "".join(
        f"<tr><td>{k}</td><td style='text-align:right'>{_fmt_money(v, 2)} {u}</td></tr>"
        for k, v, u in _print_local_detail
    )

    _rows_totals_html = "".join(
        f"<tr><td>{k}</td><td style='text-align:right'>{_fmt_money(v, 2)} {u}</td></tr>"
        for k, v, u in _print_totals
    )

    _html_print = f"""
    <!doctype html>
    <html>
    <head>
      <meta charset="utf-8" />
      

<style>
  @page { size: A4; margin: 8mm; }

  body {
    font-family: Arial, sans-serif;
    color:#111;
    font-size: 10px;
    line-height: 1.3;
  }

  .header {
    display:flex;
    align-items:center;
    gap:8px;
    margin-bottom: 6px;
  }

  .logo { height:26px; }

  .title {
    font-size: 12px;
    font-weight: 700;
    margin:0;
  }

  .subtitle {
    margin:0;
    color:#444;
    font-size: 9.5px;
  }

  .grid {
    display:grid;
    grid-template-columns: 1fr 1fr;
    gap: 8px;
  }

  .card {
    border:1px solid #ddd;
    border-radius:6px;
    padding:6px 8px;
  }

  .card h3 {
    margin:0 0 6px 0;
    font-size: 10.5px;
    font-weight:700;
  }

  .t {
    width:100%;
    border-collapse: collapse;
  }

  .t th, .t td {
    border-bottom:1px solid #eee;
    padding:4px 5px;
    font-size: 10px;
    line-height: 1.3;
    vertical-align: top;
  }

  .t th {
    text-align:left;
    color:#333;
    font-weight:700;
  }

  .sum td {
    border-top: 2px solid #ccc;
    font-weight:700;
  }

  .footer {
    margin-top: 6px;
    font-size: 9px;
    color:#777;
    text-align:center;
  }

  .card, table, tr {
    page-break-inside: avoid;
  }
</style>


    </head>
    <body>
      <div class="header">
        <img class="logo" src="assets/bris_logo.png" />
        <div>
          <p class="title">BRIS Logistics — расчёт себестоимости</p>
          <p class="subtitle">{country} • {incoterms} • {transport} • Контейнеров: {containers_qty}</p>
        </div>
      </div>

      <div class="grid">
        <div class="card">
          <h3>Вводные данные</h3>
          <table class="t"><tbody>{_rows_left_html}</tbody></table>
        </div>

        <div class="card">
          <h3>Итоги</h3>
          <table class="t"><tbody>{_rows_totals_html}</tbody></table>
        </div>
      </div>

      <div class="card" style="margin-top:10px;">
        <h3>Локальные расходы РФ (детализация)</h3>
        <table class="t">
          <thead><tr><th>Статья</th><th style="text-align:right">Значение</th></tr></thead>
          <tbody>
            {_rows_local_html}
            <tr class="sum"><td><b>Итого локальные (в расчёте)</b></td><td style="text-align:right"><b>{_fmt_int(local_rub)} ₽</b></td></tr>
          </tbody>
        </table>
      </div>

      <div class="footer">
        BRIS Ceramic • Документ сформирован автоматически из калькулятора.
      </div>
    </body>
    </html>
    """

    with st.expander("Открыть форму для печати (A4)", expanded=False):
        components.html(_html_print, height=1400)
        st.caption("Далее: Ctrl+P → Save as PDF / Печать.")

    # =========================
    # Экспорт формы (Excel / CSV) — без внешних библиотек
    # =========================
    def _csv_cell(v):
        s = str(v)
        s = s.replace(";", ",").replace("\n", " ").replace("\r", " ")
        return s

    _csv_rows = []
    _csv_rows.append(["Вводные данные", ""])
    for k, v in _print_rows_left:
        _csv_rows.append([k, v])

    _csv_rows.append(["", ""])
    _csv_rows.append(["Итоги", ""])
    for k, v, u in _print_totals:
        _csv_rows.append([k, f"{_fmt_money(v, 2)} {u}"])

    _csv_rows.append(["", ""])
    _csv_rows.append(["Локальные расходы РФ (детализация)", ""])
    for k, v, u in _print_local_detail:
        _csv_rows.append([k, f"{_fmt_money(v, 2)} {u}"])

    _csv_rows.append(["Итого локальные (в расчёте)", f"{_fmt_int(local_rub)} ₽"])

    _csv_text = "\n".join(";".join(_csv_cell(c) for c in row) for row in _csv_rows)

    st.download_button(
        "Скачать форму (Excel / CSV)",
        data=_csv_text.encode("utf-8"),
        file_name="BRIS_Logistics_Print_Form.csv",
        mime="text/csv",
        use_container_width=True
    )



else:
    st.write("Заполни параметры слева и нажми **Рассчитать**.")
