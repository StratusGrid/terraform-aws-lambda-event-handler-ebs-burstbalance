# To Do #
# add try catch to volume query (and general error handling?)
# abstract function code from terraform module and variablize pattern somehow?
# add an instantiation check for new containers that checks all instances and updates the settings?


# Import libraries
import boto3
import re
import os

# Initialize boto3 clients (since this is outside of the handler function, it will only be done once per container)
cloudwatch = boto3.client('cloudwatch')
ec2 = boto3.resource('ec2')

# Entry point for lambda
def handler(event, context):

  # Volume creation event
  if event['detail']['result'] == 'available':
    for resource in event['resources']:
      match = re.match(r'.*(vol-.*)$', resource)
      if match:
        volume = ec2.Volume(match.group(1))
        if volume.volume_type == 'gp2':
          print('Creating alarm for volume: ', match.group(1))
          response = cloudwatch.put_metric_alarm(
            AlarmName='{0}-BurstBalance'.format(match.group(1)),
            AlarmActions=[
              os.environ['sns_alarm_target']
            ],
            ComparisonOperator='LessThanThreshold',
            EvaluationPeriods=1,
            MetricName='BurstBalance',
            Namespace='AWS/EBS',
            Period=int(os.environ['alarm_period']),
            Statistic='Average',
            Threshold=float(os.environ['alarm_threshold']),
            ActionsEnabled=True,
            AlarmDescription='Alarm when EBS Burst Balance below 50%',
            Dimensions=[
              {
                'Name': 'VolumeId',
                'Value': match.group(1)
              },
            ],
          )
          if response['ResponseMetadata']['HTTPStatusCode'] == 200:
            print('Successfully created BurstBalance Alarm for volume: ', match.group(1))
          else:
            print(response)

  # Volume deletion event
  if event['detail']['result'] == 'deleted':
    for resource in event['resources']:
      match = re.match(r'.*(vol-.*)$', resource)
      if match:
        volume =  ec2.Volume(match.group(1))
        if volume.volume_type == 'gp2':
          print('Deleting alarm for volume: ', match.group(1))
          response = cloudwatch.delete_alarms(
            AlarmNames=[
                '{0}-BurstBalance'.format(match.group(1))
            ]
          )
          if response['ResponseMetadata']['HTTPStatusCode'] == 200:
            print('Successfully deleted BurstBalance Alarm for volume: ', match.group(1))
          else:
            print(response)
