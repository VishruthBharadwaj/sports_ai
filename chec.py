import boto3

# Create a new session with AWS
session = boto3.session.Session()

# Get the list of available AWS regions
available_regions = session.get_available_regions("s3")

print(available_regions)