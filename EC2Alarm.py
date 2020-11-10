import boto3
import json

def ec2_alarm(metriclist, statistic, period, comparisonoperator, threshold, datapointstoalarm, treatmissingdata, evaluationperiods,
              alarmnameprefix, description, snstopic, ec2actions, grouptype, groupvalue, region, notifications, ec2alarm,
              my_config):
    ec2list = ec2_list(grouptype, groupvalue, my_config)
    # create alarms
    clientcw = boto3.client('cloudwatch', config=my_config)

    success_instance = []
    error_instance = []


    period = period_transform(period)
    alarmactions = alarm_action(notifications,snstopic,ec2alarm,region,ec2actions)
    okactions = ok_action(notifications,snstopic,ec2alarm,region,ec2actions)
    insufficientdataactions = insufficient_action(notifications,snstopic,ec2alarm,region,ec2actions)
    actionsenabled = action_enable(notifications,ec2alarm)



    try:
        for metric in metriclist:
            for ec2 in ec2list:

                if grouptype == 'Resource group':
                    instanceid = ec2['ResourceArn'].split('/')[1]

                    response = Create_Alarm(metric, instanceid, statistic, period, comparisonoperator, threshold,
                                            datapointstoalarm,
                                            treatmissingdata, evaluationperiods, clientcw, alarmnameprefix,
                                            actionsenabled, description,
                                            alarmactions, okactions, insufficientdataactions)

                    if response['ResponseMetadata']['HTTPStatusCode'] == 200:
                        success_instance.append(instanceid)
                    else:
                        error_instance.append(instanceid)

                elif grouptype == 'AutoScaling group':
                    instanceid = ec2['InstanceId']
                    response = Create_Alarm(metric, instanceid, statistic, period, comparisonoperator, threshold,
                                            datapointstoalarm,
                                            treatmissingdata, evaluationperiods, clientcw, alarmnameprefix,
                                            actionsenabled, description,
                                            alarmactions, okactions, insufficientdataactions)

                    if response['ResponseMetadata']['HTTPStatusCode'] == 200:
                        success_instance.append(instanceid)
                    else:
                        error_instance.append(instanceid)

                else:
                    instances = ec2['Instances']
                    for instance in instances:
                        instanceid = instance['InstanceId']

                        response = Create_Alarm(metric, instanceid, statistic, period, comparisonoperator, threshold, datapointstoalarm,
                                      treatmissingdata, evaluationperiods, clientcw, alarmnameprefix, actionsenabled, description,
                                      alarmactions,okactions,insufficientdataactions)

                        if response['ResponseMetadata']['HTTPStatusCode'] == 200:
                            success_instance.append(instanceid)
                        else:
                            error_instance.append(instanceid)

        result = {'Success': success_instance, 'Error': error_instance}
        return json.dumps(result)
    except Exception as e:
        return json.dumps(str(e))


# create alarm
def Create_Alarm(metricname, instanceid, statistic, period, comparisonoperator, threshold, datapointstoalarm,
                          treatmissingdata, evaluationperiods, clientcw, alarmnameprefix, actionsenabled, description,
                          alarmactions, okactions,insufficientdataactions):
    response_cw = clientcw.put_metric_alarm(
        AlarmName=alarmnameprefix + instanceid + metricname,
        ComparisonOperator=comparisonoperator,
        EvaluationPeriods=evaluationperiods,
        MetricName=metricname,
        Namespace='AWS/EC2',
        Period=period,
        DatapointsToAlarm=datapointstoalarm,
        TreatMissingData=treatmissingdata,
        Statistic=statistic,
        Threshold=threshold,
        ActionsEnabled=actionsenabled,
        OKActions=okactions,
        AlarmActions=alarmactions,
        InsufficientDataActions=insufficientdataactions,
        AlarmDescription=description,
        Dimensions=[
            {
                'Name': 'InstanceId',
                'Value': instanceid
            },
        ],
    )
    return response_cw


#transform period to int
def period_transform(period):
    if period == '10 seconds':
        period = 10
    elif period == '30 seconds':
        period = 30
    elif period == '1 minute':
        period = 60
    elif period == '5 minutes':
        period = 300
    elif period == '15 minutes':
        period = 900
    elif period == '1 hour':
        period = 3600
    elif period == '6 hour':
        period = 21600
    else:
        period = 86400
    return period

#build alarm actions list
def alarm_action(notifications,snstopic,ec2alarm,region,ec2action):
    alarmactions = []
    if notifications == 'In alarm':
        alarmactions.append(snstopic)
    if ec2alarm == 'In alarm':
        alarmactions.append('arn:aws:automate:' + region + ':ec2:'+ec2action)
    return alarmactions


#build ok actions list
def ok_action(notifications,snstopic,ec2alarm,region,ec2action):
    okactions = []
    if notifications == 'OK':
        okactions.append(snstopic)
    if ec2alarm == 'OK':
        okactions.append('arn:aws:automate:' + region + ':ec2:' + ec2action)
    return okactions


#build insufficient actions list
def insufficient_action(notifications,snstopic,ec2alarm,region,ec2action):
    insufficientdataactions = []
    if notifications == 'Insufficient data':
        insufficientdataactions.append(snstopic)
    if ec2alarm == 'Insufficient data':
        insufficientdataactions.append('arn:aws:automate:' + region + ':ec2:' + ec2action)
    return insufficientdataactions


#build ec2 list based on condition
def ec2_list(grouptype, groupvalue,my_config):
    if grouptype == 'AutoScaling group':
        autoscaling_client = boto3.client('autoscaling', config=my_config)
        autoscaling_response = autoscaling_client.describe_auto_scaling_groups(
            AutoScalingGroupNames=[
                groupvalue,
            ],
        )
        ec2list = autoscaling_response['AutoScalingGroups'][0]['Instances']
        print(ec2list)
    elif grouptype == 'Resource group':
        clientrg = boto3.client('resource-groups', config=my_config)
        clientrg_response = clientrg.list_group_resources(
            GroupName=groupvalue,
            Filters=[
                {
                    'Name': 'resource-type',
                    'Values': [
                        'AWS::EC2::Instance',
                    ]
                },
            ],
        )
        ec2list = clientrg_response['ResourceIdentifiers']
    elif grouptype == 'Tag':
        clientec2 = boto3.client('ec2', config=my_config)
        response_tag = clientec2.describe_instances(
            Filters=[
                {
                    'Name': "tag:" + groupvalue.split(":")[0],
                    'Values': [
                        groupvalue.split(":")[1],
                    ]
                },
            ],
        )
        ec2list = response_tag['Reservations']
    elif grouptype == 'AMI':
        client_ami = boto3.client('ec2', config=my_config)
        response_ami = client_ami.describe_instances(
            Filters=[
                {
                    'Name': "image-id",
                    'Values': [
                        groupvalue,
                    ]
                },
            ],
        )
        ec2list = response_ami['Reservations']
    else:
        client_all = boto3.client('ec2', config=my_config)
        response_all = client_all.describe_instances()
        ec2list = response_all['Reservations']

    return ec2list


# Actionsenable parameter
def action_enable(notifications,ec2alarm):
    if notifications != 'None' or ec2alarm != 'None':
        actionsenabled = True
    else:
        actionsenabled = False
    return actionsenabled
