import unittest
from unittest.mock import patch, Mock
from shared_inputs import SharedInputs

PARAMS = {"prefill": "1", "supplier": "LEEN SANITARY WARE", "invoice": "158200",
          "invoice_currency": "CNY", "country": "Китай", "incoterms": "FOB",
          "containers": "1", "loading": "Shenzhen", "discharge": "Владивосток",
          "product": "Сантехника (унитазы)", "unit": "шт.", "quantity": "791",
          "price": "200", "price_currency": "CNY"}


class ShareTest(unittest.TestCase):
    def test_validation(self):
        import datetime
        self.assertEqual(SharedInputs({"prefill":"1", "date":"2026-09-30"}).date("date", datetime.date.today()), datetime.date(2026,9,30))
        self.assertEqual(SharedInputs({"prefill":"1", "date":"wrong"}).date("date", datetime.date(2026,9,30)), datetime.date(2026,9,30))
        self.assertEqual(SharedInputs({"prefill":"1", "usd_rub":"84.4283"}).number("usd_rub", 90), 84.4283)
        self.assertEqual(SharedInputs({"price": "200"}).number("price", 7.5), 7.5)
        for bad in ("nan", "inf", "-1", "1e999", "oops"):
            shared = SharedInputs({"prefill": "1", "price": bad})
            self.assertEqual(shared.number("price", 7.5), 7.5)
            self.assertEqual(shared.errors, ["price"])
        self.assertEqual(SharedInputs({"prefill": "1", "containers": "1.5"}).number("containers", 1, integer=True), 1)
        self.assertEqual(SharedInputs({"prefill": "1", "supplier": "x\n"}).text("supplier"), "")
        self.assertEqual(SharedInputs(PARAMS).index("country", ["Индия", "Китай"]), 1)

    def test_full_app(self):
        from streamlit.testing.v1 import AppTest
        response = Mock()
        response.json.return_value = {"Valute": {"USD": {"Value": 90}}}
        with patch("requests.get", return_value=response):
            app = AppTest.from_file("streamlit_app.py", default_timeout=15)
            app.query_params.update(PARAMS)
            app.run()
            self.assertFalse(app.exception)
            text = {w.label: w.value for w in app.text_input}
            numbers = {w.label: w.value for w in app.number_input}
            selects = {w.label: w.value for w in app.selectbox}
            self.assertEqual(text["Фабрика / поставщик (как в инвойсе)"], "LEEN SANITARY WARE")
            self.assertEqual(numbers["Кол-во, шт."], 791)
            self.assertEqual(numbers["Цена товара, CNY/шт."], 200)
            self.assertEqual(numbers["Общая стоимость товара по инвойсу"], 158200)
            self.assertEqual(numbers["Количество контейнеров"], 1)
            self.assertEqual(selects["Порт отгрузки"], "Shenzhen")
            self.assertEqual(selects["Порт выгрузки"], "Владивосток")
            self.assertEqual(selects["Валюта (инвойс)"], "CNY")
            self.assertEqual(numbers["Фрахт, USD (авто)"], 0)
            qty = next(w for w in app.number_input if w.label == "Кол-во, шт.")
            qty.set_value(790).run()
            self.assertFalse(app.exception)
            self.assertEqual(next(w.value for w in app.number_input if w.label == "Кол-во, шт."), 790)
            normal = AppTest.from_file("streamlit_app.py", default_timeout=15).run()
            self.assertFalse(normal.exception)
            self.assertEqual(next(w.value for w in normal.selectbox if w.label == "Страна"), "Индия")


if __name__ == "__main__":
    unittest.main()
