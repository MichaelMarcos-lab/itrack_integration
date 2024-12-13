import frappe
import requests
import hashlib
import time
from datetime import datetime, timedelta

class ITrackAPIIntegration:
    def __init__(self):
        # Configuration settings (to be set in ERPNext configuration)
        self.base_url = "http://api.itrack.top/api"
        self.account = frappe.db.get_single_value('iTrack Settings', 'account')
        self.password = frappe.db.get_single_value('iTrack Settings', 'password')
        self.access_token = None
        self.token_expiry = None

    def generate_signature(self):
        """Generate MD5 signature for authentication"""
        current_time = int(time.time())
        first_md5 = hashlib.md5(self.password.encode()).hexdigest()
        signature = hashlib.md5(f"{first_md5}{current_time}".encode()).hexdigest()
        return current_time, signature

    def get_access_token(self):
        """Obtain access token from iTrack API"""
        # Check if existing token is valid
        if self.access_token and self.token_expiry and self.token_expiry > datetime.now():
            return self.access_token

        # Generate new token
        current_time, signature = self.generate_signature()
        
        params = {
            'time': current_time,
            'account': self.account,
            'signature': signature
        }
        
        response = requests.get(f"{self.base_url}/authorization", params=params)
        data = response.json()
        
        if data['code'] == 0:
            self.access_token = data['record']['access_token']
            # Set expiry 30 minutes before actual expiration for safety
            self.token_expiry = datetime.now() + timedelta(seconds=data['record']['expires_in'] - 1800)
            return self.access_token
        else:
            frappe.throw(f"Failed to get access token: {data.get('message', 'Unknown error')}")

    def track_vehicle(self, imei):
        """Get latest tracking information for a vehicle"""
        access_token = self.get_access_token()
        
        params = {
            'access_token': access_token,
            'imeis': imei
        }
        
        response = requests.get(f"{self.base_url}/track", params=params)
        data = response.json()
        
        if data['code'] == 0:
            return data['record'][0]
        else:
            frappe.throw(f"Failed to track vehicle: {data.get('message', 'Unknown error')}")

    def get_vehicle_history(self, imei, start_time, end_time):
        """Get vehicle movement history"""
        access_token = self.get_access_token()
        
        params = {
            'access_token': access_token,
            'imei': imei,
            'begintime': int(start_time.timestamp()),
            'endtime': int(end_time.timestamp())
        }
        
        response = requests.get(f"{self.base_url}/playback", params=params)
        data = response.json()
        
        if data['code'] == 0:
            # Parse semicolon-separated records
            history = [
                dict(zip(['longitude', 'latitude', 'gpstime', 'speed', 'course'], 
                         record.split(','))) 
                for record in data['record'].split(';')
            ]
            return history
        else:
            frappe.throw(f"Failed to get vehicle history: {data.get('message', 'Unknown error')}")

    def create_geofence(self, vehicle_doc):
        """Create geofence for a specific vehicle"""
        access_token = self.get_access_token()
        
        # Assuming vehicle doc has geofence-related fields
        params = {
            'access_token': access_token,
            'imei': vehicle_doc.imei,
            'efencename': vehicle_doc.name,
            'alarmtype': vehicle_doc.geofence_type or 0,  # default to 'out'
            'longitude': vehicle_doc.geofence_longitude,
            'latitude': vehicle_doc.geofence_latitude,
            'radius': vehicle_doc.geofence_radius or 300  # default 300 meters
        }
        
        response = requests.post(f"{self.base_url}/geofence/create", params=params)
        data = response.json()
        
        if data['code'] != 0:
            frappe.throw(f"Failed to create geofence: {data.get('message', 'Unknown error')}")

@frappe.whitelist()
def sync_vehicle_tracking(vehicle_name):
    """Sync tracking data for a specific vehicle"""
    vehicle = frappe.get_doc('Vehicle', vehicle_name)
    
    if not vehicle.imei:
        frappe.throw("No IMEI found for this vehicle")
    
    integration = ITrackAPIIntegration()
    
    # Get current tracking data
    tracking_data = integration.track_vehicle(vehicle.imei)
    
    # Update vehicle document
    vehicle.update({
        'last_gps_time': datetime.fromtimestamp(tracking_data['gpstime']),
        'current_longitude': tracking_data['longitude'],
        'current_latitude': tracking_data['latitude'],
        'current_speed': tracking_data['speed'],
        'current_course': tracking_data['course'],
        'battery_status': tracking_data['battery'],
        'acc_status': tracking_data['accstatus'],
        'door_status': tracking_data['doorstatus'],
        'defense_status': tracking_data['defencestatus']
    })
    
    vehicle.save()
    
    return tracking_data

def create_itrack_settings():
    """Create custom DocType for iTrack API settings"""
    if not frappe.db.exists('DocType', 'iTrack Settings'):
        doc = frappe.get_doc({
            'doctype': 'DocType',
            'name': 'iTrack Settings',
            'module': 'Fleet Management',
            'is_single': 1,
            'fields': [
                {
                    'fieldname': 'account',
                    'fieldtype': 'Data',
                    'label': 'iTrack Account',
                    'reqd': 1
                },
                {
                    'fieldname': 'password',
                    'fieldtype': 'Password',
                    'label': 'iTrack Password',
                    'reqd': 1
                }
            ]
        })
        doc.insert()

def update_vehicle_doctype():
    """Add custom fields to Vehicle DocType for iTrack integration"""
    vehicle_doc = frappe.get_doc('DocType', 'Vehicle')
    
    # Add fields if not already exists
    fields_to_add = [
        {
            'fieldname': 'imei',
            'fieldtype': 'Data',
            'label': 'IMEI Number',
            'unique': 1
        },
        {
            'fieldname': 'geofence_type',
            'fieldtype': 'Select',
            'label': 'Geofence Type',
            'options': '\n0: Out\n1: In\n2: In/Out'
        },
        {
            'fieldname': 'geofence_longitude',
            'fieldtype': 'Float',
            'label': 'Geofence Longitude'
        },
        {
            'fieldname': 'geofence_latitude',
            'fieldtype': 'Float',
            'label': 'Geofence Latitude'
        },
        {
            'fieldname': 'geofence_radius',
            'fieldtype': 'Int',
            'label': 'Geofence Radius (meters)'
        },
        {
            'fieldname': 'last_gps_time',
            'fieldtype': 'Datetime',
            'label': 'Last GPS Time'
        },
        {
            'fieldname': 'current_longitude',
            'fieldtype': 'Float',
            'label': 'Current Longitude'
        },
        {
            'fieldname': 'current_latitude',
            'fieldtype': 'Float',
            'label': 'Current Latitude'
        },
        {
            'fieldname': 'current_speed',
            'fieldtype': 'Int',
            'label': 'Current Speed (KM/H)'
        },
        {
            'fieldname': 'current_course',
            'fieldtype': 'Int',
            'label': 'Current Course'
        },
        {
            'fieldname': 'battery_status',
            'fieldtype': 'Int',
            'label': 'Battery Status'
        },
        {
            'fieldname': 'acc_status',
            'fieldtype': 'Select',
            'label': 'ACC Status',
            'options': '\n1: ON\n0: OFF\n-1: No Status'
        },
        {
            'fieldname': 'door_status',
            'fieldtype': 'Select',
            'label': 'Door Status',
            'options': '\n1: Open\n0: Closed\n-1: No Status'
        },
        {
            'fieldname': 'defense_status',
            'fieldtype': 'Select',
            'label': 'Defense Status',
            'options': '\n1: On\n0: Off\n-1: No Status'
        }
    ]
    
    for field in fields_to_add:
        if not any(existing_field.fieldname == field['fieldname'] for existing_field in vehicle_doc.fields):
            vehicle_doc.append('fields', field)
    
    vehicle_doc.save()

def install_itrack_integration():
    """Installation method for iTrack integration"""
    create_itrack_settings()
    update_vehicle_doctype()
