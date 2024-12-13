import frappe

def get_tracking_dashboard_data(data):
    """Customize Vehicle list view with tracking information"""
    for vehicle in data:
        if vehicle.imei:
            try:
                # Attempt to get latest tracking data
                from .itrack_integration import ITrackAPIIntegration
                integration = ITrackAPIIntegration()
                tracking_data = integration.track_vehicle(vehicle.imei)
                
                # Add tracking status to vehicle
                vehicle.tracking_status = {
                    'last_update': tracking_data.get('servertime'),
                    'speed': tracking_data.get('speed', 0),
                    'location': f"{tracking_data.get('latitude')}, {tracking_data.get('longitude')}"
                }
            except Exception as e:
                vehicle.tracking_status = {'error': str(e)}
    return data

@frappe.whitelist()
def bulk_vehicle_sync():
    """Sync tracking data for all vehicles with IMEI"""
    from .itrack_integration import sync_vehicle_tracking
    
    vehicles = frappe.get_all('Vehicle', filters={'imei': ['!=', '']}, fields=['name', 'imei'])
    
    results = []
    for vehicle in vehicles:
        try:
            sync_result = sync_vehicle_tracking(vehicle.name)
            results.append({
                'vehicle': vehicle.name,
                'status': 'Success',
                'details': sync_result
            })
        except Exception as e:
            results.append({
                'vehicle': vehicle.name,
                'status': 'Failed',
                'error': str(e)
            })
    
    return results
