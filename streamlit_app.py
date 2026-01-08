import streamlit as st

# =========================
# BRIS Logistics калькулятор (v0+)
# 1) Порты отгрузки + выгрузки (рядом)
# 2) Море 20/40 фут
# 3) Дефолтные ставки фрахта по направлениям (порт отгрузки + порт выгрузки)
# 4) Китай: курс USD→CNY и возможность цены в CNY
# 5) НДС фикс 22%, пошлина авто по типу товара/поверхности/HS (с ручным оверрайдом)
# =========================

st.set_page_config(
    page_title="BRIS Logistics калькулятор",
    layout="wide",
    page_icon="assets/bris_logo.png"
)

# --- Header ---
col1, col2 = st.columns([1, 5])
with col1:
    st.image("assets/bris_logo.png", width=120)
with col2:
    st.title("BRIS Logistics калькулятор")
    st.caption("Черновик v0+: логистика + таможня + себестоимость единицы товара")

# --- Дефолтные фрахты (примерные, правим позже под твою реальность) ---
# Ключ: (country, port_loading, port_discharge, "20ft"/"40ft") -> USD за партию
DEFAULT_FREIGHT_USD = {
    # India
    ("Индия", "Mundra", "Новороссийск", "20ft"): 4500,
    ("Индия", "Mundra", "Новороссийск", "40ft"): 6500,
    ("Индия", "Mundra", "Санкт-Петербург", "20ft"): 5200,
    ("Индия", "Mundra", "Санкт-Петербург", "40ft"): 7200,
    ("Индия", "Mundra", "Владивосток", "20ft"): 6500,
    ("Индия", "Mundra", "Владивосток", "40ft"): 9000,

    ("Индия", "Nhava Sheva", "Новороссийск", "20ft"): 4700,
    ("Индия", "Nhava Sheva", "Новороссийск", "40ft"): 6700,
    ("Индия", "Nhava Sheva", "Санкт-Петербург", "20ft"): 5400,
    ("Индия", "Nhava Sheva", "Санкт-Петербург", "40ft"): 7400,
    ("Индия", "Nhava Sheva", "Владивосток", "20ft"): 6700,
    ("Индия", "Nhava Sheva", "Владивосток", "40ft"): 9200,

    # China
    ("Китай", "Qingdao", "Новороссийск", "20ft"): 4000,
    ("Китай", "Qingdao", "Новороссийск", "40ft"): 5800,
    ("Китай", "Qingdao", "Санкт-Петербург", "20ft"): 4300,
    ("Китай", "Qingdao", "Санкт-Петербург", "40ft"): 6100,
    ("Китай", "Qingdao", "Владивосток", "20ft"): 2400,
    ("Китай", "Qingdao", "Владивосток", "40ft"): 3400,

    ("Китай", "Shanghai", "Новороссийск", "20ft"): 4200,
    ("Китай", "Shanghai", "Новороссийск", "40ft"): 6000,
    ("Китай", "Shanghai", "Санкт-Петербург", "20ft"): 4500,
    ("Китай", "Shanghai", "Санкт-Петербург", "40ft"): 6300,
    ("Китай", "Shanghai", "Владивосток", "20ft"): 2500,
    ("Китай", "Shanghai", "Владивосток", "40ft"): 3600,

    ("Китай", "Ningbo", "Новороссийск", "20ft"): 4200,
    ("Китай", "Ningbo", "Новороссийск", "40ft"): 6000,
    ("Китай", "Ningbo", "Санкт-Петербург", "20ft"): 4500,
    ("Китай", "Ningbo", "Санкт-Петербург", "40ft"): 6300,
    ("Китай", "Ningbo", "Владивосток", "20ft"): 2500,
    ("Китай", "Ningbo", "Владивосток", "40ft"): 3600,

    ("Китай", "Foshan", "Новороссийск", "20ft"): 4400,
    ("Китай", "Foshan", "Новороссийск", "40ft"): 6300,
    ("Китай", "Foshan", "Санкт-Петербург", "20ft"): 4700,
    ("Китай", "Foshan", "Санкт-Петербург", "40ft"): 6600,
    ("Китай", "Foshan", "Владивосток", "20ft"): 2700,
    ("Китай", "Foshan", "Владивосток", "40ft"): 3800,
}

VAT_PCT_FIXED = 22.0

def get_default_freight(country: str, port_loading: str, port_discharge: str, container: str) -> float | None:
    return DEFAULT_FREIGHT_USD.get((country, port_loading, port_discharge, container))

def infer_hs_and_duty(product_type: str, finish: str) -> tuple[str, float]:
    """
    Возвращает (hs_code, duty_pct)
    По твоим правилам:
    - Керамогранит <0.5% водопоглощение:
        глазурованный 7.5%
        неглазурованный 12%
      HS (примечание): 69072100/69072200 (как базово)
    - Сантехника (унитазы): 6910900000, глазурованная (условно) 10%
    """
    if product_type == "Керамогранит":
        # Базовые HS (пока упрощённо)
        hs = "69072100" if finish == "Неглазурованный" else "69072200"
        duty = 12.0 if finish == "Неглазурованный" else 7.5
        return hs, duty

    if product_type == "Сантехника (унитазы)":
        hs = "6910900000"
        duty = 10.0
        return hs, duty

    # fallback
    return "", 0.0

def to_usd(amount: float, currency: str, usd_cny: float) -> float:
    """Конвертация суммы в USD. Сейчас поддерживаем USD и CNY."""
    if currency == "USD":
        return amount
    if currency == "CNY":
        # 1 USD = usd_cny CNY -> CNY / usd_cny = USD
        return amount / usd_cny if usd_cny else 0.0
    return amount

def calc_model(
    qty_m2: float,
    product_price_amount_per_m2: float,
    price_currency: str,
    usd_cny: float,
    freight_usd: float,
    insurance_usd: float,
    local_rub: float,
    usd_rub: float,
    duty_pct: float,
    vat_pct: float,
    incoterms: str,
):
    # 1) Стоимость товара (в валюте цены) -> USD
    goods_amount = qty_m2 * product_price_amount_per_m2
    goods_usd = to_usd(goods_amount, price_currency, usd_cny)

    # 2) Таможенная стоимость (упрощённо, но с учётом Инкотермс)
    # EXW/FOB: товар + фрахт + страховка
    # CIF/DAP: считаем, что фрахт/страховка уже включены в цену товара (в реальности нюансов больше)
    if incoterms in ["EXW", "FOB"]:
        customs_value_usd = goods_usd + freight_usd + insurance_usd
        freight_in_customs_usd = freight_usd
        insurance_in_customs_usd = insurance_usd
    else:  # CIF, DAP
        customs_value_usd = goods_usd
        freight_in_customs_usd = 0.0
        insurance_in_customs_usd = 0.0

    # 3) Пошлина (USD)
    duty_usd = customs_value_usd * (duty_pct / 100.0)

    # 4) НДС (USD) — упрощение: (тамож.стоимость + пошлина) * НДС
    vat_usd = (customs_value_usd + duty_usd) * (vat_pct / 100.0)

    # 5) Итого затраты (RUB)
    total_rub = (customs_value_usd + duty_usd + vat_usd) * usd_rub + local_rub

    # 6) Себестоимость за м² (RUB/м²)
    cost_rub_per_m2 = total_rub / qty_m2 if qty_m2 else 0.0

    return {
        "goods_usd": goods_usd,
        "customs_value_usd": customs_value_usd,
        "duty_usd": duty_usd,
        "vat_usd": vat_usd,
        "freight_in_customs_usd": freight_in_customs_usd,
        "insurance_in_customs_usd": insurance_in_customs_usd,
        "local_rub": local_rub,
        "total_rub": total_rub,
        "cost_rub_per_m2": cost_rub_per_m2,
    }

# --- Sidebar (ввод параметров) ---
with st.sidebar:
    st.header("Ввод данных")

    supplier = st.text_input("Фабрика / поставщик (как в инвойсе)", value="")

    # Важно: по умолчанию Индия первой
    country = st.selectbox("Страна", ["Индия", "Китай"], index=0)
    incoterms = st.selectbox("Инкотермс", ["EXW", "FOB", "CIF", "DAP"], index=1)

    transport = st.selectbox(
        "Тип доставки",
        ["Море (20фут.контейнер)", "Море (40фут.контейнер)", "ЖД", "Авто"],
        index=0
    )

    # --- Порты рядом ---
    st.subheader("Порты")
    col_p1, col_p2 = st.columns(2)

    with col_p1:
        if country == "Индия":
            port_loading = st.selectbox("Порт отгрузки", ["Mundra", "Nhava Sheva"], index=0)
        else:
            port_loading = st.selectbox("Порт отгрузки", ["Qingdao", "Shanghai", "Ningbo", "Foshan"], index=0)

    with col_p2:
        port_discharge = st.selectbox(
            "Порт выгрузки",
            ["Новороссийск", "Санкт-Петербург", "Владивосток"],
            index=0
        )

    # --- Курсы ---
    currency_rate = st.number_input("Курс USD→RUB", min_value=0.0, value=95.0, step=0.1)

    usd_cny = 0.0
    price_currency = "USD"
    if country == "Китай":
        usd_cny = st.number_input("Курс USD→CNY (RMB)", min_value=0.0, value=7.20, step=0.01)
        price_currency = st.selectbox("Валюта цены товара", ["CNY", "USD"], index=0)
    else:
        price_currency = "USD"

    st.divider()

    # --- Товар / партия ---
    st.subheader("Товар / партия")

    product_type = st.selectbox("Тип товара", ["Керамогранит", "Сантехника (унитазы)"], index=0)

    if product_type == "Керамогранит":
        finish = st.selectbox("Поверхность/тип", ["Глазурованный", "Неглазурованный"], index=0)
        st.caption("Керамогранит <0,5% водопоглощение: глазур. 7,5% / неглазур. 12%")
    else:
        finish = st.selectbox("Поверхность/тип", ["Глазурованный"], index=0)
        st.caption("Сантехника (унитазы): 10%")

    # Автоподстановка HS и пошлины
    hs_auto, duty_auto = infer_hs_and_duty(product_type, "Неглазурованный" if finish == "Неглазурованный" else "Глазурованный")

    hs_code = st.text_input("Код ТН ВЭД (HS Code)", value=hs_auto)

    manual_duty = st.checkbox("Ручная ставка пошлины", value=False)
    if manual_duty:
        duty_pct = st.number_input("Пошлина, %", min_value=0.0, value=float(duty_auto), step=0.5)
    else:
        duty_pct = float(duty_auto)
        st.text_input("Пошлина, % (авто)", value=f"{duty_pct:.2f}", disabled=True)

    # НДС всегда 22%
    st.text_input("НДС, % (фикс)", value=f"{VAT_PCT_FIXED:.2f}", disabled=True)

    qty_m2 = st.number_input("Кол-во, м²", min_value=0.0, value=1200.0, step=10.0)

    price_label = f"Цена товара, {price_currency}/м²"
    product_price_amount_per_m2 = st.number_input(price_label, min_value=0.0, value=7.5 if price_currency == "USD" else 55.0, step=0.1)

    st.divider()

    # --- Логистика ---
    st.subheader("Логистика")

    is_sea_20 = (transport == "Море (20фут.контейнер)")
    is_sea_40 = (transport == "Море (40фут.контейнер)")
    is_sea = is_sea_20 or is_sea_40

    container = "20ft" if is_sea_20 else ("40ft" if is_sea_40 else "")

    use_default_freight = False
    default_freight = None
    if is_sea:
        default_freight = get_default_freight(country, port_loading, port_discharge, container)
        use_default_freight = st.checkbox("Использовать дефолтную ставку фрахта", value=True)

        if default_freight is None:
            st.warning("Для выбранного направления нет дефолтной ставки. Введи фрахт вручную.")
            use_default_freight = False
        else:
            st.caption(f"Дефолтный фрахт ({country}, {port_loading} → {port_discharge}, {container}): {default_freight:,.0f} USD")

    if is_sea and use_default_freight and default_freight is not None:
        freight_usd = st.number_input(
            "Фрахт/доставка, USD (на всю партию)",
            min_value=0.0,
            value=float(default_freight),
            step=50.0
        )
    else:
        freight_usd = st.number_input("Фрахт/доставка, USD (на всю партию)", min_value=0.0, value=4500.0, step=50.0)

    insurance_usd = st.number_input("Страхование, USD", min_value=0.0, value=0.0, step=10.0)
    local_rub = st.number_input("Локальные расходы РФ, RUB", min_value=0.0, value=300000.0, step=10000.0)

    calc = st.button("Рассчитать", type="primary")

# --- Расчёт ---
if calc:
    res = calc_model(
        qty_m2=qty_m2,
        product_price_amount_per_m2=product_price_amount_per_m2,
        price_currency=price_currency,
        usd_cny=usd_cny if country == "Китай" else 0.0,
        freight_usd=freight_usd,
        insurance_usd=insurance_usd,
        local_rub=local_rub,
        usd_rub=currency_rate,
        duty_pct=duty_pct,
        vat_pct=VAT_PCT_FIXED,
        incoterms=incoterms,
    )

    st.subheader("Параметры партии")
    p1, p2, p3, p4 = st.columns(4)
    p1.write(f"**Фабрика:** {supplier or '—'}")
    p2.write(f"**Страна:** {country}")
    p3.write(f"**Инкотермс:** {incoterms}")
    p4.write(f"**Доставка:** {transport}")

    p5, p6, p7, p8 = st.columns(4)
    p5.write(f"**Порт отгрузки:** {port_loading}")
    p6.write(f"**Порт выгрузки:** {port_discharge}")
    p7.write(f"**Тип товара:** {product_type}")
    p8.write(f"**HS Code:** {hs_code or '—'}")

    st.divider()

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Товар, USD", f"{res['goods_usd']:,.2f}")
    c2.metric("Тамож. стоимость, USD", f"{res['customs_value_usd']:,.2f}")
    c3.metric("Пошлина, USD", f"{res['duty_usd']:,.2f}")
    c4.metric("НДС (22%), USD", f"{res['vat_usd']:,.2f}")

    st.caption(
        f"В тамож.стоимости учтены фрахт/страховка: "
        f"{res['freight_in_customs_usd']:,.0f} / {res['insurance_in_customs_usd']:,.0f} USD "
        f"(логика зависит от Инкотермс)."
    )

    st.divider()
    c5, c6, c7 = st.columns([1, 1, 1])
    c5.metric("Итого затраты, RUB", f"{res['total_rub']:,.0f}")
    c6.metric("Себестоимость, RUB/м²", f"{res['cost_rub_per_m2']:,.2f}")
    c7.metric("Локальные расходы РФ, RUB", f"{local_rub:,.0f}")

    st.info(
        "Дальше можно расширять модель: раздельные сценарии по ЖД/Авто, СВХ/брокер, "
        "нормальные формулы по Инкотермс, таблица ставок пошлины по HS, "
        "и более точные дефолты фрахта по линиям."
    )
else:
    st.write("Заполни параметры слева и нажми **Рассчитать**.")
