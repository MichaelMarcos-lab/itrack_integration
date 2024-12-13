from setuptools import setup, find_packages

with open("requirements.txt", "r") as f:
    requires = f.read().strip().split('\n')

setup(
    name="itrack_integration",
    version="0.0.1",
    description="iTrack API Integration for ERPNext",
    author="Your Name",
    author_email="your.email@example.com",
    packages=find_packages(),
    zip_safe=False,
    include_package_data=True,
    install_requires=requires
)
