import unittest
from unittest.mock import patch

from app import app, categories


class PredictionAppTests(unittest.TestCase):
    def setUp(self):
        app.config["TESTING"] = True
        self.client = app.test_client()
        self.valid_payload = {
            "category": categories[0],
            "actual_price": 1000,
            "rating": 4.0,
            "rating_count": 100,
        }

    def test_home_page_renders_categories(self):
        response = self.client.get("/")

        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Estimate your price", response.data)
        self.assertIn(categories[0].replace("&", "&amp;").encode(), response.data)

    def test_home_page_renders_legacy_numeric_categories(self):
        with patch("app.categories", [0, 1]):
            response = self.client.get("/")

        self.assertEqual(response.status_code, 200)
        self.assertIn(b'<option value="0">0</option>', response.data)

    def test_health_check(self):
        response = self.client.get("/health")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json(), {"status": "ok"})

    def test_prediction_returns_discount_and_price(self):
        response = self.client.post("/predict", json=self.valid_payload)
        result = response.get_json()

        self.assertEqual(response.status_code, 200)
        self.assertGreaterEqual(result["discount"], 0)
        self.assertLessEqual(result["discount"], 100)
        self.assertEqual(
            result["final_price"],
            round(1000 * (1 - result["discount"] / 100), 2),
        )

    def test_prediction_accepts_form_submission(self):
        response = self.client.post("/predict", data=self.valid_payload)

        self.assertEqual(response.status_code, 200)
        self.assertIn("discount", response.get_json())

    def test_invalid_values_return_bad_request(self):
        cases = (
            {"actual_price": 0},
            {"rating": 5.1},
            {"rating_count": -1},
            {"rating_count": 1.5},
            {"actual_price": float("nan")},
            {"actual_price": 10**400},
            {"category": "not a known category"},
        )
        for change in cases:
            with self.subTest(change=change):
                payload = {**self.valid_payload, **change}
                response = self.client.post("/predict", json=payload)
                self.assertEqual(response.status_code, 400)
                self.assertIn("error", response.get_json())

    def test_non_object_json_returns_bad_request(self):
        response = self.client.post("/predict", json=["not", "an", "object"])

        self.assertEqual(response.status_code, 400)
        self.assertIn("error", response.get_json())


if __name__ == "__main__":
    unittest.main()
