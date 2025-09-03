import requests
import sys
import time
from datetime import datetime

class VeloraAPITester:
    def __init__(self, base_url="https://velora-cloud.preview.emergentagent.com/api"):
        self.base_url = base_url
        self.tests_run = 0
        self.tests_passed = 0
        self.developer_id = None
        self.service_id = None

    def run_test(self, name, method, endpoint, expected_status, data=None, params=None):
        """Run a single API test"""
        url = f"{self.base_url}/{endpoint}" if endpoint else self.base_url
        headers = {'Content-Type': 'application/json'}

        self.tests_run += 1
        print(f"\n🔍 Testing {name}...")
        print(f"   URL: {url}")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, params=params)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=headers)
            elif method == 'DELETE':
                response = requests.delete(url, headers=headers)

            success = response.status_code == expected_status
            if success:
                self.tests_passed += 1
                print(f"✅ Passed - Status: {response.status_code}")
                try:
                    return True, response.json()
                except:
                    return True, {}
            else:
                print(f"❌ Failed - Expected {expected_status}, got {response.status_code}")
                try:
                    print(f"   Response: {response.text}")
                except:
                    pass

            return False, {}

        except Exception as e:
            print(f"❌ Failed - Error: {str(e)}")
            return False, {}

    def test_root_endpoint(self):
        """Test root API endpoint"""
        success, response = self.run_test(
            "Root API Endpoint",
            "GET",
            "",
            200
        )
        return success

    def test_create_developer(self):
        """Test developer creation"""
        developer_data = {
            "name": "Test Developer",
            "email": "test@velora.dev",
            "github_username": "test-dev"
        }
        
        success, response = self.run_test(
            "Create Developer",
            "POST",
            "developers",
            200,
            data=developer_data
        )
        
        if success and 'id' in response:
            self.developer_id = response['id']
            print(f"   Developer ID: {self.developer_id}")
            return True
        return False

    def test_get_developers(self):
        """Test getting all developers"""
        success, response = self.run_test(
            "Get All Developers",
            "GET",
            "developers",
            200
        )
        
        if success and isinstance(response, list):
            print(f"   Found {len(response)} developers")
            return True
        return False

    def test_get_developer_by_id(self):
        """Test getting developer by ID"""
        if not self.developer_id:
            print("❌ Skipping - No developer ID available")
            return False
            
        success, response = self.run_test(
            "Get Developer by ID",
            "GET",
            f"developers/{self.developer_id}",
            200
        )
        return success

    def test_create_service(self):
        """Test service creation"""
        if not self.developer_id:
            print("❌ Skipping - No developer ID available")
            return False
            
        service_data = {
            "name": "Test API Service",
            "description": "A test API service for the platform",
            "service_type": "api",
            "developer_id": self.developer_id
        }
        
        success, response = self.run_test(
            "Create Service",
            "POST",
            "services",
            200,
            data=service_data
        )
        
        if success and 'id' in response:
            self.service_id = response['id']
            print(f"   Service ID: {self.service_id}")
            print(f"   Service Status: {response.get('status', 'unknown')}")
            return True
        return False

    def test_get_services(self):
        """Test getting all services"""
        success, response = self.run_test(
            "Get All Services",
            "GET",
            "services",
            200
        )
        
        if success and isinstance(response, list):
            print(f"   Found {len(response)} services")
            return True
        return False

    def test_get_services_by_developer(self):
        """Test getting services by developer ID"""
        if not self.developer_id:
            print("❌ Skipping - No developer ID available")
            return False
            
        success, response = self.run_test(
            "Get Services by Developer",
            "GET",
            "services",
            200,
            params={"developer_id": self.developer_id}
        )
        
        if success and isinstance(response, list):
            print(f"   Found {len(response)} services for developer")
            return True
        return False

    def test_get_service_by_id(self):
        """Test getting service by ID"""
        if not self.service_id:
            print("❌ Skipping - No service ID available")
            return False
            
        success, response = self.run_test(
            "Get Service by ID",
            "GET",
            f"services/{self.service_id}",
            200
        )
        
        if success:
            print(f"   Service Name: {response.get('name', 'unknown')}")
            print(f"   Service Status: {response.get('status', 'unknown')}")
            return True
        return False

    def test_service_pipeline(self):
        """Test getting service pipeline"""
        if not self.service_id:
            print("❌ Skipping - No service ID available")
            return False
            
        # Wait a bit for pipeline to be created
        print("   Waiting for pipeline creation...")
        time.sleep(3)
        
        success, response = self.run_test(
            "Get Service Pipeline",
            "GET",
            f"services/{self.service_id}/pipeline",
            200
        )
        
        if success:
            print(f"   Pipeline Status: {response.get('status', 'unknown')}")
            print(f"   Pipeline Stage: {response.get('stage', 'unknown')}")
            print(f"   Pipeline Progress: {response.get('progress', 0)}%")
            return True
        return False

    def test_service_metrics(self):
        """Test getting service metrics"""
        if not self.service_id:
            print("❌ Skipping - No service ID available")
            return False
            
        success, response = self.run_test(
            "Get Service Metrics",
            "GET",
            f"services/{self.service_id}/metrics",
            200
        )
        
        if success and isinstance(response, list):
            print(f"   Found {len(response)} metric data points")
            return True
        return False

    def test_service_logs(self):
        """Test getting service logs"""
        if not self.service_id:
            print("❌ Skipping - No service ID available")
            return False
            
        success, response = self.run_test(
            "Get Service Logs",
            "GET",
            f"services/{self.service_id}/logs",
            200
        )
        
        if success and isinstance(response, list):
            print(f"   Found {len(response)} log entries")
            return True
        return False

    def test_admin_stats(self):
        """Test admin cluster stats"""
        success, response = self.run_test(
            "Get Admin Cluster Stats",
            "GET",
            "admin/stats",
            200
        )
        
        if success:
            print(f"   Total Services: {response.get('total_services', 0)}")
            print(f"   Running Services: {response.get('running_services', 0)}")
            print(f"   Total Developers: {response.get('total_developers', 0)}")
            return True
        return False

    def test_admin_developers_activity(self):
        """Test admin developers activity"""
        success, response = self.run_test(
            "Get Developers Activity",
            "GET",
            "admin/developers-activity",
            200
        )
        
        if success and isinstance(response, list):
            print(f"   Found {len(response)} developer activity records")
            return True
        return False

    def test_service_rollback(self):
        """Test service rollback"""
        if not self.service_id:
            print("❌ Skipping - No service ID available")
            return False
            
        success, response = self.run_test(
            "Service Rollback",
            "POST",
            f"services/{self.service_id}/rollback",
            200
        )
        return success

    def test_delete_service(self):
        """Test service deletion"""
        if not self.service_id:
            print("❌ Skipping - No service ID available")
            return False
            
        success, response = self.run_test(
            "Delete Service",
            "DELETE",
            f"services/{self.service_id}",
            200
        )
        return success

def main():
    print("🚀 Starting Velora API Testing...")
    print("=" * 50)
    
    tester = VeloraAPITester()
    
    # Test sequence
    tests = [
        tester.test_root_endpoint,
        tester.test_create_developer,
        tester.test_get_developers,
        tester.test_get_developer_by_id,
        tester.test_create_service,
        tester.test_get_services,
        tester.test_get_services_by_developer,
        tester.test_get_service_by_id,
        tester.test_service_pipeline,
        tester.test_service_metrics,
        tester.test_service_logs,
        tester.test_admin_stats,
        tester.test_admin_developers_activity,
        tester.test_service_rollback,
        tester.test_delete_service
    ]
    
    # Run all tests
    for test in tests:
        test()
        time.sleep(0.5)  # Small delay between tests
    
    # Print final results
    print("\n" + "=" * 50)
    print(f"📊 Final Results: {tester.tests_passed}/{tester.tests_run} tests passed")
    
    if tester.tests_passed == tester.tests_run:
        print("🎉 All tests passed! Backend API is working correctly.")
        return 0
    else:
        failed_tests = tester.tests_run - tester.tests_passed
        print(f"⚠️  {failed_tests} test(s) failed. Please check the issues above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())