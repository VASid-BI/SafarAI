"""
SafarAI Backend API Tests
Tests for all backend endpoints including new features:
- Briefs archive
- PDF export
- Scheduled runs
- Source health monitoring
- Email configuration
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestHealthAndBasicEndpoints:
    """Basic API health and stats tests"""
    
    def test_api_root(self):
        """Test API root endpoint"""
        response = requests.get(f"{BASE_URL}/api/")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        print(f"SUCCESS: API root returns: {data['message']}")
    
    def test_stats_endpoint(self):
        """Test stats endpoint"""
        response = requests.get(f"{BASE_URL}/api/stats")
        assert response.status_code == 200
        data = response.json()
        assert "total_sources" in data
        assert "active_sources" in data
        assert "total_runs" in data
        assert "total_events" in data
        print(f"SUCCESS: Stats - Sources: {data['active_sources']}, Runs: {data['total_runs']}, Events: {data['total_events']}")


class TestSourcesEndpoints:
    """Tests for sources CRUD operations"""
    
    def test_list_sources(self):
        """Test listing all sources"""
        response = requests.get(f"{BASE_URL}/api/sources")
        assert response.status_code == 200
        data = response.json()
        assert "sources" in data
        assert isinstance(data["sources"], list)
        print(f"SUCCESS: Found {len(data['sources'])} sources")
    
    def test_create_and_delete_source(self):
        """Test creating and deleting a source"""
        # Create source
        new_source = {
            "name": "TEST_Source_For_Testing",
            "url": "https://test-source.example.com",
            "category": "news"
        }
        create_response = requests.post(f"{BASE_URL}/api/sources", json=new_source)
        assert create_response.status_code == 200
        created = create_response.json()
        assert created["name"] == new_source["name"]
        source_id = created["id"]
        print(f"SUCCESS: Created source with ID: {source_id}")
        
        # Delete source
        delete_response = requests.delete(f"{BASE_URL}/api/sources/{source_id}")
        assert delete_response.status_code == 200
        print(f"SUCCESS: Deleted source {source_id}")


class TestSourceHealthMonitoring:
    """Tests for source health monitoring endpoint"""
    
    def test_get_sources_health(self):
        """Test GET /api/sources/health endpoint"""
        response = requests.get(f"{BASE_URL}/api/sources/health")
        assert response.status_code == 200
        data = response.json()
        assert "health" in data
        assert isinstance(data["health"], list)
        print(f"SUCCESS: Source health endpoint returns {len(data['health'])} health records")
        
        # Validate health record structure if any exist
        if data["health"]:
            health_record = data["health"][0]
            assert "source_id" in health_record
            assert "source_name" in health_record
            assert "success_rate" in health_record
            print(f"SUCCESS: Health record structure validated - Source: {health_record['source_name']}, Success Rate: {health_record['success_rate']}%")


class TestBriefsEndpoints:
    """Tests for briefs archive and PDF export"""
    
    def test_list_briefs(self):
        """Test GET /api/briefs endpoint"""
        response = requests.get(f"{BASE_URL}/api/briefs")
        assert response.status_code == 200
        data = response.json()
        assert "briefs" in data
        assert isinstance(data["briefs"], list)
        print(f"SUCCESS: Found {len(data['briefs'])} briefs in archive")
        return data["briefs"]
    
    def test_get_latest_brief(self):
        """Test GET /api/brief/latest endpoint"""
        response = requests.get(f"{BASE_URL}/api/brief/latest")
        assert response.status_code == 200
        data = response.json()
        # May return message if no briefs or actual brief data
        if "message" in data and data.get("brief") is None:
            print(f"INFO: No briefs available yet - {data['message']}")
        else:
            assert "id" in data or "events" in data
            print(f"SUCCESS: Latest brief retrieved")
    
    def test_export_brief_to_pdf(self):
        """Test GET /api/brief/{id}/pdf endpoint"""
        # First get list of briefs
        briefs_response = requests.get(f"{BASE_URL}/api/briefs")
        briefs = briefs_response.json().get("briefs", [])
        
        if not briefs:
            pytest.skip("No briefs available to test PDF export")
        
        brief_id = briefs[0]["id"]
        response = requests.get(f"{BASE_URL}/api/brief/{brief_id}/pdf")
        assert response.status_code == 200
        assert response.headers.get("content-type") == "application/pdf"
        assert len(response.content) > 0
        print(f"SUCCESS: PDF export for brief {brief_id} - Size: {len(response.content)} bytes")
    
    def test_get_brief_by_id(self):
        """Test GET /api/brief/{id} endpoint"""
        # First get list of briefs
        briefs_response = requests.get(f"{BASE_URL}/api/briefs")
        briefs = briefs_response.json().get("briefs", [])
        
        if not briefs:
            pytest.skip("No briefs available to test")
        
        brief_id = briefs[0]["id"]
        response = requests.get(f"{BASE_URL}/api/brief/{brief_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == brief_id
        print(f"SUCCESS: Retrieved brief by ID: {brief_id}")


class TestScheduledRunsEndpoints:
    """Tests for scheduled runs (cron-based) endpoints"""
    
    def test_list_schedules(self):
        """Test GET /api/schedules endpoint"""
        response = requests.get(f"{BASE_URL}/api/schedules")
        assert response.status_code == 200
        data = response.json()
        assert "schedules" in data
        assert isinstance(data["schedules"], list)
        print(f"SUCCESS: Found {len(data['schedules'])} scheduled runs")
    
    def test_create_and_delete_schedule(self):
        """Test POST /api/schedules and DELETE /api/schedules/{id}"""
        # Create schedule with valid cron expression (every day at 9am)
        new_schedule = {
            "name": "TEST_Daily_Morning_Run",
            "cron_expression": "0 9 * * *",
            "enabled": False
        }
        create_response = requests.post(f"{BASE_URL}/api/schedules", json=new_schedule)
        assert create_response.status_code == 200
        data = create_response.json()
        assert "schedule" in data
        schedule_id = data["schedule"]["id"]
        print(f"SUCCESS: Created schedule with ID: {schedule_id}")
        
        # Delete schedule
        delete_response = requests.delete(f"{BASE_URL}/api/schedules/{schedule_id}")
        assert delete_response.status_code == 200
        print(f"SUCCESS: Deleted schedule {schedule_id}")
    
    def test_invalid_cron_expression(self):
        """Test POST /api/schedules with invalid cron"""
        invalid_schedule = {
            "name": "TEST_Invalid_Schedule",
            "cron_expression": "invalid cron",
            "enabled": False
        }
        response = requests.post(f"{BASE_URL}/api/schedules", json=invalid_schedule)
        assert response.status_code == 400
        print("SUCCESS: Invalid cron expression correctly rejected")


class TestEmailConfiguration:
    """Tests for email configuration endpoint"""
    
    def test_get_email_config(self):
        """Test GET /api/email/config endpoint"""
        response = requests.get(f"{BASE_URL}/api/email/config")
        assert response.status_code == 200
        data = response.json()
        assert "from_email" in data
        assert "recipients" in data
        assert "domain_verified" in data
        
        # Verify domain is kirikomal.com
        from_email = data["from_email"]
        domain_verified = data["domain_verified"]
        print(f"SUCCESS: Email config - From: {from_email}, Domain Verified: {domain_verified}")
        
        # Check if kirikomal.com domain is used
        if "kirikomal.com" in from_email:
            print("SUCCESS: Email domain is kirikomal.com as expected")
        else:
            print(f"WARNING: Email domain is not kirikomal.com - From: {from_email}")


class TestAgenticInsightsEndpoints:
    """Tests for agentic insights endpoints"""
    
    def test_get_latest_insights(self):
        """Test GET /api/agentic/insights/latest"""
        response = requests.get(f"{BASE_URL}/api/agentic/insights/latest")
        assert response.status_code == 200
        data = response.json()
        # May return message if no insights or actual insight data
        if "message" in data:
            print(f"INFO: {data['message']}")
        else:
            assert "id" in data
            print(f"SUCCESS: Latest insights retrieved")
    
    def test_get_trends(self):
        """Test GET /api/trends"""
        response = requests.get(f"{BASE_URL}/api/trends")
        assert response.status_code == 200
        data = response.json()
        assert "trends" in data
        print(f"SUCCESS: Found {len(data['trends'])} trends")


class TestRunsEndpoints:
    """Tests for runs endpoints"""
    
    def test_get_latest_run(self):
        """Test GET /api/runs/latest"""
        response = requests.get(f"{BASE_URL}/api/runs/latest")
        assert response.status_code == 200
        data = response.json()
        if "message" in data:
            print(f"INFO: {data['message']}")
        else:
            assert "id" in data
            print(f"SUCCESS: Latest run - ID: {data['id']}, Status: {data.get('status', 'unknown')}")
    
    def test_get_latest_logs(self):
        """Test GET /api/logs/latest"""
        response = requests.get(f"{BASE_URL}/api/logs/latest")
        assert response.status_code == 200
        data = response.json()
        assert "logs" in data
        print(f"SUCCESS: Found {len(data['logs'])} logs")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
