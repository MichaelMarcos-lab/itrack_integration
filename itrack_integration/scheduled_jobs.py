import frappe

def scheduled_vehicle_sync():
    """
    Scheduled job to sync all vehicles with iTrack
    Run every hour
    """
    from .itrack_integration import sync_vehicle_tracking
    
    vehicles = frappe.get_all('Vehicle', filters={'imei': ['!=', '']}, fields=['name', 'imei'])
    
    for vehicle in vehicles:
        try:
            sync_vehicle_tracking(vehicle.name)
            frappe.db.commit()
        except Exception as e:
            frappe.log_error(f"Vehicle Sync Failed for {vehicle.name}: {str(e)}")
