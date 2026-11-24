import tempfile
import unittest
from pathlib import Path

from bot.brand_rules import (
    brand_block_reason,
    is_forbidden_model,
    is_full_name,
    is_phone,
    is_plate,
    normalize_plate,
    parse_year,
)


class BrandRulesTest(unittest.TestCase):
    def test_name(self):
        self.assertTrue(is_full_name("Иванов ИВАН"))
        self.assertFalse(is_full_name("."))
        self.assertFalse(is_full_name("Иван"))
        self.assertFalse(is_full_name("Иванов И"))

    def test_phone(self):
        self.assertTrue(is_phone("+998999999999"))
        self.assertFalse(is_phone("123"))

    def test_forbidden_models(self):
        self.assertTrue(is_forbidden_model("Chevrolet Spark"))
        self.assertTrue(is_forbidden_model("NEXIA 3"))
        self.assertTrue(is_forbidden_model("nexia-3"))
        self.assertFalse(is_forbidden_model("Chevrolet Lacetti"))

    def test_year_block(self):
        self.assertEqual(brand_block_reason("Spark", 2020), "model")
        self.assertEqual(brand_block_reason("Lacetti", 2015), "year")
        self.assertIsNone(brand_block_reason("Chevrolet Lacetti", 2023))
        self.assertIsNone(parse_year("2023 yil"))
        self.assertEqual(parse_year("2023"), 2023)

    def test_plate(self):
        self.assertEqual(normalize_plate("01a 123bc"), "01A123BC")
        self.assertTrue(is_plate("01Z777ZZ"))
        self.assertFalse(is_plate("12"))


class SheetRowTest(unittest.TestCase):
    def test_known_headers(self):
        from bot.sheets import build_row

        app = {
            "created_at": "2026-11-20 15:00",
            "code": "WB-000001",
            "city": "Toshkent shahri",
            "phone": "+998",
            "full_name": "Иванов Иван",
            "username": "driver",
            "plate": "01A123BC",
            "status": "new",
            "user_id": 7,
            "car_model": "Lacetti",
            "car_year": "2023",
            "car_color": "oq",
            "kind": "brend",
        }
        row = build_row(["Код", "ФИО", "Год", "Комментарий"], app)
        self.assertEqual(row, ["WB-000001", "Иванов Иван", "2023", ""])


class DatabaseTest(unittest.IsolatedAsyncioTestCase):
    async def test_two_codes(self):
        from bot import db
        from bot.config import settings

        with tempfile.TemporaryDirectory() as folder:
            settings.database_path = Path(folder) / "bot.sqlite"
            settings.turso_url = ""
            settings.code_prefix = "WB"
            await db.init()
            first = await db.create_application(
                {"kind": "brend", "user_id": 1, "phone": "+998", "city": "Toshkent shahri", "full_name": "A B"}
            )
            second = await db.create_application(
                {"kind": "ulanish", "user_id": 2, "phone": "+998", "city": "Toshkent shahri", "plate": "01A123BC"}
            )
            self.assertEqual(first["code"], "WB-000001")
            self.assertEqual(second["code"], "WB-000002")
            self.assertNotEqual(first["code"], second["code"])
            changed = await db.set_status(first["id"], "rejected")
            self.assertEqual(changed["status"], "rejected")
            same = await db.set_status(first["id"], "rejected")
            self.assertEqual(same["status"], "rejected")


if __name__ == "__main__":
    unittest.main()
