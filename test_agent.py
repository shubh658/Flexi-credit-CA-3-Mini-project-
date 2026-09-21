import unittest
from fastapi.testclient import TestClient
from app.main import app
from app import database, triage_agent, dispatch_engine, simulator

class TestPublicSafetyIncidentAgent(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        database.init_db()

    def test_01_triage_classification_and_scoring(self):
        # Test Fire Triage
        report_fire = triage_agent.analyze_report(
            description="Heavy flames engulfing 3rd floor apartment, 2 people trapped inside!",
            location_name="120 Oak Street"
        )
        self.assertEqual(report_fire['category'], "Fire")
        self.assertEqual(report_fire['severity'], "P1-Critical")
        self.assertGreaterEqual(report_fire['priority_score'], 80)
        self.assertEqual(report_fire['victims_count'], 2)

        # Test Medical Triage
        report_med = triage_agent.analyze_report(
            description="Man collapsed on sidewalk, not breathing, severe head injury and bleeding",
            location_name="Central Park Plaza"
        )
        self.assertEqual(report_med['category'], "Medical")
        self.assertIn(report_med['severity'], ["P1-Critical", "P2-High"])

        # Test Hazmat Triage
        report_haz = triage_agent.analyze_report(
            description="Industrial chemical spill of toxic ammonia gas at warehouse dock",
            location_name="Industrial Port"
        )
        self.assertEqual(report_haz['category'], "Hazard")

    def test_02_unit_recommendation_and_dispatch(self):
        incidents = database.fetch_all_incidents()
        self.assertGreater(len(incidents), 0)
        target_inc = incidents[0]

        recommendations = dispatch_engine.get_recommended_units(target_inc['id'])
        self.assertIsInstance(recommendations, list)
        self.assertGreater(len(recommendations), 0)

        top_unit = recommendations[0]['unit_id']
        dispatch_res = dispatch_engine.dispatch_units(target_inc['id'], [top_unit])
        self.assertTrue(dispatch_res['success'])
        self.assertIn(top_unit, dispatch_res['dispatched_units'])

        units = database.fetch_all_units()
        matched_unit = next(u for u in units if u['id'] == top_unit)
        self.assertEqual(matched_unit['status'], "Dispatched")

    def test_03_citizen_interactive_chat(self):
        incidents = database.fetch_all_incidents()
        inc_id = incidents[0]['id']

        chat_res = triage_agent.process_citizen_chat(inc_id, "The smoke is getting thicker and we cannot breathe!")
        self.assertIn("Escalating emergency priority", chat_res['reply'])

    def test_04_simulator_scenario(self):
        incident = simulator.trigger_scenario("hazmat_leak")
        self.assertEqual(incident['category'], "Hazard")
        self.assertIn("INC-2026-", incident['id'])

    def test_05_api_endpoints(self):
        client = TestClient(app)

        # GET /api/incidents
        r1 = client.get("/api/incidents")
        self.assertEqual(r1.status_code, 200)
        self.assertIn("incidents", r1.json())

        # POST /api/incidents/report
        r2 = client.post("/api/incidents/report", json={
            "description": "Subway power surge causes train derailment on line 4",
            "location_name": "Terminal Station"
        })
        self.assertEqual(r2.status_code, 200)
        self.assertTrue(r2.json()["success"])

        # GET /api/analytics
        r3 = client.get("/api/analytics")
        self.assertEqual(r3.status_code, 200)
        self.assertIn("metrics", r3.json())

if __name__ == "__main__":
    unittest.main()
