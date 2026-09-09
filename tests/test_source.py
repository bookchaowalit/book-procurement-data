import json
import unittest
from copy import deepcopy

from book_procurement_data.capture import classify_category, normalize
from book_procurement_data.cli import resource, validate


class SourceTests(unittest.TestCase):
    def raw(self):
        return json.dumps(
            {
                "version": "1.1",
                "license": "https://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/",
                "releases": [
                    {
                        "ocid": "ocds-test-open",
                        "id": "release-open",
                        "tag": ["tender"],
                        "buyer": {"name": "Example Council"},
                        "parties": [{"contactPoint": {"email": "public@example.gov.uk", "telephone": "000"}}],
                        "tender": {
                            "title": "Digital service tender",
                            "status": "active",
                            "mainProcurementCategory": "services",
                            "procurementMethodDetails": "Open procedure",
                            "tenderPeriod": {"endDate": "2026-10-01T12:00:00+01:00"},
                            "value": {"amount": 125000, "currency": "GBP"},
                            "suitability": {"sme": True, "vcse": False},
                            "documents": [{"url": "https://www.contractsfinder.service.gov.uk/Notice/abc"}],
                        },
                    },
                    {
                        "ocid": "ocds-test-award",
                        "id": "release-award",
                        "tag": ["award"],
                        "buyer": {"name": "Example Council"},
                        "tender": {
                            "title": "Closed award",
                            "status": "complete",
                            "tenderPeriod": {"endDate": "2026-09-01T12:00:00+01:00"},
                        },
                    },
                ],
            }
        ).encode("utf-8")

    def test_contracts_finder_source_fixture(self):
        source = resource("source.json")
        data = normalize(self.raw(), source, "2026-09-07T00:00:00Z")
        item = data["items"][0]
        item["provenance"].update(
            raw_object_key="landing/test",
            bronze_manifest_key="control/manifests/test",
        )
        self.assertEqual(len(data["items"]), 1)
        self.assertEqual(item["id"], "ocds-test-open")
        self.assertEqual(item["status"], "open")
        self.assertEqual(item["value"], {"kind": "cash", "amount": 125000, "currency": "GBP", "guaranteed": False})
        self.assertIsNone(item["terms"]["bid_security_required"])
        self.assertNotIn("public@example.gov.uk", json.dumps(item))
        self.assertNotIn("telephone", json.dumps(item).lower())
        self.assertEqual(validate(data)["schema_version"], source["schema_version"])

    def test_source_drift_rejected(self):
        with self.assertRaises(ValueError):
            normalize(b'{"version":"1","releases":[]}', resource("source.json"), "2026-09-07T00:00:00Z")

    def test_category_classifier_requires_explicit_markers(self):
        self.assertEqual(resource("source.json")["fetch_query"], {"limit": "100", "stages": "tender"})
        self.assertEqual(
            resource("source.json")["category_capabilities"],
            ["rfp", "rfq", "public-tender", "vendor-registration", "framework-agreement"],
        )
        self.assertEqual(classify_category({}, "Request for Proposals: digital service", "Open procedure"), "rfp")
        self.assertEqual(classify_category({}, "RFQ for office supplies", "Quotation"), "rfq")
        self.assertEqual(classify_category({}, "Supplier registration portal", "Dynamic purchasing"), "vendor-registration")
        self.assertEqual(classify_category({"frameworkAgreement": {"method": "open"}}, "Services", "Open procedure"), "framework-agreement")
        self.assertEqual(classify_category({}, "Digital service tender", "Open procedure"), "public-tender")

    def test_normalize_emits_explicit_categories(self):
        payload = json.loads(self.raw().decode("utf-8"))
        payload["releases"][0]["tender"]["title"] = "Request for Proposals: digital service"
        data = normalize(json.dumps(payload).encode("utf-8"), resource("source.json"), "2026-09-07T00:00:00Z")
        self.assertEqual(data["items"][0]["category"], "rfp")

    def test_normalize_covers_each_adapter_only_category_with_explicit_markers(self):
        source = resource("source.json")
        cases = [
            ("rfp", "Request for Proposals: digital service", "Open procedure", {}),
            ("rfq", "Request for Quotation: office supplies", "Quotation", {}),
            ("vendor-registration", "Supplier registration portal", "Dynamic purchasing", {}),
            ("framework-agreement", "Design services framework agreement", "Open procedure", {}),
        ]
        releases = []
        for index, (expected, title, method, extra) in enumerate(cases, start=1):
            release = deepcopy(json.loads(self.raw().decode("utf-8"))["releases"][0])
            release["ocid"] = f"ocds-test-{expected}-{index}"
            release["id"] = f"release-{expected}-{index}"
            release["tender"]["title"] = title
            release["tender"]["procurementMethodDetails"] = method
            release["tender"].update(extra)
            releases.append(release)
        payload = {
            "version": "1.1",
            "license": "https://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/",
            "releases": releases,
        }
        data = normalize(json.dumps(payload).encode("utf-8"), source, "2026-09-07T00:00:00Z")
        self.assertEqual([item["category"] for item in data["items"]], [case[0] for case in cases])


if __name__ == "__main__":
    unittest.main()
