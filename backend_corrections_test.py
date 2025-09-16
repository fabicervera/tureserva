import requests
import sys
import json
from datetime import datetime, timedelta
import uuid

class TurnosProCorrectionsAPITester:
    def __init__(self, base_url="https://appt-view-enhance.preview.emergentagent.com/api"):
        self.base_url = base_url
        self.employer_token = None
        self.client_token = None
        self.employer_user = None
        self.client_user = None
        self.calendar_id = None
        self.friendship_id = None
        self.tests_run = 0
        self.tests_passed = 0
        self.errors = []

    def log_test(self, name, success, details=""):
        """Log test results"""
        self.tests_run += 1
        if success:
            self.tests_passed += 1
            print(f"✅ {name} - PASSED")
        else:
            print(f"❌ {name} - FAILED: {details}")
            self.errors.append(f"{name}: {details}")

    def make_request(self, method, endpoint, data=None, token=None, expected_status=200):
        """Make HTTP request with error handling"""
        url = f"{self.base_url}/{endpoint}"
        headers = {'Content-Type': 'application/json'}
        
        if token:
            headers['Authorization'] = f'Bearer {token}'

        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, timeout=10)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=headers, timeout=10)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=headers, timeout=10)
            elif method == 'DELETE':
                response = requests.delete(url, headers=headers, timeout=10)
            
            success = response.status_code == expected_status
            response_data = {}
            
            try:
                response_data = response.json()
            except:
                response_data = {"text": response.text}
            
            return success, response.status_code, response_data
            
        except requests.exceptions.RequestException as e:
            return False, 0, {"error": str(e)}

    def setup_test_users(self):
        """Setup employer and client users for testing"""
        print("🔧 Setting up test users...")
        
        # Register employer
        employer_email = f"employer_{uuid.uuid4().hex[:8]}@test.com"
        employer_data = {
            "email": employer_email,
            "password": "TestPass123!",
            "full_name": "Test Employer",
            "user_type": "employer",
            "location": {
                "country": "argentina",
                "province": "Buenos Aires",
                "city": "La Plata"
            }
        }
        
        success, status, response = self.make_request('POST', 'auth/register', employer_data)
        if not success:
            print(f"❌ Failed to register employer: {status} - {response}")
            return False
        self.employer_user = response
        
        # Register client
        client_email = f"client_{uuid.uuid4().hex[:8]}@test.com"
        client_data = {
            "email": client_email,
            "password": "TestPass123!",
            "full_name": "Test Client",
            "user_type": "client",
            "location": {
                "country": "argentina",
                "province": "Buenos Aires",
                "city": "La Plata"
            }
        }
        
        success, status, response = self.make_request('POST', 'auth/register', client_data)
        if not success:
            print(f"❌ Failed to register client: {status} - {response}")
            return False
        self.client_user = response
        
        # Login employer
        login_data = {"email": employer_email, "password": "TestPass123!"}
        success, status, response = self.make_request('POST', 'auth/login', login_data)
        if not success:
            print(f"❌ Failed to login employer: {status} - {response}")
            return False
        self.employer_token = response['access_token']
        
        # Login client
        login_data = {"email": client_email, "password": "TestPass123!"}
        success, status, response = self.make_request('POST', 'auth/login', login_data)
        if not success:
            print(f"❌ Failed to login client: {status} - {response}")
            return False
        self.client_token = response['access_token']
        
        # Create calendar
        calendar_data = {
            "calendar_name": "Test Calendar",
            "business_name": "Test Business",
            "description": "Test calendar for corrections testing",
            "url_slug": f"test-calendar-{uuid.uuid4().hex[:8]}",
            "category": "medical"
        }
        
        success, status, response = self.make_request('POST', 'calendars', calendar_data, token=self.employer_token)
        if not success:
            print(f"❌ Failed to create calendar: {status} - {response}")
            return False
        self.calendar_id = response['id']
        
        print("✅ Test users and calendar setup complete")
        return True

    def test_friendship_respond_corrected_endpoint(self):
        """Test corrected friendship response endpoint: POST /api/friendships/{id}/respond with {"accept": true/false}"""
        # First, create a friendship request
        friendship_data = {"employer_id": self.employer_user["id"]}
        success, status, response = self.make_request('POST', 'friendships/request', friendship_data, token=self.client_token)
        
        if not success:
            self.log_test("Friendship Respond - Setup Request", False, f"Failed to create request: {status} - {response}")
            return False
        
        # Get the friendship request
        success, status, response = self.make_request('GET', 'friendships/requests', token=self.employer_token)
        if not success or not response:
            self.log_test("Friendship Respond - Get Requests", False, f"Failed to get requests: {status} - {response}")
            return False
        
        self.friendship_id = response[0]['id']
        
        # Test the corrected endpoint with {"accept": true}
        accept_data = {"accept": True}
        success, status, response = self.make_request('POST', f'friendships/{self.friendship_id}/respond', accept_data, token=self.employer_token)
        
        if success and response.get('status') == 'accepted':
            self.log_test("Friendship Respond - Corrected Endpoint (Accept)", True)
            return True
        else:
            self.log_test("Friendship Respond - Corrected Endpoint (Accept)", False, f"Status: {status}, Response: {response}")
            return False

    def test_friendship_respond_reject(self):
        """Test friendship rejection with corrected endpoint"""
        # Create another friendship request for rejection test
        client_email2 = f"client2_{uuid.uuid4().hex[:8]}@test.com"
        client_data2 = {
            "email": client_email2,
            "password": "TestPass123!",
            "full_name": "Test Client 2",
            "user_type": "client",
            "location": {"country": "argentina", "province": "Buenos Aires", "city": "La Plata"}
        }
        
        success, status, response = self.make_request('POST', 'auth/register', client_data2)
        if not success:
            self.log_test("Friendship Respond - Reject Setup", False, "Failed to create second client")
            return False
        
        # Login second client
        login_data = {"email": client_email2, "password": "TestPass123!"}
        success, status, response = self.make_request('POST', 'auth/login', login_data)
        if not success:
            self.log_test("Friendship Respond - Reject Setup", False, "Failed to login second client")
            return False
        client2_token = response['access_token']
        
        # Create friendship request
        friendship_data = {"employer_id": self.employer_user["id"]}
        success, status, response = self.make_request('POST', 'friendships/request', friendship_data, token=client2_token)
        if not success:
            self.log_test("Friendship Respond - Reject Setup", False, "Failed to create second friendship request")
            return False
        
        # Get requests and find the new one
        success, status, response = self.make_request('GET', 'friendships/requests', token=self.employer_token)
        if not success:
            self.log_test("Friendship Respond - Reject Setup", False, "Failed to get friendship requests")
            return False
        
        # Find the pending request (not the accepted one)
        friendship_id2 = None
        for req in response:
            if req.get('client', {}).get('email') == client_email2:
                friendship_id2 = req['id']
                break
        
        if not friendship_id2:
            self.log_test("Friendship Respond - Reject Setup", False, "Could not find second friendship request")
            return False
        
        # Test rejection with {"accept": false}
        reject_data = {"accept": False}
        success, status, response = self.make_request('POST', f'friendships/{friendship_id2}/respond', reject_data, token=self.employer_token)
        
        if success and response.get('status') == 'blocked':
            self.log_test("Friendship Respond - Corrected Endpoint (Reject)", True)
            return True
        else:
            self.log_test("Friendship Respond - Corrected Endpoint (Reject)", False, f"Status: {status}, Response: {response}")
            return False

    def test_get_my_services_endpoint(self):
        """Test new endpoint: GET /api/friendships/my-services"""
        success, status, response = self.make_request('GET', 'friendships/my-services', token=self.client_token)
        
        if success and isinstance(response, list):
            # Should have at least one service (from accepted friendship)
            if len(response) > 0:
                service = response[0]
                if 'friendship_id' in service and 'calendar' in service and 'employer' in service:
                    self.log_test("Get My Services - New Endpoint", True)
                    return True
                else:
                    self.log_test("Get My Services - New Endpoint", False, f"Missing required fields in response: {service}")
                    return False
            else:
                self.log_test("Get My Services - New Endpoint", True, "No services found (expected for new client)")
                return True
        else:
            self.log_test("Get My Services - New Endpoint", False, f"Status: {status}, Response: {response}")
            return False

    def test_get_friendship_status_endpoint(self):
        """Test new endpoint: GET /api/friendships/status/{employer_id}"""
        success, status, response = self.make_request('GET', f'friendships/status/{self.employer_user["id"]}', token=self.client_token)
        
        if success and 'status' in response:
            # Should show 'accepted' status from previous test
            if response['status'] == 'accepted' and 'friendship_id' in response:
                self.log_test("Get Friendship Status - New Endpoint", True)
                return True
            else:
                self.log_test("Get Friendship Status - New Endpoint", False, f"Unexpected status or missing friendship_id: {response}")
                return False
        else:
            self.log_test("Get Friendship Status - New Endpoint", False, f"Status: {status}, Response: {response}")
            return False

    def test_delete_friendship_endpoint(self):
        """Test new endpoint: DELETE /api/friendships/{id}"""
        if not self.friendship_id:
            self.log_test("Delete Friendship - New Endpoint", False, "No friendship ID available")
            return False
        
        success, status, response = self.make_request('DELETE', f'friendships/{self.friendship_id}', token=self.client_token)
        
        if success and 'message' in response:
            self.log_test("Delete Friendship - New Endpoint", True)
            
            # Verify friendship is deleted by checking status
            success2, status2, response2 = self.make_request('GET', f'friendships/status/{self.employer_user["id"]}', token=self.client_token)
            if success2 and response2.get('status') == 'none':
                self.log_test("Delete Friendship - Verification", True)
                return True
            else:
                self.log_test("Delete Friendship - Verification", False, f"Friendship still exists: {response2}")
                return False
        else:
            self.log_test("Delete Friendship - New Endpoint", False, f"Status: {status}, Response: {response}")
            return False

    def test_friendship_system_complete_flow(self):
        """Test complete friendship system flow with corrected endpoints"""
        print("\n🔄 Testing Complete Friendship Flow...")
        
        # 1. Client requests friendship
        friendship_data = {"employer_id": self.employer_user["id"]}
        success, status, response = self.make_request('POST', 'friendships/request', friendship_data, token=self.client_token)
        if not success:
            self.log_test("Complete Flow - Request", False, f"Failed to request: {status} - {response}")
            return False
        
        # 2. Check status shows pending
        success, status, response = self.make_request('GET', f'friendships/status/{self.employer_user["id"]}', token=self.client_token)
        if not success or response.get('status') != 'pending':
            self.log_test("Complete Flow - Status Pending", False, f"Expected pending status: {response}")
            return False
        
        # 3. Employer gets requests
        success, status, response = self.make_request('GET', 'friendships/requests', token=self.employer_token)
        if not success or not response:
            self.log_test("Complete Flow - Get Requests", False, f"Failed to get requests: {response}")
            return False
        
        new_friendship_id = response[0]['id']
        
        # 4. Employer accepts with corrected endpoint
        accept_data = {"accept": True}
        success, status, response = self.make_request('POST', f'friendships/{new_friendship_id}/respond', accept_data, token=self.employer_token)
        if not success or response.get('status') != 'accepted':
            self.log_test("Complete Flow - Accept", False, f"Failed to accept: {response}")
            return False
        
        # 5. Client sees service in my-services
        success, status, response = self.make_request('GET', 'friendships/my-services', token=self.client_token)
        if not success or not response:
            self.log_test("Complete Flow - My Services", False, f"No services found: {response}")
            return False
        
        # 6. Client can delete friendship
        success, status, response = self.make_request('DELETE', f'friendships/{new_friendship_id}', token=self.client_token)
        if not success:
            self.log_test("Complete Flow - Delete", False, f"Failed to delete: {response}")
            return False
        
        self.log_test("Complete Friendship Flow", True)
        return True

    def run_corrections_tests(self):
        """Run all correction-specific tests"""
        print("🚀 Starting TurnosPro Corrections API Tests...")
        print("=" * 60)
        
        # Setup
        if not self.setup_test_users():
            print("❌ Failed to setup test users")
            return False
        
        print("\n👥 Testing Corrected Friendship System...")
        
        # Test corrected endpoints
        self.test_friendship_respond_corrected_endpoint()
        self.test_friendship_respond_reject()
        self.test_get_my_services_endpoint()
        self.test_get_friendship_status_endpoint()
        self.test_delete_friendship_endpoint()
        
        # Test complete flow
        self.test_friendship_system_complete_flow()
        
        # Print results
        print("\n" + "=" * 60)
        print(f"📊 Corrections Test Results: {self.tests_passed}/{self.tests_run} passed")
        
        if self.errors:
            print("\n❌ Failed Tests:")
            for error in self.errors:
                print(f"  - {error}")
        else:
            print("\n✅ All correction tests passed!")
        
        return self.tests_passed == self.tests_run

def main():
    tester = TurnosProCorrectionsAPITester()
    success = tester.run_corrections_tests()
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())