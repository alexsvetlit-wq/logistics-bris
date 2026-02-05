import streamlit as st
import streamlit.components.v1 as components
import json
import os

# --- Fixed sidebar helper button (scroll sidebar to top) ---
components.html(
    '''
    <script>
      (function(){
        const doc = window.parent?.document || document;

        function ensureBtn(){
          // create (or reuse) fixed button
          let btn = doc.getElementById('brisSidebarScrollTopBtn');
          if(!btn){
            btn = doc.createElement('div');
            btn.id = 'brisSidebarScrollTopBtn';
            btn.textContent = '«';
            btn.style.position = 'fixed';
            btn.style.left = '8px';
            btn.style.bottom = '12px';
            btn.style.zIndex = '999999';
            btn.style.width = '14px';
            btn.style.height = '14px';
            btn.style.display = 'flex';
            btn.style.alignItems = 'center';
            btn.style.justifyContent = 'center';
            btn.style.background = '#f3f4f6';
            btn.style.border = '2px solid #d1d5db';
            btn.style.borderRadius = '4px';
            btn.style.cursor = 'pointer';
            btn.style.fontSize = '10px';
            btn.style.userSelect = 'none';
            btn.addEventListener('click', () => {
              try{
                const sc = doc.querySelector('div[data-testid="stSidebarContent"]');
                if(sc){ sc.scrollTo({top:0, behavior:'smooth'}); return; }
                const sb = doc.querySelector('section[data-testid="stSidebar"]');
                if(sb){ sb.scrollTo({top:0, behavior:'smooth'}); }
              }catch(e){}
            });
            doc.body.appendChild(btn);
          }
        }

        // init + keep alive (Streamlit may re-render DOM)
        ensureBtn();
        setInterval(ensureBtn, 1500);
      })();
    </script>
    ''',
    height=0,
)



# --- Sidebar bottom collapse button (inside sidebar DOM) ---
components.html(
    '''
    <script>
      (function(){
        const doc = window.parent?.document || document;

        function findCollapseButton(){
          // Most common Streamlit selectors (vary by version/theme)
          const candidates = [
            'button[data-testid="collapsedControl"]',                        // sometimes exists
            'button[aria-label="Close sidebar"]',
            'button[aria-label="Open sidebar"]',
            'button[title="Close sidebar"]',
            'button[title="Open sidebar"]',
            '[data-testid="stSidebar"] button[aria-label="Close sidebar"]',
            '[data-testid="stSidebar"] button[aria-label="Open sidebar"]',
            '[data-testid="stSidebar"] [data-testid="stSidebarCollapseButton"] button',
            '[data-testid="stSidebar"] [data-testid="stSidebarCollapseButton"]',
            'button[data-testid="stSidebarCollapseButton"]',
          ];
          for (const sel of candidates){
            const el = doc.querySelector(sel);
            if (el) return el;
          }
          return null;
        }

        function toggleSidebar(){
          const btn = findCollapseButton();
          if (btn) { btn.click(); return; }

          // Fallback: click first "sidebar" icon button in header area
          const headerBtns = Array.from(doc.querySelectorAll('header button'));
          const maybe = headerBtns.find(b=>{
            const a = (b.getAttribute('aria-label')||'').toLowerCase();
            const t = (b.getAttribute('title')||'').toLowerCase();
            return a.includes('sidebar') || t.includes('sidebar');
          });
          if (maybe) { maybe.click(); }
        }

        function ensureSidebarBottomBtn(){
          const sidebar = doc.querySelector('section[data-testid="stSidebar"]');
          if(!sidebar) return;

          // Streamlit places scrollable content in stSidebarContent; we attach to sidebar itself.
          let host = sidebar;
          // Make positioning context
          try { host.style.position = 'relative'; } catch(e){}

          let btn = doc.getElementById('brisSidebarCollapseBtn');
          if(!btn){
            btn = doc.createElement('div');
            btn.id = 'brisSidebarCollapseBtn';
            btn.textContent = '«';
            btn.style.position = 'absolute';
            btn.style.right = '10px';
            btn.style.bottom = '10px';
            btn.style.width = '14px';
            btn.style.height = '14px';
            btn.style.display = 'flex';
            btn.style.alignItems = 'center';
            btn.style.justifyContent = 'center';
            btn.style.background = '#f3f4f6';
            btn.style.border = '2px solid #d1d5db';
            btn.style.borderRadius = '4px';
            btn.style.cursor = 'pointer';
            btn.style.fontSize = '10px';
            btn.style.userSelect = 'none';
            btn.style.zIndex = '999999';
            btn.addEventListener('click', ()=>{ try{ toggleSidebar(); }catch(e){} });
            host.appendChild(btn);
          } else {
            if (btn.parentElement !== host){
              try { host.appendChild(btn); } catch(e){}
            }
          }
        }

        ensureSidebarBottomBtn();
        // Streamlit rerenders; keep alive
        setInterval(ensureSidebarBottomBtn, 1200);
      })();
    </script>
    ''',
    height=0,
)

# =========================
# Logistics калькулятор  =========================

st.set_page_config(
    page_title="Logistics калькулятор",
    layout="wide",
    page_icon="assets/bris_logo.png"
)


st.markdown("""
<style>
/* Уменьшаем заголовок Logistics калькулятор в 2 раза */
h1 {
    font-size: 1.25rem !important;
}

/* Уменьшаем заголовок "Печать / PDF" в 2 раза */
h2 {
    font-size: 1.1rem !important;
}
</style>
""", unsafe_allow_html=True)



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
# (НОВОЕ) Справочник контактов по морским линиям (сайт/облако/менеджер)
# Не влияет на расчёты. Используется только для кнопки ℹ️ рядом с выбором линии.
# =========================

# =========================
# (НОВОЕ) Справочник контактов по морским линиям (сайт/облако/менеджер)
# Данные подгружаются из файла lines.json (если он есть рядом с приложением).
# Это НЕ влияет на расчёты. Используется только для кнопки ℹ️ рядом с выбором линии.
# =========================
SEA_LINE_INFO_DEFAULT = {
    "Fesco": {
        "site": "https://www.fesco.ru",
        "cloud": "",  # ссылка на облако с документами/контактами (опционально)
        "manager": {"name": "", "phone": "", "email": ""},
    },
    "Silmar": {"site": "", "cloud": "", "manager": {"name": "", "phone": "", "email": ""}},
    "Akkon": {"site": "", "cloud": "", "manager": {"name": "", "phone": "", "email": ""}},
    "Arkas": {"site": "", "cloud": "", "manager": {"name": "", "phone": "", "email": ""}},
    "ExpertTrans": {"site": "", "cloud": "", "manager": {"name": "", "phone": "", "email": ""}},
}

def load_sea_line_info():
    # Файл должен лежать рядом с streamlit_app.py
    # Формат 1 (простой): { "Fesco": {...}, "Arkas": {...} }
    # Формат 2 (обёртка): { "SEA_LINE_INFO": { ... } }
    path = "lines.json"
    try:
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)

            if isinstance(data, dict) and "SEA_LINE_INFO" in data and isinstance(data["SEA_LINE_INFO"], dict):
                data = data["SEA_LINE_INFO"]

            if isinstance(data, dict):
                merged = dict(SEA_LINE_INFO_DEFAULT)
                merged.update(data)  # переопределяем только то, что есть в JSON
                return merged
    except Exception:
        pass

    return SEA_LINE_INFO_DEFAULT

SEA_LINE_INFO = load_sea_line_info()


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

open_line_info = False  # кнопка ℹ️ по морской линии
open_email_registry = False  # кнопка ✉️ реестр почт

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
    currency_rate = st.number_input("Курс ЦБ+2,5% конвертация USD→RUB", value=80.0, step=0.1)

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
        price_per_m2 = st.number_input(price_label, value=7.500, step=0.001, format="%.3f")
    else:
        qty_m2 = st.number_input("Кол-во, шт.", value=1000.0, step=10.0)
        price_label = f"Цена товара, {price_currency}/шт."
        price_per_m2 = st.number_input(price_label, value=7.500, step=0.001, format="%.3f")

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
        line_c1, line_c2 = st.columns([6, 1])
        with line_c1:
            sea_line = st.selectbox("Морская линия", sorted(list(SEA_LINE_INFO.keys())))
        with line_c2:
            open_line_info = st.button("ℹ️", help="Сайт/документы/контакты по выбранной линии", key="open_line_info_btn")
            open_email_registry = st.button("✉️", help="Реестр почт по всем морским линиям", key="open_email_registry_btn")
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
        freight_usd = st.number_input("Фрахт, USD/конт.", value=2500.0, step=50.0)

    insurance_usd = st.number_input("DTHC портовые сборы, USD/конт.", value=0.0, step=10.0)

    # Поле "как раньше" (ручной ввод, если детализацию не используем)
    local_costs_rub_input = st.number_input(
        "Локальные расходы в РФ всего , RUB",
        value=24000.0,
        step=24000.0
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
        value=18000.0, step=18000.0
    )

    lr_restack_cross = st.number_input(
        "Перетарка на СВХ кросс-докинг (из ктк в авто/склад), RUB/1 фура",
        value=9000.0, step=9000.0
    )

    lr_prr_mech = st.number_input(
        "ПРР механизированная (из ктк -склад- авто), RUB/паллет",
        value=500.0, step=500.0
    )

    lr_prr_manual = st.number_input(
        "ПРР ручная (из ктк авто/склад) за 1 тн без паллеты, RUB/тонна",
        value=900.0, step=900.0
    )

    lr_restack_ktt = st.number_input(
        "Паллетированние(вкл.поддон+стрейч+пплента), RUB/паллет",
        value=1300.0, step=1300.0
    )

    lr_restack_terminal = st.number_input(
        "Перетарка на СВХ (с ктквоз снять/поставить), RUB/ктк лифт",
        value=1500.0, step=1500.0
    )

    lr_storage = st.number_input(
        "Хранение на СВХ (начиная с 10 дня хран.), RUB/паллетодень",
        value=30.0, step=30.0
    )

    lr_delivery_rf = st.number_input(
        "Доставка по РФ до склада клиента (авто 20 тонн), RUB/авто",
        value=0.0, step=5000.0
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

    calc_bottom = st.button("Рассчитать", type="primary", key="calc_bottom")

    # Триггер расчёта (верхняя или нижняя кнопка)
    calc = bool(calc_top or calc_bottom)


# =========================
# (НОВОЕ) Инфо по выбранной морской линии (кнопка ℹ️)
# Примечание: используем @st.dialog (совместимо с версиями Streamlit, где st.dialog — декоратор)
# =========================
@st.dialog("Реестр почт морских линий")
def _show_sea_lines_email_registry():
    rows = []

    for line_name, info in (SEA_LINE_INFO or {}).items():
        emails = []

        mgr = info.get("manager") or {}
        m_email = (mgr.get("email") or "").strip()
        if m_email:
            emails.append(m_email)

        extra = info.get("additional_contacts") or []
        if isinstance(extra, list):
            for c in extra:
                e = (c.get("email") or "").strip()
                if e:
                    emails.append(e)

        # уникальные, с сохранением порядка
        seen = set()
        uniq = []
        for e in emails:
            el = e.lower()
            if el not in seen:
                seen.add(el)
                uniq.append(e)

        if uniq:
            emails_html = "<br>".join(
                [f'<a href="mailto:{e}" style="color:#1f6feb">{e}</a>' for e in uniq]
            )
        else:
            emails_html = ""

        rows.append((line_name, emails_html))

    rows = sorted(rows, key=lambda x: x[0].lower())

    html = """
    <style>
      table {font-size: 16px;}
      td {word-break: break-word;}
      a {text-decoration: none;}
    </style>
    <table style="width:100%; border-collapse:collapse;">
      <thead>
        <tr>
          <th style="text-align:left; padding:8px; border-bottom:1px solid #ddd;">Линия</th>
          <th style="text-align:left; padding:8px; border-bottom:1px solid #ddd;">Email(ы)</th>
        </tr>
      </thead>
      <tbody>
    """

    for line, emails_html in rows:
        html += f"""
        <tr>
          <td style="vertical-align:top; padding:8px; border-bottom:1px solid #eee;">{line}</td>
          <td style="padding:8px; border-bottom:1px solid #eee;">{emails_html}</td>
        </tr>
        """

    html += "</tbody></table>"

    components.html(html, height=520, scrolling=True)



@st.dialog("Сводная таблица морских линий")
def _show_sea_lines_summary():
    """
    Показывает общую таблицу по всем морским линиям (ставки/сроки/тип судна),
    собранную из lines.json.
    """
    rows = []
    for line_name, info in (SEA_LINE_INFO or {}).items():
        routes = info.get("main_routes_and_rates") or []
        if not isinstance(routes, list):
            routes = []
        if routes:
            for r in routes:
                rows.append({
                    "Линия": line_name,
                    "Маршрут": r.get("route", ""),
                    "Контейнер": r.get("container", ""),
                    "Ставка, USD": r.get("rate_usd", ""),
                    "Тип судна": r.get("vessel_type", ""),
                    "Срок, дни": r.get("transit_time_days", ""),
                    "Примечание": r.get("notes", ""),
                })
        else:
            # строка-заглушка, чтобы линия всё равно была видна
            rows.append({
                "Линия": line_name,
                "Маршрут": "",
                "Контейнер": "",
                "Ставка, USD": "",
                "Тип судна": "",
                "Срок, дни": "",
                "Примечание": "",
            })

    if rows:
        st.dataframe(rows, use_container_width=True, hide_index=True)
    else:
        st.info("Нет данных для отображения.")


@st.dialog("Инфо: морская линия")
def _show_sea_line_dialog(_sea_line: str):
    info = SEA_LINE_INFO.get(_sea_line, {})
    mgr = (info.get("manager") or {})

    site = (info.get("site") or "").strip()
    cloud = (info.get("cloud") or "").strip()

    if st.button("📊 Сводная таблица ставок и сроков", use_container_width=True):
        _show_sea_lines_summary()

        # --- Лаконичные ссылки (кнопка + кликабельная/копируемая ссылка рядом) ---
    st.markdown(
        """
        <style>
          /* компактные кнопки в ℹ️-окне */
          div[data-testid="stDialog"] a[data-testid="stLinkButton"] > div {
            padding: 0.25rem 0.55rem !important;
            min-height: 32px !important;
            border-radius: 8px !important;
          }
          /* уменьшаем ширину: делаем кнопки "по содержимому" */
          div[data-testid="stDialog"] a[data-testid="stLinkButton"] {
            width: fit-content !important;
          }
          /* вид ссылки справа: синий, переносится */
          .bris-inline-link a{
            color:#1f6feb;
            text-decoration: none;
            word-break: break-word;
          }
          .bris-inline-link a:hover{ text-decoration: underline; }
          .bris-inline-link{ padding-top: 0.35rem; }
        </style>
        """,
        unsafe_allow_html=True,
    )

    def _inline_link(url: str) -> str:
        if not url:
            return "<span style='color:#999'>(—)</span>"
        esc = url.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        return f"<span class='bris-inline-link'>(<a href='{esc}' target='_blank' rel='noopener noreferrer'>{esc}</a>)</span>"

    tariffs = (info.get("tariffs") or "").strip()

    # Сайт
    r1c1, r1c2 = st.columns([1, 5])
    with r1c1:
        if site:
            st.link_button("Сайт", site, use_container_width=False)
        else:
            st.link_button("Сайт", "https://example.com", disabled=True, use_container_width=False)
    with r1c2:
        st.markdown(_inline_link(site), unsafe_allow_html=True)

    # Облако
    r2c1, r2c2 = st.columns([1, 5])
    with r2c1:
        if cloud:
            st.link_button("Облако", cloud, use_container_width=False)
        else:
            st.link_button("Облако", "https://example.com", disabled=True, use_container_width=False)
    with r2c2:
        st.markdown(_inline_link(cloud), unsafe_allow_html=True)

    # Тарифы (опционально, если есть в JSON)
    if tariffs:
        r3c1, r3c2 = st.columns([1, 5])
        with r3c1:
            st.link_button("Тарифы", tariffs, use_container_width=False)
        with r3c2:
            st.markdown(_inline_link(tariffs), unsafe_allow_html=True)

    st.divider()
    st.markdown("#### Менеджер")

    name = (mgr.get("name") or "").strip() or "—"
    phone = (mgr.get("phone") or "").strip() or "—"
    email = (mgr.get("email") or "").strip() or "—"

    st.write(f"**{name}**")
    st.write(f"📞 {phone}")
    st.write(f"✉️ {email}")

    # Быстрые ссылки (если заполнено)
    if email != "—":
        st.markdown(f"[Написать письмо](mailto:{email})")
    if phone != "—":
        tel = phone.replace(" ", "").replace("-", "").replace("(", "").replace(")", "")
        st.markdown(f"[Позвонить](tel:{tel})")


    # =========================
    # Дополнительные контакты (если есть)
    # =========================
    extra = info.get("additional_contacts") or []
    if isinstance(extra, list) and len(extra) > 0:
        st.divider()
        st.markdown("#### Доп. контакты")
        for c in extra:
            cname = (c.get("name") or "").strip() or "—"
            cphone = (c.get("phone") or "").strip()
            cemail = (c.get("email") or "").strip()
            st.write(f"**{cname}**")
            if cphone:
                st.write(f"📞 {cphone}")
            if cemail:
                st.write(f"✉️ {cemail}")
                st.markdown(f"[Написать письмо](mailto:{cemail})")
            st.write("")

    # =========================
    # Основные направления и ставки (если есть)
    # =========================
    rates = info.get("main_routes_and_rates") or []
    if isinstance(rates, list) and len(rates) > 0:
        st.divider()
        st.markdown("#### Основные направления и ставки")
        rows = []
        for r in rates:
            rows.append({
                "Маршрут": r.get("route", ""),
                "Контейнер": r.get("container", ""),
                "Ставка, USD": r.get("rate_usd", ""),
                "Тип судна": r.get("vessel_type", ""),
                "Срок, дни": r.get("transit_time_days", ""),
                "Примечание": r.get("notes", ""),
            })
        st.dataframe(rows, use_container_width=True, hide_index=True)


if open_line_info and (sea_line is not None):
    _show_sea_line_dialog(sea_line)


if open_email_registry:
    _show_sea_lines_email_registry()

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

    # --- Вывод услуги по экспедированию / оформлению (итого) ---
    expediting_fee_per_container = exp_service_rub
    expediting_fee_total = expediting_fee_per_container * containers_qty
    st.write(
        f"Услуга по экспедированию / оформлению "
        f"({expediting_fee_per_container:.2f} USD/контейнер × {containers_qty}): "
        f"{expediting_fee_total:.2f} USD"
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
        c5.metric("Итого стоимость партии товара, RUB", f"{res['total_rub']:,.0f}")
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
        ("Курс на дату платежа USD→RUB(в т.ч ЦБ+2,5%)", _fmt_money(currency_rate, 2)),
        ("Инвойс (итого)", f"{_fmt_money(invoice_total, 2)} {invoice_currency}"),
        ("Товар", product_type),
        ("Поверхность", finish),
        ("Код ТН ВЭД", hs_code),
        ("Пошлина, %", _fmt_money(duty_pct, 2)),
        ("НДС, %", _fmt_money(VAT_PCT_FIXED, 2)),
        ("Кол-во", f"{_fmt_money(qty_m2, 2)} {unit}"),
        ("Цена (ср.расчетная цена по кол-ву)", f"{_fmt_money(price_per_m2, 2)} {price_currency}/{unit}"),
        ("Фрахт", f"{_fmt_money(freight_usd, 2)} USD/конт."),
        ("DTHC (портовые сборы)", f"{_fmt_money(insurance_usd, 2)} USD/конт."),
    ]

    # Детализация локальных расходов
    _print_local_detail = [
        ("Вывоз ктк из порта на СВХ в т.ч сдача в депо,RUB/1 ктк от:", lr_ktt_out, "₽"),
        ("Перетарка на СВХ кросс-докинг (КТК → авто/склад),RUB/1 фура от:", lr_restack_cross, "₽"),
        ("ПРР механизированная (из ктк -склад- авто),RUB/паллет от:", lr_prr_mech, "₽"),
        ("ПРР ручная (из ктк авто/склад) за 1тн. без паллеты,RUB/тн. от:", lr_prr_manual, "₽"),
        ("Паллетированние(поддон+стрейч+пп лента),RUB/паллет от:", lr_restack_ktt, "₽"),
        ("Перетарка на СВХ (с ктквоз снять/поставить),RUB/ктк лифт от:", lr_restack_terminal, "₽"),
        ("Хранение на СВХ (1 под/сутки с 10 дня хран.),RUB/палл.день от:", lr_storage, "₽"),
        ("Доставка по РФ до склада клиента (авто 20 тонн),RUB/авто от:", lr_delivery_rf, "₽"),
    ]

    # Итоги (результат)
    _print_totals = [
        ("Товар, USD", res["goods_usd"], "USD"),
        ("Тамож. стоимость, USD", res["customs_value_usd"], "USD"),
        ("Пошлина, USD", res["duty_usd"], "USD"),
        ("НДС 22%+тамож.сбор, USD", res["vat_usd"], "USD"),
        ("Локальные расходы в РФ, всего", local_costs_rub_input, "₽"),
        ("Итого стоимость партии товара, RUB", res["total_rub"], "₽"),
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
        <h3>Вознаграждение за комплекс работ экспедитора и технического импортера (договорные от объема)</h3>
        <table class="t totals">
          <tr>
            <td>Услуга по экспедированию / оформлению (100USD/ктк), USD</td>
            <td style="text-align:right">{_fmt_money(exp_service_rub * containers_qty, 2)} USD</td>
          </tr>
          <tr>
            <td>Агентская комиссия от подбора фрахта (% х Ocean Freight х N), USD</td>
            <td style="text-align:right">{_fmt_money((freight_usd * float(containers_qty)) * (exp_commission_pct / 100.0), 2)} USD</td>
          </tr>
          <tr>
            <td>Оплата на фабрику за клиента (USD)</td>
            <td style="text-align:right">{_fmt_money(res.get("factory_pay_usd", 0.0), 2)} USD</td>
          </tr>
          <tr>
            <td>Сумма вознаграждений (USD),всего</td>
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
        <h3>Расшифровка статьи "Локальные расходы в РФ, всего" (договорные)</h3>
        <table class="t">
          {_rows_local_html}
        </table>
      </div>

      <div class="box" style="margin-top:12px;">
        <h3>Примечание</h3>
        <p style="font-size:8.4px; line-height:1.4; margin:0;">
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

