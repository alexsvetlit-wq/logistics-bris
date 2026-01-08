import streamlit as st

st.set_page_config(page_title="BRIS Logistics калькулятор", layout="wide")

st.title("BRIS Logistics калькулятор")
st.caption("Черновик v0: логистика + таможня + себестоимость единицы товара")

# --- Sidebar (ввод параметров) ---
with st.sidebar:
    st.header("Ввод данных")

    country = st.selectbox("Страна", ["Китай", "Индия"])
    incoterms = st.selectbox("Инкотермс", ["EXW", "FOB", "CIF", "DAP"])
    transport = st.selectbox("Тип доставки", ["Море (контейнер)", "ЖД", "Авто"])
    currency_rate = st.number_input("Курс USD→RUB", min_value=0.0, value=95.0, step=0.1)

    st.divider()
    st.subheader("Товар / партия")
    qty_m2 = st.number_input("Кол-во, м²", min_value=0.0, value=1200.0, step=10.0)
    product_price_usd_per_m2 = st.number_input("Цена товара, USD/м²", min_value=0.0, value=7.5, step=0.1)

    st.divider()
    st.subheader("Логистика")
    freight_usd = st.number_input("Фрахт/доставка, USD (на всю партию)", min_value=0.0, value=4500.0, step=50.0)
    insurance_usd = st.number_input("Страхование, USD", min_value=0.0, value=0.0, step=10.0)
    local_rub = st.number_input("Локальные расходы РФ, RUB", min_value=0.0, value=300000.0, step=10000.0)

    st.divider()
    st.subheader("Таможня (упрощённо)")
    duty_pct = st.number_input("Пошлина, %", min_value=0.0, value=10.0, step=0.5)
    vat_pct = st.number_input("НДС, %", min_value=0.0, value=20.0, step=0.5)

    calc = st.button("Рассчитать", type="primary")

# --- Расчёт ---
def calc_model(
    qty_m2: float,
    product_price_usd_per_m2: float,
    freight_usd: float,
    insurance_usd: float,
    local_rub: float,
    usd_rub: float,
    duty_pct: float,
    vat_pct: float,
):
    # 1) Стоимость товара (USD)
    goods_usd = qty_m2 * product_price_usd_per_m2

    # 2) Таможенная стоимость (очень упрощённо): товар + фрахт + страховка (USD)
    customs_value_usd = goods_usd + freight_usd + insurance_usd

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
        "local_rub": local_rub,
        "total_rub": total_rub,
        "cost_rub_per_m2": cost_rub_per_m2,
    }

if calc:
    res = calc_model(
        qty_m2=qty_m2,
        product_price_usd_per_m2=product_price_usd_per_m2,
        freight_usd=freight_usd,
        insurance_usd=insurance_usd,
        local_rub=local_rub,
        usd_rub=currency_rate,
        duty_pct=duty_pct,
        vat_pct=vat_pct,
    )

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Товар, USD", f"{res['goods_usd']:,.2f}")
    c2.metric("Тамож. стоимость, USD", f"{res['customs_value_usd']:,.2f}")
    c3.metric("Пошлина, USD", f"{res['duty_usd']:,.2f}")
    c4.metric("НДС, USD", f"{res['vat_usd']:,.2f}")

    st.divider()
    c5, c6 = st.columns([1, 1])
    c5.metric("Итого затраты, RUB", f"{res['total_rub']:,.0f}")
    c6.metric("Себестоимость, RUB/м²", f"{res['cost_rub_per_m2']:,.2f}")

    st.info("Это упрощённая модель v0. Дальше добавим раздельные сценарии Китай/Индия, контейнер/м², брокера, СВХ, ЖД-плечо и т.д.")
else:
    st.write("Заполни параметры слева и нажми **Рассчитать**.")
