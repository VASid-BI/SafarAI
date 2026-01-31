import requests
import sys
import json
from datetime import datetime
import time

class SafarAIAPITester:
    def __init__(self, base_url="https://safarai-intel.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.tests_run = 0
        self.tests_passed = 0
        self.test_source_id = None

    def run_test(self, name, method, endpoint, expected_status, data=None, timeout=30):
        """Run a single API test"""
        url = f"{self.api_url}/{endpoint}"
        headers = {'Content-Type': 'application/json'}

        self.tests_run += 1
        print(f"\n🔍 Testing {name}...")
        print(f"   URL: {url}")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, timeout=timeout)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=headers, timeout=timeout)
            elif method == 'PATCH':
                response = requests.patch(url, json=data, headers=headers, timeout=timeout)
            elif method == 'DELETE':
                response = requests.delete(url, headers=headers, timeout=timeout)

            success = response.status_code == expected_status
            if success:
                self.tests_passed += 1
                print(f"✅ Passed - Status: {response.status_code}")
                try:
                    response_data = response.json()
                    print(f"   Response: {json.dumps(response_data, indent=2)[:200]}...")
                    return True, response_data
                except:
                    return True, {}
            else:
                print(f"❌ Failed - Expected {expected_status}, got {response.status_code}")
                try:
                    error_data = response.json()
                    print(f"   Error: {error_data}")
                except:
                    print(f"   Error: {response.text}")
                return False, {}

        except Exception as e:
            print(f"❌ Failed - Error: {str(e)}")
            return False, {}

    def test_root_endpoint(self):
        """Test root API endpoint"""
        return self.run_test("Root API", "GET", "", 200)

    def test_get_stats(self):
        """Test GET /api/stats"""
        success, response = self.run_test("Get Stats", "GET", "stats", 200)
        if success:
            required_fields = ['total_sources', 'active_sources', 'total_runs', 'total_events', 'total_items']
            for field in required_fields:
                if field not in response:
                    print(f"❌ Missing required field: {field}")
                    return False
            print(f"   Stats: {response['active_sources']}/{response['total_sources']} sources, {response['total_runs']} runs")
        return success

    def test_get_sources(self):
        """Test GET /api/sources"""
        success, response = self.run_test("Get Sources", "GET", "sources", 200)
        if success:
            sources = response.get('sources', [])
            print(f"   Found {len(sources)} sources")
            if len(sources) >= 6:  # Should have 6 default sources
                print("✅ Default sources seeded correctly")
            else:
                print(f"⚠️  Expected 6 default sources, found {len(sources)}")
        return success

    def test_create_source(self):
        """Test POST /api/sources"""
        test_source = {
            "name": "Test Source API",
            "url": "https://test-api.example.com",
            "category": "hotel",
            "active": True
        }
        success, response = self.run_test("Create Source", "POST", "sources", 200, test_source)
        if success and 'id' in response:
            self.test_source_id = response['id']
            print(f"   Created source with ID: {self.test_source_id}")
        return success

    def test_update_source(self):
        """Test PATCH /api/sources/:id"""
        if not self.test_source_id:
            print("❌ No test source ID available for update test")
            return False
        
        update_data = {"active": False}
        success, response = self.run_test(
            "Update Source", 
            "PATCH", 
            f"sources/{self.test_source_id}", 
            200, 
            update_data
        )
        if success:
            print(f"   Updated source active status to: {response.get('active', 'unknown')}")
        return success

    def test_delete_source(self):
        """Test DELETE /api/sources/:id"""
        if not self.test_source_id:
            print("❌ No test source ID available for delete test")
            return False
        
        success, response = self.run_test(
            "Delete Source", 
            "DELETE", 
            f"sources/{self.test_source_id}", 
            200
        )
        if success:
            print(f"   Deleted source successfully")
        return success

    def test_trigger_run(self):
        """Test POST /api/run"""
        success, response = self.run_test("Trigger Pipeline Run", "POST", "run", 200)
        if success and 'run_id' in response:
            print(f"   Started run with ID: {response['run_id']}")
            # Wait a bit for the run to start
            time.sleep(2)
        return success

    def test_get_latest_run(self):
        """Test GET /api/runs/latest"""
        success, response = self.run_test("Get Latest Run", "GET", "runs/latest", 200)
        if success:
            if 'message' in response and 'No runs yet' in response['message']:
                print("   No runs available yet")
            else:
                print(f"   Run status: {response.get('status', 'unknown')}")
                print(f"   Sources: {response.get('sources_ok', 0)}/{response.get('sources_total', 0)}")
        return success

    def test_get_latest_logs(self):
        """Test GET /api/logs/latest"""
        success, response = self.run_test("Get Latest Logs", "GET", "logs/latest", 200)
        if success:
            logs = response.get('logs', [])
            print(f"   Found {len(logs)} log entries")
            if logs:
                print(f"   Latest log: {logs[-1].get('message', 'N/A')[:50]}...")
        return success

    def test_get_latest_brief(self):
        """Test GET /api/brief/latest"""
        success, response = self.run_test("Get Latest Brief", "GET", "brief/latest", 200)
        if success:
            if 'message' in response and 'No briefs available' in response['message']:
                print("   No briefs available yet")
            else:
                events = response.get('events', [])
                print(f"   Brief contains {len(events)} events")
        return success

    def test_invalid_endpoints(self):
        """Test invalid endpoints return 404"""
        success, _ = self.run_test("Invalid Endpoint", "GET", "nonexistent", 404)
        return success

def main():
    print("🚀 Starting SafarAI API Testing...")
    print("=" * 60)
    
    tester = SafarAIAPITester()
    
    # Test all endpoints
    tests = [
        ("Root API", tester.test_root_endpoint),
        ("Stats Endpoint", tester.test_get_stats),
        ("Sources List", tester.test_get_sources),
        ("Create Source", tester.test_create_source),
        ("Update Source", tester.test_update_source),
        ("Delete Source", tester.test_delete_source),
        ("Trigger Run", tester.test_trigger_run),
        ("Latest Run", tester.test_get_latest_run),
        ("Latest Logs", tester.test_get_latest_logs),
        ("Latest Brief", tester.test_get_latest_brief),
        ("Invalid Endpoint", tester.test_invalid_endpoints),
    ]
    
    for test_name, test_func in tests:
        try:
            test_func()
        except Exception as e:
            print(f"❌ {test_name} failed with exception: {e}")
            tester.tests_run += 1
    
    # Print results
    print("\n" + "=" * 60)
    print(f"📊 Test Results: {tester.tests_passed}/{tester.tests_run} tests passed")
    
    if tester.tests_passed == tester.tests_run:
        print("🎉 All tests passed!")
        return 0
    else:
        print(f"⚠️  {tester.tests_run - tester.tests_passed} tests failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())