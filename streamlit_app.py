import streamlit as st

# =========================
# BRIS Logistics калькулятор
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
    st.caption("Логистика + таможня + себестоимость единицы товара")

VAT_PCT_FIXED = 22.0

# =========================
# Вспомогательные функции
# =========================

def convert_to_usd(amount, currency, usd_cny, usd_inr):
    if currency == "USD":
        return amount
    if currency == "CNY":
        return amount / usd_cny if usd_cny else 0
    if currency == "INR":
        return amount / usd_inr if usd_inr else 0
    return amount


def infer_hs_and_duty(product_type, finish):
    if product_type == "Керамогранит":
        if finish == "Неглазурованный":
            return "69072100", 12.0
        return "69072200", 7.5

    if product_type == "Сантехника (унитазы)":
        return "6910900000", 10.0

    return "", 0.0


def calc_model(
    qty,
    price_per_unit,
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
):
    goods_amount = qty * price_per_unit
    goods_usd = convert_to_usd(goods_amount, price_currency, usd_cny, usd_inr)

    if incoterms in ["EXW", "FOB"]:
        customs_value_usd = goods_usd + freight_usd + insurance_usd
    else:
        customs_value_usd = goods_usd

    duty_usd = customs_value_usd * duty_pct / 100
    vat_usd = (customs_value_usd + duty_usd) * vat_pct / 100

    total_rub = (customs_value_usd + duty_usd + vat_usd) * usd_rub + local_rub
    cost_per_unit = total_rub / qty if qty else 0

    return {
        "goods_usd": goods_usd,
        "customs_value_usd": customs_value_usd,
        "duty_usd": duty_usd,
        "vat_usd": vat_usd,
        "total_rub": total_rub,
        "cost_per_unit": cost_per_unit,
    }


# =========================
# Sidebar
# =========================

with st.sidebar:
    st.header("Ввод данных")

    supplier = st.text_input("Фабрика / поставщик (как в инвойсе)")

    country = st.selectbox("Страна", ["Индия", "Китай"], index=0)
    incoterms = st.selectbox("Инкотермс", ["EXW", "FOB", "CIF", "DAP"], index=1)

    transport = st.selectbox(
        "Тип доставки",
        ["Море (20фут.контейнер)", "Море (40фут.контейнер)", "ЖД", "Авто"]
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
        usd_cny = st.number_input("Курс USD→CNY (RMB)", value=7.2, step=0.01)
        price_currency = st.selectbox("Валюта цены товара", ["CNY", "USD"], index=0)
    else:
        usd_inr = st.number_input("Курс USD→INR", value=83.0, step=0.1)
        price_currency = st.selectbox("Валюта цены товара", ["USD", "INR"], index=0)

    st.divider()

    # --- Товар ---
    st.subheader("Товар / партия")

    product_type = st.selectbox(
        "Тип товара",
        ["Керамогранит", "Сантехника (унитазы)"]
    )

    if product_type == "Керамогранит":
        finish = st.selectbox("Поверхность", ["Глазурованный", "Неглазурованный"])
    else:
        finish = "Глазурованный"

    hs_auto, duty_auto = infer_hs_and_duty(product_type, finish)

    st.text_input("Код ТН ВЭД (HS Code)", value=hs_auto)
    duty_pct = st.number_input("Пошлина, %", value=duty_auto, step=0.5)
    st.text_input("НДС, % (фикс)", value=str(VAT_PCT_FIXED), disabled=True)

    # ====== ВАЖНОЕ НОВОЕ ======
    unit = st.selectbox("Единица измерения", ["м²", "шт"])

    qty_label = f"Кол-во, {unit}"
    qty = st.number_input(qty_label, value=1200.0, step=10.0)

    price_label = f"Цена товара, {price_currency}/{unit}"
    price_per_unit = st.number_input(price_label, value=7.5, step=0.1)

    st.divider()

    # --- Логистика ---
    st.subheader("Логистика")
    freight_usd = st.number_input("Фрахт, USD", value=4500.0, step=50.0)
    insurance_usd = st.number_input("Страхование, USD", value=0.0, step=10.0)
    local_rub = st.number_input("Локальные расходы РФ, RUB", value=300000.0, step=10000.0)

    calc = st.button("Рассчитать", type="primary")


# =========================
# Результат
# =========================

if calc:
    res = calc_model(
        qty,
        price_per_unit,
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
    )

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Товар, USD", f"{res['goods_usd']:,.2f}")
    c2.metric("Тамож. стоимость, USD", f"{res['customs_value_usd']:,.2f}")
    c3.metric("Пошлина, USD", f"{res['duty_usd']:,.2f}")
    c4.metric("НДС 22%, USD", f"{res['vat_usd']:,.2f}")

    st.divider()
    c5, c6 = st.columns(2)
    c5.metric("Итого затраты, RUB", f"{res['total_rub']:,.0f}")
    c6.metric(f"Себестоимость, RUB/{unit}", f"{res['cost_per_unit']:,.2f}")

else:
    st.write("Заполни параметры слева и нажми **Рассчитать**.")
