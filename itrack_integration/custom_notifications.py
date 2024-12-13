import frappe

def send_tracking_alerts():
    """
    Send alerts for vehicles with potential issues
    - Low battery
    - Prolonged stationary status
    - Geofence violations
    """
    vehicles = frappe.get_all('Vehicle', 
        filters={'imei': ['!=', '']}, 
        fields=['name', 'imei', 'battery_status', 'current_longitude', 'current_latitude']
    )
    
    for vehicle in vehicles:
        # Battery low alert
        if vehicle.battery_status < 20:
            frappe.sendmail(
                recipients=frappe.get_list('User', filters={'role': 'Fleet Manager'}),
                subject=f"Low Battery Alert: {vehicle.name}",
                message=f"Vehicle {vehicle.name} has low battery ({vehicle.battery_status}%)"
            )
        
