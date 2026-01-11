
import streamlit as st

# =========================
# BRIS Logistics калькулятор
# =========================

st.set_page_config(
    page_title="BRIS Logistics калькулятор",
    layout="wide",
    page_icon="assets/bris_logo.png"
)

# -------------------------
# Единицы измерения
# -------------------------
unit = st.selectbox(
    "Ед. измерения",
    ["м2", "шт."],
    index=0
)

unit_sym = "м²" if unit == "м2" else "шт."

# -------------------------
# Ввод основных данных
# -------------------------
containers = st.number_input(
    "Количество контейнеров",
    min_value=1,
    value=1,
    step=1
)

freight_usd = st.number_input(
    "Фрахт, USD/конт.",
    value=2500.0,
    step=100.0
)

invoice_total_usd = st.number_input(
    "Общая стоимость по инвойсу, USD",
    value=0.0,
    step=100.0
)

# -------------------------
# Вознаграждение экспедитора и технического импортера (ВВОД)
# -------------------------
st.markdown("### Вознаграждение экспедитора и технического импортера")

expedition_service_usd = st.number_input(
    "Услуга по экспедированию / оформлению (USD/конт.)",
    value=100.0,
    step=10.0
)

agent_fee_pct = st.number_input(
    "Агентская комиссия по подбору O/F (% от фрахта)",
    value=10.0,
    step=0.5
)

factory_payment_pct = st.number_input(
    "Оплата на фабрику за клиента (% от инвойса)",
    value=2.0,
    step=0.5
)

# -------------------------
# Формулы (1–3)
# -------------------------
expedition_service_total = expedition_service_usd * containers
agent_fee_total = (agent_fee_pct / 100) * freight_usd * containers
factory_payment_total = (factory_payment_pct / 100) * invoice_total_usd

# -------------------------
# Локальные расходы РФ (пример)
# -------------------------
local_rf_total = st.number_input(
    "Локальные расходы в РФ всего, RUB",
    value=24000.0,
    step=1000.0
)

usd_rub_rate = st.number_input(
    "Курс USD → RUB",
    value=95.0,
    step=0.5
)

# -------------------------
# Печатная форма — итоги
# -------------------------
st.markdown("## Печатная форма")

with st.container():
    st.markdown("### Вознаграждение экспедитора и технического импортера")
    st.write(f"Услуга по экспедированию / оформлению, USD — {expedition_service_total:,.2f}")
    st.write(f"Агентская комиссия по подбору O/F, USD — {agent_fee_total:,.2f}")
    st.write(f"Оплата на фабрику за клиента, USD — {factory_payment_total:,.2f}")

# -------------------------
# Себестоимость с учетом всех расходов
# (Поля ввода скрыты)
# -------------------------
cost_all_usd_unit = 0.0
cost_all_rub_unit = 0.0

with st.container():
    st.markdown("### Себестоимость с учетом всех расходов")
    st.write(f"Себестоимость, USD/{unit_sym} — {cost_all_usd_unit:,.2f}")
    st.write(f"Себестоимость, RUB/{unit_sym} — {cost_all_rub_unit:,.2f}")
