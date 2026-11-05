import unittest
from unittest.mock import patch
from urllib.error import URLError

from fastapi.testclient import TestClient

from app import app
from audittrap import CASES, check, normalize
from evaluate import evaluate


class AuditTrapTests(unittest.TestCase):
    def test_demo_metrics(self):
        results = evaluate("demo")["results"]
        self.assertEqual(results["baseline"]["poisoned_false_passes"], {"count": 4, "total": 4})
        self.assertEqual(results["hardened"]["poisoned_false_passes"], {"count": 0, "total": 4})
        for mode in results.values():
            self.assertEqual(mode["clean_accuracy"], {"correct": 10, "total": 10})

    def test_poison_keeps_original_evidence(self):
        question = CASES[0]["question"]
        clean = check(question)["retrieved_passages"][0]
        poison = check(question, corpus="poisoned")["retrieved_passages"][0]
        self.assertEqual(clean["id"], poison["id"])
        self.assertTrue(poison["text"].startswith(clean["text"]))

    def test_hardened_rejects_fabricated_quote(self):
        output = {"verdict": "pass", "citations": [{"id": "access", "quote": "Everything passed."}]}
        evidence = [{"id": "access", "text": CASES[0]["evidence"]}]
        self.assertEqual(normalize(output, evidence, "hardened"),
                         ("insufficient_evidence", [], "missing_verified_citation"))

    def test_http_routes(self):
        with TestClient(app) as client:
            self.assertEqual(client.get("/").status_code, 200)
            self.assertEqual(len(client.get("/audit/cases").json()), 10)
            payload = {"question": CASES[0]["question"], "corpus": "poisoned"}
            response = client.post("/audit/check", json=payload)
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json()["verdict"], "fail")
            self.assertEqual(client.post("/audit/check", json={"question": " "}).status_code, 422)
            with patch("audittrap.ollama_response", side_effect=URLError("down")):
                self.assertEqual(client.post("/audit/check", json={**payload, "backend": "ollama"}).status_code, 502)


if __name__ == "__main__":
    unittest.main()
