import streamlit as st
import streamlit.components.v1 as components

# --- Sidebar collapse/expand buttons (fixed + sidebar bottom) ---
st.markdown(
    '''
    <style>
      .sidebar-toggle-fixed {
        position: fixed;
        left: 8px;
        bottom: 12px;
        z-index: 9999;
        background: #f3f4f6;
        border: 1px solid #d1d5db;
        border-radius: 10px;
        padding: 6px 10px;
        cursor: pointer;
        font-size: 16px;
        user-select: none;
      }
      .sidebar-toggle-fixed:hover { filter: brightness(0.98); }
      .sidebar-toggle-bottom {
        width: 100%;
        display: flex;
        justify-content: center;
        padding-top: 6px;
      }
      .sidebar-toggle-bottom button{
        width: 100%;
        border-radius: 10px;
        border: 1px solid #d1d5db;
        background: #f3f4f6;
        padding: 6px 10px;
        cursor: pointer;
        font-size: 16px;
      }
    </style>
    <script>
      function _getSidebarEl(){
        return window.parent.document.querySelector('section[data-testid="stSidebar"]');
      }
      function _isCollapsed(sidebar){
        return sidebar && (sidebar.style.display === 'none' || sidebar.style.width === '0px');
      }
      function _setToggleIcon(){
        const sidebar = _getSidebarEl();
        const btn = window.parent.document.getElementById('sidebarToggleFixed');
        if(!btn) return;
        btn.textContent = _isCollapsed(sidebar) ? '»' : '«';
      }
      function toggleSidebar(){
        // Prefer Streamlit native collapse control (stable)
        const doc = window.parent?.document || document;
        const ctl = doc.querySelector('button[data-testid="collapsedControl"]');
        if (ctl) { ctl.click(); return; }

        // Fallback (older Streamlit DOM)
        const alt = doc.querySelector('button[aria-label="Close sidebar"], button[aria-label="Open sidebar"]');
        if (alt) { alt.click(); return; }

        // Last-resort fallback: direct style manipulation
        const sidebar = doc.querySelector('section[data-testid="stSidebar"]');
        if (!sidebar) return;
        const collapsed = (sidebar.style.display === 'none' || sidebar.style.width === '0px');
        if (collapsed) {
          sidebar.style.display = '';
          sidebar.style.width = '';
          sidebar.style.minWidth = '';
        } else {
          sidebar.style.width = '0px';
          sidebar.style.minWidth = '0px';
          sidebar.style.display = 'none';
        }
      }
      // expose for other components
      try { window.toggleSidebar = toggleSidebar; } catch(e) {}
      try { window.parent.toggleSidebar = toggleSidebar; } catch(e) {}
      try { window.top.toggleSidebar = toggleSidebar; } catch(e) {}
      // listen for toggle requests from other frames
      try {
        window.addEventListener('message', (ev) => {
          if (ev && ev.data === 'toggleSidebar') {
            try { toggleSidebar(); } catch(e) {}
          }
        });
      } catch(e) {}
      // init icon
      setTimeout(_setToggleIcon, 300);
    </script>
    <div id="sidebarToggleFixed" class="sidebar-toggle-fixed" onclick="try{(window.parent||window.top||window).parent.document.querySelector('section[data-testid="stSidebar"]').scrollTo({top:0,behavior:'smooth'});}catch(e){}">«</div>
    ''',
    unsafe_allow_html=True
)


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
    st.title("Logistics калькулятор")
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
    exp_commission_pct,
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

    # Оплата на фабрику за клиента (% от инвойса)
    factory_pay_usd = invoice_usd * (exp_factory_pay_rub / 100.0)

    customs_value_usd = invoice_usd + (freight_usd * float(containers_qty))

    # Агентская комиссия = % × фрахт × количество контейнеров
    exp_commission_usd = freight_usd * float(containers_qty) * (exp_commission_pct / 100.0)

    # Услуга по экспедированию / оформлению = 100 USD × количество контейнеров
    exp_service_usd = exp_service_rub * float(containers_qty)

    # Сумма вознаграждений (USD)
    fees_usd = exp_service_usd + exp_commission_usd + factory_pay_usd

    # 3) Пошлина (как было)
    duty_usd = customs_value_usd * duty_pct / 100

    # 4) НДС 22% + Ставка 2026 (НОВАЯ ФОРМУЛА):
    # НДС_RUB = (Тамож.стоимость_USD + Пошлина_USD) × курс × 22% + ставка_2026(RUB)
    customs_value_rub = customs_value_usd * usd_rub
    vat_fee_rub = vat_fee_2026_rub(customs_value_rub)

    vat_rub = (customs_value_usd + duty_usd) * usd_rub * (vat_pct / 100) + vat_fee_rub
    vat_usd = (vat_rub / usd_rub) if usd_rub else 0.0  # для отображения в USD

    # Итого затраты с учетом всех расходов (USD)
    total_usd_all = (customs_value_usd + duty_usd + vat_usd) + (insurance_usd * containers_qty) + fees_usd

    # Итого затраты с учетом всех расходов (RUB)
    total_rub_all = (total_usd_all * usd_rub) + local_rub

    # 5) Итого затраты (RUB) — учитываем НДС в рублях
    total_rub = (
    (customs_value_usd + duty_usd + vat_usd) * usd_rub
    + local_rub
    + insurance_usd * containers_qty * usd_rub
)


    # 6) Себестоимость за м² (RUB/м²)
    cost_rub_m2 = total_rub / qty_m2 if qty_m2 else 0

    # Себестоимость с учетом всех расходов
    cost_all_usd_m2 = total_usd_all / qty_m2 if qty_m2 else 0
    cost_all_rub_m2 = total_rub_all / qty_m2 if qty_m2 else 0

    return {
        "goods_usd": goods_usd,
        "customs_value_usd": customs_value_usd,
        "duty_usd": duty_usd,
        "vat_usd": vat_usd,
        "factory_pay_usd": factory_pay_usd,
        "exp_commission_usd": exp_commission_usd,
        "exp_service_usd": exp_service_usd,
        "total_rub": total_rub,
        "cost_rub_m2": cost_rub_m2,
        "fees_usd": fees_usd,
        "total_usd_all": total_usd_all,
        "total_rub_all": total_rub_all,
        "cost_all_usd_m2": cost_all_usd_m2,
        "cost_all_rub_m2": cost_all_rub_m2,
    }


# =========================
# Sidebar
# =========================

with st.sidebar:
    st.header("Ввод данных")

    # Быстрая кнопка расчёта (дублирует нижнюю)
    calc_top = st.button("Рассчитать", type="primary", key="calc_top")



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
    currency_rate = st.number_input("Курс ЦБ+2% конвертация USD→RUB", value=95.0, step=0.1)

    usd_cny = 0.0
    usd_inr = 0.0

    if country == "Китай":
        usd_cny = st.number_input("Курс ЦБ+2% конвертация USD→CNY (RMB)", value=7.20, step=0.01)
        price_currency = st.selectbox("Валюта цены товара", ["CNY", "USD"], index=0)

    elif country == "Индия":
        usd_inr = st.number_input("Курс ЦБ+2% конвертация USD→INR", value=83.0, step=0.1)
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
    unit_sym = "м²" if str(unit).strip() in ["м²", "м2", "m2", "m²"] else "шт."

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
        "Локальные расходы в РФ всего , RUB",
        value=24000.0,
        step=1000.0
    )

    # =========================
    # (Блок ввода) Вознаграждение экспедитора и технического импортера (для печатной формы)
    # =========================
    st.markdown("### Вознаграждение экспедитора и технического импортера")
    exp_service_rub = st.number_input(
        "Услуга по экспедированию / оформлению (100USD/ктк),USD",
        value=100.0,
        step=100.0
    )
    exp_commission_pct = st.number_input(
        "Агентская комиссия от подбора фрахта O/F (Ocean Freight) (10% от O/F/ктк),USD",
        value=10.0,
        step=0.5
    )
    exp_factory_pay_rub = st.number_input(
        "Оплата на фабрику за клиента (% от стоимости инвойса), %",
        value=2.0,
        step=0.1
    )

    # =========================
    # (Блок ввода) Себестоимость с учетом всех расходов (для печатной формы)
    # =========================
    st.markdown("### Себестоимость с учетом всех расходов")
    cost_all_usd_m2_input = st.number_input(
        f"Себестоимость, USD/{unit_sym} (с учетом всех расходов)",
        value=0.0,
        step=0.1
    )
    cost_all_rub_m2_input = st.number_input(
        f"Себестоимость, RUB/{unit_sym} (с учетом всех расходов)",
        value=0.0,
        step=10.0
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
    local_costs_rub = local_costs_rub_input  # вручную (НЕ зависит от детализации ниже)
    local_rub = local_costs_rub  # совместимость с calc_model(..., local_rub, ...)

    st.caption(
        "В расчёте используется: ручной ввод"
    )


    # =========================
    # Печать: какие блоки показывать в печатной форме
    # =========================
    st.subheader("Печать (настройки)")
    print_show_rewards = st.checkbox(
        "Печатать блок: Вознаграждения (экспедитор/декларант/тех.импортер)",
        value=True,
        key="print_show_rewards",
    )
    print_show_cost_all = st.checkbox(
        "Печатать блок: Себестоимость с учетом всех расходов",
        value=True,
        key="print_show_cost_all",
    )


    
    # Кнопка сворачивания панели (дублирует фиксированную, симметричная)
    st.markdown(
        '''
        <div style="position:relative; width:100%; height:36px; margin-top:8px;">
          <div onclick="try{(window.parent||window.top||window).parent.document.querySelector('section[data-testid="stSidebar"]').scrollTo({top:0,behavior:'smooth'});}catch(e){}"
               style="
                 position:absolute;
                 right:6px;
                 bottom:0;
                 width:32px;
                 height:32px;
                 display:flex;
                 align-items:center;
                 justify-content:center;
                 background:#f3f4f6;
                 border:1px solid #d1d5db;
                 border-radius:8px;
                 cursor:pointer;
                 font-size:16px;
                 user-select:none;">
            «
          </div>
        </div>
        ''',
        unsafe_allow_html=True
    )

    calc_bottom = st.button("Рассчитать", type="primary", key="calc_bottom")

    # Триггер расчёта (верхняя или нижняя кнопка)
    calc = bool(calc_top or calc_bottom)

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
        exp_commission_pct,
    )

    # =========================
    # Контроль: товар (qty × price) vs инвойс — сравнение по целым USD
    # =========================
    goods_usd_int = int(res.get("goods_usd", 0))
    # invoice_usd считаем заново для контроля (инвойс не участвует в расчёте товара)
    if invoice_currency == "RUB":
        invoice_usd_ctrl = int((invoice_total / currency_rate)) if currency_rate else 0
    else:
        invoice_usd_ctrl = int(convert_to_usd(invoice_total, invoice_currency, usd_cny, usd_inr))

    if goods_usd_int != invoice_usd_ctrl:
        st.warning(
            f"⚠️ Контроль: расчёт товара {goods_usd_int} USD "
            f"не совпадает с инвойсом {invoice_usd_ctrl} USD"
        )

    with st.expander("Сводка расчёта", expanded=True):
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Товар, USD", f"{res['goods_usd']:,.2f}")
        c2.metric("Тамож. стоимость, USD", f"{res['customs_value_usd']:,.2f}")
        c3.metric("Пошлина, USD", f"{res['duty_usd']:,.2f}")
        c4.metric("НДС 22%+тамож.сбор, USD", f"{res['vat_usd']:,.2f}")
    
        st.divider()
        c5, c6 = st.columns(2)
        c5.metric("Итого стоимость товара в НВРСК , RUB", f"{res['total_rub']:,.0f}")
        c6.metric(f"Себестоимость, RUB/{unit_sym}", f"{res['cost_rub_m2']:,.2f}")
    

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
            return f"{int(round(x)):,}".replace(",", " ")
        except Exception:
            return "—"

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
    ]

    # Детализация локальных расходов
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
        ("Локальные расходы в РФ, всего", local_costs_rub_input, "₽"),
        ("Итого стоимость товара в НВРСК, RUB", res["total_rub"], "₽"),
        (f"Себестоимость, RUB/{unit_sym}", res["cost_rub_m2"], "₽"),
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

    # --- Доп.блоки (условно печатаем) ---
    rewards_block_html = ""
    if print_show_rewards:
        rewards_block_html = f"""
      <div class="box">
        <h3>Вознаграждение экспедитора и технического импортера</h3>
        <table class="t totals">
          <tr>
            <td>Услуга по экспедированию / оформлению (100USD/ктк), USD</td>
            <td style="text-align:right">{_fmt_money(exp_service_rub, 2)} USD</td>
          </tr>
          <tr>
            <td>Агентская комиссия от подбора фрахта O/F (Ocean Freight), %</td>
            <td style="text-align:right">{_fmt_money(exp_commission_pct, 2)} %</td>
          </tr>
          <tr>
            <td>Оплата на фабрику за клиента (USD)</td>
            <td style="text-align:right">{_fmt_money(res.get("factory_pay_usd", 0.0), 2)} USD</td>
          </tr>
          <tr>
            <td>Сумма вознаграждений (USD)</td>
            <td style="text-align:right">{_fmt_money(res.get("fees_usd", 0.0), 2)} USD</td>
          </tr>
        </table>
      </div>
"""

    cost_all_block_html = ""
    if print_show_cost_all:
        cost_all_block_html = f"""
      <div class="box">
        <h3>Себестоимость с учетом всех расходов</h3>
        <table class="t totals">
          <tr>
            <td>Себестоимость, USD/{unit_sym}</td>
            <td style="text-align:right">{_fmt_money(res.get("cost_all_usd_m2", 0.0), 2)} USD/{unit_sym}</td>
          </tr>
          <tr>
            <td>Себестоимость, RUB/{unit_sym}</td>
            <td style="text-align:right">{_fmt_money(res.get("cost_all_rub_m2", 0.0), 2)} ₽/{unit_sym}</td>
          </tr>
        </table>
      </div>
"""

    _html_print = f"""<!doctype html>
<html>
<head>
  <meta charset="utf-8" />
  <style>
    @page {{
      size: A4 landscape;
      margin: 8mm;
    }}

    html, body {{
      padding: 0;
      margin: 0;
      font-family: Arial, Helvetica, sans-serif;
      color: #111;
      font-size: 12px;
      line-height: 1.2;
    }}

    @media screen {{
      body {{
        zoom: 1.25;
      }}
    }}

    .top {{
      display: flex;
      align-items: center;
      gap: 10px;
      margin-bottom: 4px;
    }}

    .logo {{
      height: 22px;
    }}

    .title {{
      font-size: 14px;
      font-weight: 700;
      margin: 0;
      padding: 0;
    }}

    .subtitle {{
      font-size: 9px;
      margin-top: 1px;
      color: #444;
    }}

    .grid {{
      display: flex;
      gap: 10px;
      align-items: flex-start;
    }}

    .left {{
      flex: 0 0 64%;
    }}

    .right {{
      flex: 0 0 36%;
    }}

    .box {{
      border: 1px solid #d9d9d9;
      border-radius: 6px;
      padding: 6px 8px;
      margin-bottom: 8px;
      break-inside: avoid;
      page-break-inside: avoid;
    }}

    .box h3 {{
      font-size: 10px;
      font-weight: 700;
      margin: 0 0 6px 0;
      padding: 0;
    }}

    table.t {{
      width: 100%;
      border-collapse: collapse;
    }}

    table.t td {{
      border-top: 1px solid #ededed;
      padding: 3px 0;
      vertical-align: top;
    }}

    table.t tr:first-child td {{
      border-top: none;
    }}

    table.t td:first-child {{
      color: #222;
      padding-right: 22px;
      width: 75%;
    }}

    table.t td:last-child {{
      text-align: right;
      white-space: nowrap;
      width: 25%;
    }}

    .totals td:first-child {{
      width: 78%;
    }}
    .totals td:last-child {{
      width: 22%;
    }}

    .footer {{
      position: fixed;
      bottom: 6mm;
      left: 8mm;
      right: 8mm;
      text-align: center;
      font-size: 8px;
      color: #666;
    }}
  </style>
</head>
<body>
  <div class="top">
    <img class="logo" src="assets/bris_logo.png" />
    <div>
      <div class="title">BRIS Logistics — расчёт себестоимости</div>
      <div class="subtitle">{country} • {incoterms} • {transport} • Контейнеров: {containers_qty}</div>
    </div>
  </div>

  <div class="grid">
    <div class="left">
      <div class="box">
        <h3>Вводные данные</h3>
        <table class="t">
          {_rows_left_html}
        </table>
      </div>

      <div class="box">
        <h3>Итоги</h3>
        <table class="t totals">
          {_rows_totals_html}
        </table>
      </div>

      {rewards_block_html}
      {cost_all_block_html}

      <div class="box">
        <h3>Расценки на прямые локальные расходы в РФ (актуализация на дату расчета)</h3>
        <table class="t">
          {_rows_local_html}
        </table>
      </div>

      <div class="box" style="margin-top:12px;">
        <h3>Примечание</h3>
        <p style="font-size:12px; line-height:1.4; margin:0;">
          Расчёт не включает возможные дополнительные сборы за таможенные операции в порту,
          такие как сканирование MIIC/IIC (мобильный/стационарный инспекционный комплекс) и другие
          виды контроля, таможенные проверки/осмотры, дополнительное взвешивание, а также
          последующие сборы за задержание, демередж и хранение контейнеров, возникающие из‑за
          задержек по вывозу контейнера из порта.
        </p>
      </div>
    </div>
  </div>

  <div class="footer">BRIS Ceramic — внутренний расчёт. Сгенерировано из калькулятора.</div>
</body>
</html>
"""

    with st.expander("Открыть форму для печати (A4)", expanded=False):
        components.html(_html_print, height=1400)
        st.caption("Далее: Ctrl+P → Save as PDF / Печать.")

