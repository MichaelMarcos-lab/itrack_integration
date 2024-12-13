from . import __version__ as app_version

app_name = "itrack_integration"
app_title = "iTrack Integration"
app_publisher = "Your Company Name"
app_description = "Integration between iTrack API and ERPNext"
app_email = "your.email@example.com"
app_license = "MIT"

# Include Python modules that need to be imported on boot
app_include_js = []
app_include_css = []

# Include install method
def install():
    """Run during app installation"""
    from .itrack_integration import install_itrack_integration
    install_itrack_integration()
