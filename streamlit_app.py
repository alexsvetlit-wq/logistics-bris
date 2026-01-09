import streamlit as st

# =========================
# BRIS Logistics калькулятор (v0+)
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

VAT_PCT_FIXED = 22.0

# =========================
# Формат чисел (ЕДИНСТВЕННОЕ ДОБАВЛЕНИЕ)
# =========================
def fmt(num):
    return f"{num:,.2f}".replace(",", " ").replace(".", ",")

# =========================
# (Блок 1) Дефолтные ставки фрахта по портам
# =========================

FREIGHT_DEFAULTS = {
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

    ("Китай", "Qingdao", "Новороссийск", "20"): 4200.0,
    ("Китай", "Qingdao", "Санкт-Петербург", "20"): 4800.0,
    ("Китай", "Qingdao", "Владивосток", "20"): 2600.0,

    ("Китай", "Qingdao", "Новороссийск", "40"): 5800.0,
    ("Китай", "Qingdao", "Санкт-Петербург", "40"): 6500.0,
    ("Китай", "Qingdao", "Владивосток", "40"): 3400.0,
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
):
    goods_amount = qty_m2 * price_per_m2
    goods_usd = convert_to_usd(goods_amount, price_currency, usd_cny, usd_inr)

    if incoterms in ["EXW", "FOB"]:
        customs_value_usd = goods_usd + freight_usd + insurance_usd
    else:
        customs_value_usd = goods_usd

    duty_usd = customs_value_usd * duty_pct / 100
    vat_usd = (customs_value_usd + duty_usd) * vat_pct / 100

    total_rub = (customs_value_usd + duty_usd + vat_usd) * usd_rub + local_rub
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
# Sidebar (БЕЗ ИЗМЕНЕНИЙ)
# =========================

with st.sidebar:
    st.header("Ввод данных")

    supplier = st.text_input("Фабрика / поставщик (как в инвойсе)")
    country = st.selectbox("Страна", ["Индия", "Китай"], index=0)
    incoterms = st.selectbox("Инкотермс", ["EXW", "FOB", "CIF", "DAP"], index=1)
    transport = st.selectbox("Тип доставки", ["Море (20фут.контейнер)", "Море (40фут.контейнер)"])

    currency_rate = st.number_input("Курс USD→RUB", value=95.0, step=0.1)

    usd_cny = 0.0
    usd_inr = 0.0

    if country == "Китай":
        usd_cny = st.number_input("Курс USD→CNY", value=7.2)
        price_currency = "CNY"
    else:
        usd_inr = st.number_input("Курс USD→INR", value=83.0)
        price_currency = "USD"

    st.divider()

    qty_m2 = st.number_input("Кол-во, м²", value=1200.0)
    price_per_m2 = st.number_input("Цена товара, USD/м²", value=7.5)

    freight_usd = st.number_input("Фрахт, USD", value=2500.0)
    insurance_usd = st.number_input("Страхование, USD", value=0.0)
    local_rub = st.number_input("Локальные расходы РФ, RUB", value=300000.0)

    product_type = st.selectbox("Тип товара", ["Керамогранит", "Сантехника (унитазы)"])
    finish = st.selectbox("Поверхность", ["Глазурованный", "Неглазурованный"])

    _, duty_pct = infer_hs_and_duty(product_type, finish)

    calc = st.button("Рассчитать", type="primary")

# =========================
# Результат (ТОЛЬКО ФОРМАТ)
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
    )

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Товар, USD", fmt(res["goods_usd"]))
    c2.metric("Тамож. стоимость, USD", fmt(res["customs_value_usd"]))
    c3.metric("Пошлина, USD", fmt(res["duty_usd"]))
    c4.metric("НДС 22%, USD", fmt(res["vat_usd"]))

    st.divider()
    c5, c6 = st.columns(2)
    c5.metric("Итого затраты, RUB", fmt(res["total_rub"]))
    c6.metric("Себестоимость, RUB/м²", fmt(res["cost_rub_m2"]))

else:
    st.write("Заполни параметры слева и нажми **Рассчитать**.")
