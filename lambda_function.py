import json
import boto3
import datetime

# Defines the region to which the metrics are going to be exported
METRICS_REGION = 'sa-east-1'

# Defines which regions are going to be verified
REGIONS = ['us-east-1', 'sa-east-1']

# Uncomment line 13 if all regions are needed
# (Don't forget to change Lambda's timeout to at least 30 seconds if so)
#REGIONS = [region['RegionName'] for region in ec2.describe_regions()['Regions']]

ec2 = boto3.client('ec2')
cloudwatch = boto3.client('cloudwatch', region_name=METRICS_REGION)
total_volumes = 0
ebs_tags = []

def lambda_handler(event, context):
    # Change the value to False if checking for EBS Volumes without tags isn't needed
    debug_tags = False
    for r in REGIONS:
        print("[INFO] Starting verification on region:", r)
        try:
            ec2Region = boto3.client('ec2', region_name=r)
            volumes = ec2Region.describe_volumes()
            check_ebs(volumes, ec2Region)
            search_null(debug_tags, ebs_tags)
        except Exception as e:
            print("[ERROR]", e)
        print("[INFO] Verification Ended.")
    return send_metrics(total_volumes, total_eips)

def check_ebs(volumes, ec2Region):
    global total_volumes
    global ebs_tags
    for volume in volumes['Volumes']:
        volumeId = volume['VolumeId']
        if volume['State'] == 'available' and 'Tags' not in volume:
            ebs_tags.append("[WARN] Found EBS Volume without Tags: "+str(volumeId))
        elif volume['State'] == 'available':
            print("[ALERT] Found Available EBS volume:", volumeId)
            total_volumes += 1

def send_metrics():
    global total_volumes
    try:
        cloudwatch.put_metric_data(
                Namespace='LambdaMonitoring',
                MetricData=[
                    {
                        'Dimensions': [
                            {
                                'Name': 'Service',
                                'Value': 'EC2'
                            },
                        ],
                        'MetricName': 'VolumesAvailable',
                        'Value': total_volumes,
                        'Unit': 'Count'
                    }
                ]
        )
        print("[EBS] |"+str(total_volumes+"| available volumes were found")
    except Exception as e:
        print("[ERROR] When sending metrics to CloudWatch:", e)

def search_null(debug_tags, ebs_tags):
    if debug_tags == True:
        for v in ebs_tags:
            print(v)
        print('\n')
        print("[EBS] Found |"+str(len(ebs_tags))+"| volumes without tags")
