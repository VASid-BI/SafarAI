#!/usr/bin/env python3
"""
Comprehensive SafarAI Pipeline Testing
Tests the complete end-to-end functionality as requested in the review.
"""

import requests
import json
import time
from datetime import datetime
import sys

class SafarAIPipelineTester:
    def __init__(self, base_url="https://stacker.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.test_results = []
        self.run_id = None
        
    def log_test(self, test_name, success, details=""):
        """Log test result"""
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}")
        if details:
            print(f"    {details}")
        self.test_results.append({
            "test": test_name,
            "success": success,
            "details": details,
            "timestamp": datetime.now().isoformat()
        })
        return success
    
    def make_request(self, method, endpoint, data=None, timeout=30):
        """Make API request with error handling"""
        url = f"{self.api_url}/{endpoint}"
        headers = {'Content-Type': 'application/json'}
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, timeout=timeout)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=headers, timeout=timeout)
            else:
                raise ValueError(f"Unsupported method: {method}")
            
            return response
        except Exception as e:
            print(f"    Request failed: {str(e)}")
            return None

    def test_pipeline_execution(self):
        """Test 1: Pipeline Execution Test"""
        print("\n🔄 Testing Pipeline Execution...")
        
        # Trigger new pipeline run
        response = self.make_request('POST', 'run')
        if not response or response.status_code != 200:
            return self.log_test("Pipeline Trigger", False, "Failed to trigger pipeline run")
        
        data = response.json()
        self.run_id = data.get('run_id')
        
        if not self.run_id:
            return self.log_test("Pipeline Trigger", False, "No run_id returned")
        
        self.log_test("Pipeline Trigger", True, f"Started run: {self.run_id}")
        
        # Monitor run status
        print("    Monitoring pipeline execution...")
        max_wait = 120  # 2 minutes max wait
        start_time = time.time()
        
        while time.time() - start_time < max_wait:
            response = self.make_request('GET', f'runs/{self.run_id}')
            if response and response.status_code == 200:
                run_data = response.json()
                status = run_data.get('status', 'unknown')
                
                print(f"    Status: {status} | Sources: {run_data.get('sources_ok', 0)}/{run_data.get('sources_total', 0)} | Events: {run_data.get('events_created', 0)}")
                
                if status in ['success', 'partial_failure', 'failure']:
                    # Pipeline completed
                    if status == 'success':
                        return self.log_test("Pipeline Execution", True, 
                            f"Pipeline completed successfully. Sources: {run_data.get('sources_ok')}/{run_data.get('sources_total')}, Events: {run_data.get('events_created')}")
                    elif status == 'partial_failure':
                        return self.log_test("Pipeline Execution", True, 
                            f"Pipeline completed with partial failures. Sources: {run_data.get('sources_ok')}/{run_data.get('sources_total')}, Events: {run_data.get('events_created')}")
                    else:
                        return self.log_test("Pipeline Execution", False, 
                            f"Pipeline failed. Sources: {run_data.get('sources_ok')}/{run_data.get('sources_total')}")
            
            time.sleep(5)
        
        return self.log_test("Pipeline Execution", False, "Pipeline did not complete within timeout")

    def test_active_sources_crawling(self):
        """Test 2: Verify Active Sources Crawling"""
        print("\n📡 Testing Active Sources Crawling...")
        
        # Get sources
        response = self.make_request('GET', 'sources')
        if not response or response.status_code != 200:
            return self.log_test("Sources Check", False, "Failed to get sources")
        
        sources_data = response.json()
        sources = sources_data.get('sources', [])
        active_sources = [s for s in sources if s.get('active', False)]
        
        if len(active_sources) != 9:
            return self.log_test("Active Sources Count", False, f"Expected 9 active sources, found {len(active_sources)}")
        
        self.log_test("Active Sources Count", True, f"Found {len(active_sources)} active sources")
        
        # Check if sources are being processed in logs
        if self.run_id:
            response = self.make_request('GET', f'logs/{self.run_id}')
            if response and response.status_code == 200:
                logs_data = response.json()
                logs = logs_data.get('logs', [])
                
                source_logs = [log for log in logs if 'Processing source:' in log.get('message', '')]
                
                if len(source_logs) >= 6:  # Should process at least the default sources
                    return self.log_test("Sources Processing", True, f"Found {len(source_logs)} source processing logs")
                else:
                    return self.log_test("Sources Processing", False, f"Only found {len(source_logs)} source processing logs")
        
        return self.log_test("Sources Processing", False, "No run ID available to check logs")

    def test_content_classification(self):
        """Test 3: Content Fetching and Classification"""
        print("\n🧠 Testing Content Classification...")
        
        # Check latest run for events
        response = self.make_request('GET', 'runs/latest')
        if not response or response.status_code != 200:
            return self.log_test("Content Classification", False, "Failed to get latest run")
        
        run_data = response.json()
        events_created = run_data.get('events_created', 0)
        items_total = run_data.get('items_total', 0)
        
        if items_total == 0:
            return self.log_test("Content Fetching", False, "No content items were fetched")
        
        self.log_test("Content Fetching", True, f"Fetched {items_total} content items")
        
        if events_created == 0:
            return self.log_test("Content Classification", False, "No events were created from classification")
        
        return self.log_test("Content Classification", True, f"Created {events_created} events from classification")

    def test_email_brief_generation(self):
        """Test 4: Email Brief Generation"""
        print("\n📧 Testing Email Brief Generation...")
        
        # Get latest brief
        response = self.make_request('GET', 'brief/latest')
        if not response or response.status_code != 200:
            return self.log_test("Brief Generation", False, "Failed to get latest brief")
        
        brief_data = response.json()
        
        if 'message' in brief_data and 'No briefs available' in brief_data['message']:
            return self.log_test("Brief Generation", False, "No briefs available")
        
        # Check brief structure
        required_fields = ['id', 'run_id', 'html', 'events', 'created_at']
        for field in required_fields:
            if field not in brief_data:
                return self.log_test("Brief Structure", False, f"Missing field: {field}")
        
        self.log_test("Brief Structure", True, "Brief has all required fields")
        
        # Check HTML content
        html_content = brief_data.get('html', '')
        if not html_content:
            return self.log_test("Brief HTML", False, "Brief HTML is empty")
        
        # Verify HTML contains expected elements
        html_checks = [
            ('DOCTYPE html', 'HTML document structure'),
            ('SafarAI', 'SafarAI branding'),
            ('Intelligence Brief', 'Brief title'),
            ('Events', 'Events section'),
            ('Run Health', 'Pipeline health section')
        ]
        
        for check, description in html_checks:
            if check not in html_content:
                return self.log_test("Brief HTML Content", False, f"Missing {description}")
        
        self.log_test("Brief HTML Content", True, "HTML contains all expected sections")
        
        # Check events in brief
        events = brief_data.get('events', [])
        if not events:
            return self.log_test("Brief Events", False, "No events in brief")
        
        # Verify events don't contain emoji or materiality scores in display
        for event in events[:3]:  # Check first 3 events
            title = event.get('title', '')
            summary = event.get('summary', '')
            
            # Check for emoji (basic check for common emoji ranges)
            emoji_found = any(ord(char) > 127 for char in title + summary)
            if emoji_found:
                return self.log_test("Brief Event Format", False, "Events contain emoji characters")
        
        return self.log_test("Brief Events", True, f"Brief contains {len(events)} properly formatted events")

    def test_email_delivery(self):
        """Test 5: Email Delivery Verification"""
        print("\n📬 Testing Email Delivery...")
        
        # Check latest run for email status
        response = self.make_request('GET', 'runs/latest')
        if not response or response.status_code != 200:
            return self.log_test("Email Delivery Check", False, "Failed to get latest run")
        
        run_data = response.json()
        emails_sent = run_data.get('emails_sent', 0)
        
        if emails_sent == 0:
            return self.log_test("Email Delivery", False, "No emails were sent")
        
        # Check if recipient is configured correctly
        # Note: We can't directly verify email delivery without access to the email service
        # But we can verify the configuration and that the send attempt was made
        
        return self.log_test("Email Delivery", True, f"Email send attempted ({emails_sent} emails)")

    def test_api_health_checks(self):
        """Test 6: API Health Checks"""
        print("\n🏥 Testing API Health Checks...")
        
        health_tests = [
            ('GET', 'stats', 'Platform Statistics'),
            ('GET', 'sources', 'Sources List'),
            ('GET', 'runs/latest', 'Latest Run'),
            ('GET', 'logs/latest', 'Latest Logs'),
            ('GET', 'brief/latest', 'Latest Brief')
        ]
        
        all_passed = True
        for method, endpoint, description in health_tests:
            response = self.make_request(method, endpoint)
            if not response or response.status_code != 200:
                self.log_test(f"Health Check: {description}", False, f"Endpoint /{endpoint} failed")
                all_passed = False
            else:
                self.log_test(f"Health Check: {description}", True, f"Endpoint /{endpoint} working")
        
        return all_passed

    def test_error_handling(self):
        """Test 7: Error Handling"""
        print("\n⚠️  Testing Error Handling...")
        
        # Check logs for any error handling
        if self.run_id:
            response = self.make_request('GET', f'logs/{self.run_id}')
            if response and response.status_code == 200:
                logs_data = response.json()
                logs = logs_data.get('logs', [])
                
                error_logs = [log for log in logs if log.get('level') == 'error']
                warn_logs = [log for log in logs if log.get('level') == 'warn']
                
                if error_logs:
                    error_messages = [log.get('message', '') for log in error_logs]
                    return self.log_test("Error Handling", False, f"Found {len(error_logs)} errors: {error_messages[:3]}")
                
                if warn_logs:
                    self.log_test("Warning Handling", True, f"Found {len(warn_logs)} warnings (handled gracefully)")
                
                return self.log_test("Error Handling", True, "No critical errors found in logs")
        
        return self.log_test("Error Handling", False, "No run ID available to check error logs")

    def run_comprehensive_test(self):
        """Run all comprehensive tests"""
        print("🚀 Starting Comprehensive SafarAI Pipeline Testing...")
        print("=" * 80)
        
        tests = [
            self.test_pipeline_execution,
            self.test_active_sources_crawling,
            self.test_content_classification,
            self.test_email_brief_generation,
            self.test_email_delivery,
            self.test_api_health_checks,
            self.test_error_handling
        ]
        
        passed = 0
        total = 0
        
        for test_func in tests:
            try:
                if test_func():
                    passed += 1
                total += 1
            except Exception as e:
                print(f"❌ Test {test_func.__name__} failed with exception: {e}")
                total += 1
        
        # Summary
        print("\n" + "=" * 80)
        print(f"📊 Comprehensive Test Results: {passed}/{total} test categories passed")
        
        detailed_results = sum(1 for r in self.test_results if r['success'])
        total_detailed = len(self.test_results)
        print(f"📋 Detailed Test Results: {detailed_results}/{total_detailed} individual tests passed")
        
        # Show failed tests
        failed_tests = [r for r in self.test_results if not r['success']]
        if failed_tests:
            print(f"\n❌ Failed Tests ({len(failed_tests)}):")
            for test in failed_tests:
                print(f"   • {test['test']}: {test['details']}")
        
        return passed == total and detailed_results == total_detailed

def main():
    tester = SafarAIPipelineTester()
    success = tester.run_comprehensive_test()
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())