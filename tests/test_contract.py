import copy
import unittest
from unittest.mock import patch
from book_procurement_data.cli import filter_items, resource, validate, main


class ContractTests(unittest.TestCase):
    def setUp(self):
        self.data = resource("demo.json")

    def test_synthetic_fixture(self):
        self.assertEqual(validate(self.data)["data_status"], "fixture")

    def test_domain_terms_required(self):
        self.data["items"][0]["terms"] = {}
        with self.assertRaises(ValueError): validate(self.data)

    def test_cross_domain_rejected(self):
        self.data["schema_version"] = "unrelated.v1"
        with self.assertRaises(ValueError): validate(self.data)

    def test_duplicate_rejected(self):
        self.data["items"].append(copy.deepcopy(self.data["items"][0]))
        with self.assertRaises(ValueError): validate(self.data)

    def test_fixture_cannot_be_claimed_live(self):
        self.data["data_status"] = "live"
        with self.assertRaises(ValueError): validate(self.data)

    def test_negative_value_rejected(self):
        self.data["items"][0]["value"]["amount"] = -1
        with self.assertRaises(ValueError): validate(self.data)

    def test_amount_requires_currency(self):
        self.data["items"][0]["value"]["amount"] = 100
        with self.assertRaises(ValueError): validate(self.data)

    def test_deadline_timezone_required(self):
        self.data["items"][0]["deadline"]["at"] = "2026-09-08T00:00:00"
        with self.assertRaises(ValueError): validate(self.data)

    def test_unknown_and_closed_not_open(self):
        found = filter_items(self.data, "2026-09-07T00:00:00Z", True)
        self.assertEqual(len(found), 1)

    def test_deadline_boundary_and_stale(self):
        self.assertEqual(filter_items(self.data, "2026-09-08T00:00:00Z", True), [])
        self.data["items"][0]["deadline"] = {"kind":"rolling", "at":None}
        self.assertEqual(filter_items(self.data, "2026-09-12T00:00:00Z", True), [])

    def test_future_check_not_open(self):
        self.assertEqual(filter_items(self.data, "2026-09-06T00:00:00Z", True), [])

    def test_secret_url_rejected(self):
        self.data["items"][0]["source_url"] = "https://example.org/claim?token=synthetic"
        with self.assertRaises(ValueError): validate(self.data)

    def test_search(self):
        self.assertEqual(filter_items(self.data, "2026-09-07T00:00:00Z", query="not-a-match"), [])

    def test_demo_never_uses_network(self):
        with patch("socket.socket", side_effect=AssertionError("network forbidden")), patch("builtins.print"):
            self.assertEqual(main(["demo", "--open-only"]), 0)


if __name__ == "__main__": unittest.main()
