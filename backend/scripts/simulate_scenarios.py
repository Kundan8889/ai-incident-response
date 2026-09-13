import os
import sys

# Ensure backend root is in sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import time
import httpx

BASE_URL = os.getenv("BASE_URL", "http://localhost:8000")


def test_scenario(name: str, fn):
    print("\n" + "=" * 60)
    print(f"RUNNING SCENARIO: {name}")
    print("=" * 60)
    try:
        fn()
        print(f"-> SCENARIO [{name}] PASSED")
    except Exception as e:
        print(f"-> SCENARIO [{name}] FAILED: {e}")
        raise e


def run_all_tests():
    client = httpx.Client(base_url=BASE_URL, timeout=10.0)

    # 1. Health check
    def scenario_health():
        res = client.get("/health")
        assert res.status_code == 200, f"Expected 200, got {res.status_code}"
        assert res.json().get("status") == "ok"
        assert "observability" in res.json()
        print("Health check response:", res.json())
        print("X-Request-ID:", res.headers.get("X-Request-ID"))

    # 2. Prometheus Metrics Check
    def scenario_metrics():
        res = client.get("/metrics")
        assert res.status_code == 200, f"Expected 200, got {res.status_code}"
        text = res.text
        assert "http_requests_total" in text or "http_request_duration_seconds" in text or "simulated_incidents_total" in text
        print("Prometheus /metrics endpoint verified. Sample lines:")
        for line in text.splitlines()[:8]:
            print("  ", line)

    # 3. Normal order creation & auto payment
    def scenario_normal_order():
        payload = {
            "customer_id": "cust_test_normal",
            "items": [
                {"sku": "ITEM-GPU-01", "name": "NVIDIA H100 Instance Hour", "quantity": 2, "price": 12.50}
            ],
            "currency": "USD",
            "auto_pay": True
        }
        res = client.post("/api/orders", json=payload)
        assert res.status_code == 201, f"Expected 201, got {res.status_code}: {res.text}"
        data = res.json()
        assert data["status"] == "PAID"
        assert data["amount"] == 25.0
        order_id = data["id"]
        print(f"Created normal order {order_id} (PAID):", data)

        res_get = client.get(f"/api/orders/{order_id}")
        assert res_get.status_code == 200
        assert res_get.json()["id"] == order_id
        print(f"Successfully retrieved order {order_id}")

    # 4. Direct payment endpoint
    def scenario_direct_payment():
        order_payload = {
            "customer_id": "cust_test_manual_pay",
            "items": [
                {"sku": "ITEM-CPU-01", "name": "Compute Instance 8-core", "quantity": 1, "price": 30.00}
            ],
            "currency": "USD",
            "auto_pay": False
        }
        res_order = client.post("/api/orders", json=order_payload)
        assert res_order.status_code == 201
        order_id = res_order.json()["id"]
        assert res_order.json()["status"] == "PENDING"

        pay_payload = {
            "order_id": order_id,
            "amount": 30.00,
            "currency": "USD",
            "payment_method": "card"
        }
        res_pay = client.post("/api/payments", json=pay_payload)
        assert res_pay.status_code == 201
        assert res_pay.json()["status"] == "SUCCESS"
        print(f"Direct payment successful for order {order_id}:", res_pay.json())

    # 5. Controlled Payment Failure
    def scenario_payment_failure():
        payload = {
            "customer_id": "cust_test_fail_payment",
            "items": [
                {"sku": "ITEM-STORAGE-01", "name": "Block Storage 1TB", "quantity": 1, "price": 50.00}
            ],
            "currency": "USD",
            "auto_pay": True
        }
        headers = {"X-Simulate-Incident": "payment_failure"}
        res = client.post("/api/orders", json=payload, headers=headers)
        assert res.status_code == 502, f"Expected 502 Bad Gateway, got {res.status_code}"
        print("Payment failure response (502):", res.json())

    # 6. Controlled Database Timeout Simulation
    def scenario_db_timeout():
        payload = {
            "customer_id": "cust_test_db_timeout",
            "items": [
                {"sku": "ITEM-DB-01", "name": "High-Throughput IOPS", "quantity": 1, "price": 100.00}
            ],
            "currency": "USD"
        }
        headers = {"X-Simulate-Incident": "db_timeout"}
        res = client.post("/api/orders", json=payload, headers=headers)
        assert res.status_code == 504, f"Expected 504 Gateway Timeout, got {res.status_code}"
        print("DB Timeout response (504):", res.json())

    # 7. Controlled Slow API Simulation
    def scenario_slow_api():
        payload = {
            "customer_id": "cust_test_slow",
            "items": [
                {"sku": "ITEM-NET-01", "name": "Dedicated Bandwidth", "quantity": 1, "price": 15.00}
            ],
            "currency": "USD"
        }
        headers = {"X-Simulate-Incident": "slow_api", "X-Simulate-Latency-Ms": "1500"}
        t0 = time.time()
        res = client.post("/api/orders", json=payload, headers=headers)
        elapsed = time.time() - t0
        assert res.status_code == 201
        assert elapsed >= 1.4, f"Expected delay >= 1.4s, got {elapsed:.2f}s"
        print(f"Slow API response received in {elapsed:.2f}s (Status: {res.status_code})")

    # 8. Controlled Background Job Failure
    def scenario_background_failure():
        payload = {
            "customer_id": "cust_test_bg_fail",
            "items": [
                {"sku": "ITEM-AUDIT-01", "name": "Audit Log Storage", "quantity": 1, "price": 20.00}
            ],
            "currency": "USD"
        }
        headers = {"X-Simulate-Incident": "background_failure"}
        res = client.post("/api/orders", json=payload, headers=headers)
        assert res.status_code == 201
        print("Order succeeded with status 201, background task will log simulated exception in server logs.")

    test_scenario("Health Check with Observability Metadata", scenario_health)
    test_scenario("Prometheus /metrics Endpoint", scenario_metrics)
    test_scenario("Normal Order Flow (Order + Payment)", scenario_normal_order)
    test_scenario("Direct Payment Endpoint (/api/payments)", scenario_direct_payment)
    test_scenario("Payment Service Failure Simulation (502)", scenario_payment_failure)
    test_scenario("Database Timeout Simulation (504)", scenario_db_timeout)
    test_scenario("Slow API Latency Simulation", scenario_slow_api)
    test_scenario("Background Job Failure Simulation", scenario_background_failure)
    print("\n" + "=" * 60)
    print("ALL SIMULATED SCENARIOS & OBSERVABILITY ENDPOINTS VERIFIED!")
    print("=" * 60)


if __name__ == "__main__":
    run_all_tests()
