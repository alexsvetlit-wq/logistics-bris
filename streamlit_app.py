import streamlit as st

# ----------------------------
# Config
# ----------------------------
st.set_page_config(
    page_title="Logistics калькулятор",
    layout="wide",
    page_icon="assets/bris_logo.png"
)

# ----------------------------
# Header with logo
# ----------------------------
col1, col2 = st.columns([1, 5])
with col1:
    st.image("assets/bris_logo.png", width=120)
with col2:
    st.title("Logistics калькулятор")
    st.caption("Черновик v0: логистика + таможня + себестоимость единицы товара")

# ----------------------------
# Dictionaries / presets
# ----------------------------
PORTS_BY_COUNTRY = {
    "Индия": ["Mundra", "Nhava Sheva (JNPT)", "Chennai", "Hazira", "Kandla"],
    "Китай": ["Qingdao", "Shanghai", "Ningbo", "Shenzhen (Yantian)", "Xiamen", "Tianjin"],
}

# Товары / HS / пошлина
PRODUCT_PRESETS = {
    "Керамогранит глазур.(<0.5%)": {
        "hs_code": "69072100",
        "duty_pct": 7.5,
    },
    "Керамогранит неглазур. (<0.5%)": {
        "hs_code": "69072200",
        "duty_pct": 12.0,
    },
    "Сантехника (унитазы/проч.) глазур.": {
        "hs_code": "6910900000",
        "duty_pct": 10.0,
    },
}

INCOTERMS = ["FOB", "EXW", "CIF", "DAP"]

TRANSPORTS = [
    "Море (20фут.контейнер)",
    "Море (40фут.контейнер)",
    "ЖД",
    "Авто",
]

# ----------------------------
# Sidebar inputs
# ----------------------------
with st.sidebar:
    st.header("Ввод данных")

    # 1) Поставщик/фабрика (из инвойса)
    factory_name = st.text_input("Фабрика / поставщик (как в инвойсе)", value="")

    country = st.selectbox("Страна", ["Китай", "Индия"])
    incoterms = st.selectbox("Инкотермс", INCOTERMS)

    transport = st.selectbox("Тип доставки", TRANSPORTS)

    # Порт отгрузки (логика по стране; по желанию можно показывать только для моря)
    port = st.selectbox("Порт отгрузки", PORTS_BY_COUNTRY.get(country, ["—"]))

    # Курсы
    currency_rate_usd_rub = st.number_input("Курс USD→RUB", min_value=0.0, value=95.0, step=0.1)

    # Если Китай — часто цена/инвойс в RMB, поэтому добавляем USD→RMB
    usd_to_rmb = None
    if country == "Китай":
        usd_to_rmb = st.number_input("Курс USD→RMB (CNY)", min_value=0.0, value=7.20, step=0.01)

    st.divider()

    # 2) Тип товара / HS / пошлина
    st.subheader("Классификация товара (ТН ВЭД / HS)")
    product_type = st.selectbox("Тип товара", list(PRODUCT_PRESETS.keys()))
    hs_code_default = PRODUCT_PRESETS[product_type]["hs_code"]
    duty_default = PRODUCT_PRESETS[product_type]["duty_pct"]

    hs_code = st.text_input("Код ТН ВЭД (HS Code)", value=hs_code_default)
    duty_pct = st.number_input("Пошлина, %", min_value=0.0, value=float(duty_default), step=0.5)

    # 3) НДС фиксированный
    vat_pct = 22.0
    st.text_input("НДС, % (фиксировано)", value=str(vat_pct), disabled=True)

    st.divider()

    # 4) Партия / товар
    st.subheader("Товар / партия")
    qty_m2 = st.number_input("Кол-во, м²", min_value=0.0, value=1200.0, step=10.0)

    # Цена товара: для Китая дадим выбор RMB или USD
    if country == "Китай":
        price_currency = st.radio("Валюта цены товара", ["RMB/м²", "USD/м²"], horizontal=True)
        if price_currency == "RMB/м²":
            product_price_rmb_per_m2 = st.number_input("Цена товара, RMB/м²", min_value=0.0, value=55.0, step=0.5)
            # Конвертация RMB -> USD через USD→RMB
            product_price_usd_per_m2 = (product_price_rmb_per_m2 / usd_to_rmb) if usd_to_rmb else 0.0
            st.caption(f"Пересчёт: ≈ {product_price_usd_per_m2:.3f} USD/м²")
        else:
            product_price_usd_per_m2 = st.number_input("Цена товара, USD/м²", min_value=0.0, value=7.5, step=0.1)
    else:
        product_price_usd_per_m2 = st.number_input("Цена товара, USD/м²", min_value=0.0, value=7.5, step=0.1)

    st.divider()

    # Логистика
    st.subheader("Логистика")

    # Фрахт/доставка показываем только для моря (как ты просил)
    is_sea = transport.startswith("Море")
    if is_sea:
        freight_usd = st.number_input("Фрахт, USD (на всю партию)", min_value=0.0, value=4500.0, step=50.0)
        insurance_usd = st.number_input("Страхование, USD", min_value=0.0, value=0.0, step=10.0)
    else:
        freight_usd = 0.0
        insurance_usd = 0.0
        st.caption("Фрахт/страхование скрыты: они учитываются только для доставки морем.")

    local_rub = st.number_input("Локальные расходы РФ, RUB", min_value=0.0, value=300000.0, step=10000.0)

    calc = st.button("Рассчитать", type="primary")

# ----------------------------
# Calculation model
# ----------------------------
def calc_model(
    qty_m2: float,
    product_price_usd_per_m2: float,
    freight_usd: float,
    insurance_usd: float,
    local_rub: float,
    usd_rub: float,
    duty_pct: float,
    vat_pct: float,
    incoterms: str,
):
    # 1) Стоимость товара (USD)
    goods_usd = qty_m2 * product_price_usd_per_m2

    # 2) Таможенная стоимость (упрощенно, но с логикой инкотермс)
    #    - CIF / DAP обычно уже включают доставку (в этой v0 примем, что freight+insurance уже "внутри")
    #    - EXW / FOB: добавляем freight+insurance
    if incoterms in ("CIF", "DAP"):
        customs_value_usd = goods_usd
        freight_in_customs = 0.0
        insurance_in_customs = 0.0
    else:
        customs_value_usd = goods_usd + freight_usd + insurance_usd
        freight_in_customs = freight_usd
        insurance_in_customs = insurance_usd

    # 3) Пошлина (USD)
    duty_usd = customs_value_usd * (duty_pct / 100.0)

    # 4) НДС (USD): (тамож.стоимость + пошлина) * НДС
    vat_usd = (customs_value_usd + duty_usd) * (vat_pct / 100.0)

    # 5) Итого затраты (RUB)
    total_rub = (customs_value_usd + duty_usd + vat_usd) * usd_rub + local_rub

    # 6) Себестоимость за м² (RUB/м²)
    cost_rub_per_m2 = total_rub / qty_m2 if qty_m2 else 0.0

    return {
        "goods_usd": goods_usd,
        "customs_value_usd": customs_value_usd,
        "freight_in_customs": freight_in_customs,
        "insurance_in_customs": insurance_in_customs,
        "duty_usd": duty_usd,
        "vat_usd": vat_usd,
        "local_rub": local_rub,
        "total_rub": total_rub,
        "cost_rub_per_m2": cost_rub_per_m2,
    }

# ----------------------------
# Output
# ----------------------------
if calc:
    res = calc_model(
        qty_m2=qty_m2,
        product_price_usd_per_m2=product_price_usd_per_m2,
        freight_usd=freight_usd,
        insurance_usd=insurance_usd,
        local_rub=local_rub,
        usd_rub=currency_rate_usd_rub,
        duty_pct=duty_pct,
        vat_pct=vat_pct,
        incoterms=incoterms,
    )

    st.subheader("Параметры расчёта")
    p1, p2, p3, p4 = st.columns(4)
    p1.write(f"**Фабрика:** {factory_name or '—'}")
    p2.write(f"**Страна:** {country}")
    p3.write(f"**Инкотермс:** {incoterms}")
    p4.write(f"**Доставка:** {transport}")

    p5, p6, p7, p8 = st.columns(4)
    p5.write(f"**Порт:** {port}")
    p6.write(f"**Товар:** {product_type}")
    p7.write(f"**HS Code:** `{hs_code}`")
    p8.write(f"**Пошлина:** {duty_pct:.2f}%  |  **НДС:** {vat_pct:.2f}%")

    st.divider()

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Товар, USD", f"{res['goods_usd']:,.2f}")
    c2.metric("Тамож. стоимость, USD", f"{res['customs_value_usd']:,.2f}")
    c3.metric("Пошлина, USD", f"{res['duty_usd']:,.2f}")
    c4.metric("НДС, USD", f"{res['vat_usd']:,.2f}")

    st.caption(
        f"В таможенную стоимость включено: фрахт {res['freight_in_customs']:,.2f} USD, "
        f"страхование {res['insurance_in_customs']:,.2f} USD (по логике инкотермс)."
    )

    st.divider()

    c5, c6 = st.columns([1, 1])
    c5.metric("Итого затраты, RUB", f"{res['total_rub']:,.0f}")
    c6.metric("Себестоимость, RUB/м²", f"{res['cost_rub_per_m2']:,.2f}")

    st.info(
        "v0 — упрощённая модель. Дальше можно добавить: брокера/СВХ, ЖД-плечо отдельно, "
        "калькуляцию на контейнер (20/40) с нормами загрузки, сценарии по HS/ставкам более детально, "
        "и автоподтягивание параметров из инвойса."
    )
else:
    st.write("Заполни параметры слева и нажми **Рассчитать**.")
