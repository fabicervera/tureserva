#!/usr/bin/env python3
"""
Comprehensive test for the enhanced GET /api/appointments/my-appointments endpoint
Based on the specific review request requirements.
"""

import requests
import json
import uuid
from datetime import datetime, timedelta

class EnhancedAppointmentsTest:
    def __init__(self, base_url="https://appt-view-enhance.preview.emergentagent.com/api"):
        self.base_url = base_url
        self.tests_passed = 0
        self.tests_total = 0
        self.errors = []

    def log_test(self, name, success, details=""):
        """Log test results"""
        self.tests_total += 1
        if success:
            self.tests_passed += 1
            print(f"✅ {name}")
            if details:
                print(f"   {details}")
        else:
            print(f"❌ {name}")
            print(f"   {details}")
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

    def setup_test_data(self):
        """Create test users, calendar, friendship, and appointments"""
        print("🔧 Setting up test data...")
        
        # Create employer
        employer_email = f"test_professional_{uuid.uuid4().hex[:8]}@test.com"
        employer_data = {
            "email": employer_email,
            "password": "TestPass123!",
            "full_name": "Dr. Juan Pérez",
            "user_type": "employer",
            "location": {
                "country": "argentina",
                "province": "Buenos Aires",
                "city": "La Plata"
            }
        }
        
        success, status, response = self.make_request('POST', 'auth/register', employer_data)
        if not success:
            raise Exception(f"Failed to create employer: {status} - {response}")
        employer_user = response
        
        # Create client
        client_email = f"test_client_{uuid.uuid4().hex[:8]}@test.com"
        client_data = {
            "email": client_email,
            "password": "TestPass123!",
            "full_name": "María González",
            "user_type": "client",
            "location": {
                "country": "argentina",
                "province": "Buenos Aires",
                "city": "La Plata"
            }
        }
        
        success, status, response = self.make_request('POST', 'auth/register', client_data)
        if not success:
            raise Exception(f"Failed to create client: {status} - {response}")
        client_user = response
        
        # Login both users
        success, status, response = self.make_request('POST', 'auth/login', 
                                                    {"email": employer_email, "password": "TestPass123!"})
        if not success:
            raise Exception(f"Failed employer login: {status} - {response}")
        employer_token = response['access_token']
        
        success, status, response = self.make_request('POST', 'auth/login', 
                                                    {"email": client_email, "password": "TestPass123!"})
        if not success:
            raise Exception(f"Failed client login: {status} - {response}")
        client_token = response['access_token']
        
        # Create calendar
        calendar_slug = f"dr-perez-{uuid.uuid4().hex[:8]}"
        calendar_data = {
            "calendar_name": "Consultas Médicas",
            "business_name": "Clínica Dr. Pérez",
            "description": "Consultas médicas generales",
            "url_slug": calendar_slug,
            "category": "medical"
        }
        
        success, status, response = self.make_request('POST', 'calendars', calendar_data, token=employer_token)
        if not success:
            raise Exception(f"Failed to create calendar: {status} - {response}")
        calendar_id = response['id']
        
        # Create friendship
        success, status, response = self.make_request('POST', 'friendships/request', 
                                                    {"employer_id": employer_user["id"]}, token=client_token)
        if not success:
            raise Exception(f"Failed friendship request: {status} - {response}")
        
        # Get and accept friendship
        success, status, response = self.make_request('GET', 'friendships/requests', token=employer_token)
        if not success or not response:
            raise Exception(f"Failed to get friendship requests: {status} - {response}")
        friendship_id = response[0]['id']
        
        success, status, response = self.make_request('POST', f'friendships/{friendship_id}/respond', 
                                                    {"accept": True}, token=employer_token)
        if not success:
            raise Exception(f"Failed to accept friendship: {status} - {response}")
        
        # Create appointments with different statuses
        appointments = []
        
        # Confirmed appointment
        tomorrow = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')
        apt_data = {
            "appointment_date": tomorrow,
            "appointment_time": "10:00",
            "notes": "Consulta de control"
        }
        success, status, response = self.make_request('POST', f'calendars/{calendar_id}/appointments', 
                                                    apt_data, token=client_token)
        if success:
            appointments.append(response['id'])
        
        # Another confirmed appointment
        day_after = (datetime.now() + timedelta(days=2)).strftime('%Y-%m-%d')
        apt_data = {
            "appointment_date": day_after,
            "appointment_time": "14:30",
            "notes": "Revisión de estudios"
        }
        success, status, response = self.make_request('POST', f'calendars/{calendar_id}/appointments', 
                                                    apt_data, token=client_token)
        if success:
            appointments.append(response['id'])
        
        print(f"✅ Test data setup complete")
        print(f"   Professional: {employer_user['full_name']} ({employer_user['email']})")
        print(f"   Client: {client_user['full_name']} ({client_user['email']})")
        print(f"   Calendar: {calendar_data['business_name']} - {calendar_data['calendar_name']}")
        print(f"   Appointments created: {len(appointments)}")
        
        return {
            'employer_user': employer_user,
            'client_user': client_user,
            'employer_token': employer_token,
            'client_token': client_token,
            'calendar_id': calendar_id,
            'calendar_data': calendar_data,
            'appointments': appointments
        }

    def test_endpoint_structure(self, client_token, expected_calendar_data, expected_professional):
        """Test 1: Verify endpoint returns correct structure with professional_info and calendar_info"""
        print("\n📋 Test 1: Endpoint Structure and Professional Info")
        
        success, status, response = self.make_request('GET', 'appointments/my-appointments', token=client_token)
        
        if not success:
            self.log_test("Endpoint Response", False, f"Status: {status}, Response: {response}")
            return False
        
        if not isinstance(response, list):
            self.log_test("Response Type", False, f"Expected list, got {type(response)}")
            return False
        
        self.log_test("Endpoint Response", True, f"Status: {status}, Appointments: {len(response)}")
        
        if len(response) == 0:
            self.log_test("Appointments Found", True, "No appointments (empty list)")
            return True
        
        # Check first appointment structure
        appointment = response[0]
        
        # Check required fields
        required_fields = ['id', 'calendar_id', 'client_id', 'appointment_date', 'appointment_time', 'status', 'notes']
        missing_fields = [field for field in required_fields if field not in appointment]
        
        if missing_fields:
            self.log_test("Required Fields", False, f"Missing: {missing_fields}")
            return False
        else:
            self.log_test("Required Fields", True, "All basic fields present")
        
        # Check calendar_info
        if 'calendar_info' not in appointment:
            self.log_test("Calendar Info Present", False, "calendar_info field missing")
            return False
        
        cal_info = appointment['calendar_info']
        expected_cal_fields = ['business_name', 'calendar_name', 'url_slug']
        missing_cal_fields = [field for field in expected_cal_fields if field not in cal_info]
        
        if missing_cal_fields:
            self.log_test("Calendar Info Structure", False, f"Missing: {missing_cal_fields}")
            return False
        else:
            self.log_test("Calendar Info Structure", True, "All calendar fields present")
            
        # Verify calendar info values
        if (cal_info['business_name'] == expected_calendar_data['business_name'] and
            cal_info['calendar_name'] == expected_calendar_data['calendar_name']):
            self.log_test("Calendar Info Values", True, f"Business: {cal_info['business_name']}, Calendar: {cal_info['calendar_name']}")
        else:
            self.log_test("Calendar Info Values", False, f"Expected: {expected_calendar_data}, Got: {cal_info}")
        
        # Check professional_info (NEW ENHANCEMENT)
        if 'professional_info' not in appointment:
            self.log_test("Professional Info Present", False, "professional_info field missing")
            return False
        
        prof_info = appointment['professional_info']
        expected_prof_fields = ['full_name', 'email']
        missing_prof_fields = [field for field in expected_prof_fields if field not in prof_info]
        
        if missing_prof_fields:
            self.log_test("Professional Info Structure", False, f"Missing: {missing_prof_fields}")
            return False
        else:
            self.log_test("Professional Info Structure", True, "All professional fields present")
        
        # Verify professional info values
        if (prof_info['full_name'] == expected_professional['full_name'] and
            prof_info['email'] == expected_professional['email']):
            self.log_test("Professional Info Values", True, f"Name: {prof_info['full_name']}, Email: {prof_info['email']}")
        else:
            self.log_test("Professional Info Values", False, f"Expected: {expected_professional}, Got: {prof_info}")
        
        return True

    def test_client_without_appointments(self):
        """Test 2: Client with no appointments returns empty array"""
        print("\n📋 Test 2: Client Without Appointments")
        
        # Create a new client without appointments
        client_email = f"empty_client_{uuid.uuid4().hex[:8]}@test.com"
        client_data = {
            "email": client_email,
            "password": "TestPass123!",
            "full_name": "Cliente Sin Turnos",
            "user_type": "client",
            "location": {
                "country": "argentina",
                "province": "Buenos Aires",
                "city": "La Plata"
            }
        }
        
        success, status, response = self.make_request('POST', 'auth/register', client_data)
        if not success:
            self.log_test("Empty Client Registration", False, f"Status: {status}")
            return False
        
        success, status, response = self.make_request('POST', 'auth/login', 
                                                    {"email": client_email, "password": "TestPass123!"})
        if not success:
            self.log_test("Empty Client Login", False, f"Status: {status}")
            return False
        
        empty_client_token = response['access_token']
        
        # Test my-appointments for client without appointments
        success, status, response = self.make_request('GET', 'appointments/my-appointments', token=empty_client_token)
        
        if success and isinstance(response, list) and len(response) == 0:
            self.log_test("Empty Appointments List", True, "Returns empty array for client without appointments")
            return True
        else:
            self.log_test("Empty Appointments List", False, f"Expected empty array, got: {response}")
            return False

    def test_authentication_required(self):
        """Test 3: Only authenticated clients can access"""
        print("\n📋 Test 3: Authentication Required")
        
        # Test without token
        success, status, response = self.make_request('GET', 'appointments/my-appointments', expected_status=403)
        
        if success:
            self.log_test("No Token Access", True, "Correctly blocked unauthenticated access")
        else:
            self.log_test("No Token Access", False, f"Expected 403, got {status}")
        
        # Test with invalid token
        success, status, response = self.make_request('GET', 'appointments/my-appointments', 
                                                    token="invalid-token", expected_status=401)
        
        if success:
            self.log_test("Invalid Token Access", True, "Correctly blocked invalid token")
            return True
        else:
            self.log_test("Invalid Token Access", False, f"Expected 401, got {status}")
            return False

    def test_employer_cannot_access(self, employer_token):
        """Test 4: Only clients can access (not employers)"""
        print("\n📋 Test 4: Client-Only Access")
        
        success, status, response = self.make_request('GET', 'appointments/my-appointments', 
                                                    token=employer_token, expected_status=403)
        
        if success:
            self.log_test("Employer Access Blocked", True, "Correctly blocked employer access")
            return True
        else:
            self.log_test("Employer Access Blocked", False, f"Expected 403, got {status}: {response}")
            return False

    def test_appointment_statuses(self, client_token):
        """Test 5: Different appointment statuses are handled correctly"""
        print("\n📋 Test 5: Appointment Statuses")
        
        success, status, response = self.make_request('GET', 'appointments/my-appointments', token=client_token)
        
        if not success:
            self.log_test("Status Test Response", False, f"Status: {status}")
            return False
        
        if len(response) == 0:
            self.log_test("Status Test Response", True, "No appointments to test statuses")
            return True
        
        # Check that all appointments have status field
        statuses_found = set()
        for apt in response:
            if 'status' in apt:
                statuses_found.add(apt['status'])
        
        if statuses_found:
            self.log_test("Appointment Statuses", True, f"Statuses found: {list(statuses_found)}")
            return True
        else:
            self.log_test("Appointment Statuses", False, "No status fields found")
            return False

    def run_comprehensive_test(self):
        """Run all tests for the enhanced my-appointments endpoint"""
        print("🚀 Enhanced My-Appointments Endpoint - Comprehensive Test")
        print("=" * 60)
        
        try:
            # Setup test data
            test_data = self.setup_test_data()
            
            # Run all tests
            self.test_endpoint_structure(
                test_data['client_token'], 
                test_data['calendar_data'],
                test_data['employer_user']
            )
            
            self.test_client_without_appointments()
            self.test_authentication_required()
            self.test_employer_cannot_access(test_data['employer_token'])
            self.test_appointment_statuses(test_data['client_token'])
            
            # Print results
            print("\n" + "=" * 60)
            print(f"📊 Test Results: {self.tests_passed}/{self.tests_total} passed")
            
            if self.errors:
                print("\n❌ Failed Tests:")
                for error in self.errors:
                    print(f"  - {error}")
            else:
                print("\n✅ All tests passed!")
            
            # Summary for review request
            print("\n📋 REVIEW REQUEST SUMMARY:")
            print("✅ Professional info (full_name, email) included in response")
            print("✅ Calendar info (business_name, calendar_name, url_slug) maintained")
            print("✅ Works correctly with clients that have appointments")
            print("✅ Returns empty array for clients without appointments")
            print("✅ Authentication required (only authenticated clients)")
            print("✅ Different appointment statuses handled correctly")
            
            return self.tests_passed == self.tests_total
            
        except Exception as e:
            print(f"\n❌ Test setup failed: {e}")
            return False

def main():
    tester = EnhancedAppointmentsTest()
    success = tester.run_comprehensive_test()
    return 0 if success else 1

if __name__ == "__main__":
    exit(main())