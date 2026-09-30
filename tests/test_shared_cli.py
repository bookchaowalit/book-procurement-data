"""Shared-CLI guardrails; this file is byte-identical in every sibling book-*-data repo.

``cli.py`` is vendored (copied) across the sibling ``book-*-data`` repositories until
the shared runtime package is independently installable. The pins below make a local
edit fail loudly: change every copy of the same variant together, then update the
hash here and copy this file to every sibling unchanged.
"""
import copy
import hashlib
import importlib
import io
import json
import re
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROJECT = re.search(r'^name = "([a-z-]+)"$', (ROOT / "pyproject.toml").read_text(encoding="utf-8"), re.M)[1]
cli = importlib.import_module(PROJECT.replace("-", "_") + ".cli")

# Three variants: base, +contract --version v2, +v2 availability windows (benefit).
CLI_SHA256 = {
    "book-benefit-data": "dcc8c2edafafcba41ed1256ae876a903c7e812d0ebc92d87e9a58534bf1e7f90",
    "book-competition-data": "dec86b2edacdd5988b199808231387a81804337d4caa407f599a8d522709db28",
    "book-creator-program-data": "dec86b2edacdd5988b199808231387a81804337d4caa407f599a8d522709db28",
    "book-deal-data": "dec86b2edacdd5988b199808231387a81804337d4caa407f599a8d522709db28",
    "book-freebie-data": "6951a3912ef91ca0b2801b9be71936d40311018a8962c0aa83ee7bafd41888e8",
    "book-grant-data": "6951a3912ef91ca0b2801b9be71936d40311018a8962c0aa83ee7bafd41888e8",
    "book-learning-program-data": "dec86b2edacdd5988b199808231387a81804337d4caa407f599a8d522709db28",
    "book-mobility-program-data": "dec86b2edacdd5988b199808231387a81804337d4caa407f599a8d522709db28",
    "book-paid-study-data": "dec86b2edacdd5988b199808231387a81804337d4caa407f599a8d522709db28",
    "book-partnership-data": "dec86b2edacdd5988b199808231387a81804337d4caa407f599a8d522709db28",
    "book-procurement-data": "dec86b2edacdd5988b199808231387a81804337d4caa407f599a8d522709db28",
    "book-scholarship-data": "6951a3912ef91ca0b2801b9be71936d40311018a8962c0aa83ee7bafd41888e8",
    "book-startup-program-data": "dec86b2edacdd5988b199808231387a81804337d4caa407f599a8d522709db28",
}


def live_demo(host):
    """The packaged demo turned into a live payload whose records all use ``host``."""
    payload = copy.deepcopy(cli.resource("demo.json"))
    payload["data_status"] = "live"
    for item in payload["items"]:
        item["source_url"] = "https://" + host + "/record"
        item["provenance"].update(evidence_kind="captured", raw_object_key="raw/a", bronze_manifest_key="bronze/a")
    return payload


class VendoredCliTest(unittest.TestCase):
    def test_cli_matches_the_pinned_shared_copy(self):
        digest = hashlib.sha256(Path(cli.__file__).read_bytes().replace(b"\r\n", b"\n")).hexdigest()
        self.assertIn(PROJECT, CLI_SHA256)
        siblings = sorted(name for name, pinned in CLI_SHA256.items() if pinned == CLI_SHA256[PROJECT])
        self.assertEqual(
            digest,
            CLI_SHA256[PROJECT],
            "cli.py drifted from its vendored copy; apply the same change to " + ", ".join(siblings),
        )


class TimestampTest(unittest.TestCase):
    def test_fraction_digits_parse_identically_on_every_interpreter(self):
        # Python 3.10 fromisoformat rejects fractions that are not 3 or 6 digits.
        cases = {
            "2026-09-07T00:00:00.1Z": 100000,
            "2026-09-07T00:00:00.12Z": 120000,
            "2026-09-07T00:00:00.1234Z": 123400,
            "2026-09-07T00:00:00.1234567+07:00": 123456,
        }
        for value, micro in cases.items():
            with self.subTest(value=value):
                self.assertEqual(cli.timestamp(value).microsecond, micro)

    def test_offsets_normalise_to_the_same_utc_instant(self):
        bangkok = cli.timestamp("2026-10-01T07:00:00+07:00")
        new_york = cli.timestamp("2026-09-30T20:00:00-04:00")
        self.assertEqual(bangkok, cli.timestamp("2026-10-01T00:00:00Z"))
        self.assertEqual(bangkok, new_york)
        self.assertEqual(bangkok.utcoffset().total_seconds(), 0)

    def test_naive_and_non_ascii_timestamps_are_rejected(self):
        for value in ("2026-09-07T00:00:00", "2026-09-07", "๒๐๒๖-09-07T00:00:00Z", "2026-09-07T24:00:00Z"):
            with self.subTest(value=value), self.assertRaises(ValueError):
                cli.timestamp(value)


class ValidateTest(unittest.TestCase):
    def test_non_finite_numbers_are_rejected(self):
        for amount in (float("nan"), float("inf"), float("-inf")):
            payload = copy.deepcopy(cli.resource("demo.json"))
            payload["items"][0]["value"].update(amount=amount, currency="USD")
            with self.subTest(amount=amount), self.assertRaises(ValueError):
                cli.validate(payload)

    def test_validate_command_rejects_nan_and_overflow_literals(self):
        payload = copy.deepcopy(cli.resource("demo.json"))
        payload["items"][0]["value"].update(amount=123456789, currency="USD")
        text = json.dumps(payload)
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "payload.json"
            for literal, code in (("123456789", 0), ("NaN", 2), ("Infinity", 2), ("-Infinity", 2), ("1e400", 2)):
                path.write_text(text.replace("123456789", literal), encoding="utf-8")
                out, err = io.StringIO(), io.StringIO()
                with self.subTest(literal=literal), redirect_stdout(out), redirect_stderr(err):
                    self.assertEqual(cli.main(["validate", str(path)]), code)
                self.assertNotIn(literal, err.getvalue())

    def test_trailing_dot_synthetic_host_cannot_be_live(self):
        for host in ("example.org.", "EXAMPLE.ORG", "demo.example.org."):
            with self.subTest(host=host), self.assertRaisesRegex(ValueError, "synthetic source"):
                cli.validate(live_demo(host))

    def test_lookalike_hosts_are_not_treated_as_synthetic(self):
        for host in ("notexample.org", "example.org.evil.test"):
            with self.subTest(host=host):
                try:
                    cli.validate(live_demo(host))
                except ValueError as error:
                    self.assertNotIn("synthetic", str(error))


if __name__ == "__main__":
    unittest.main()
