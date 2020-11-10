# For using this python, you fist need to install aws cli and aws configure
# Then you need to modify groupname
# Also you can modify alarm put_metric_alarm according to your need
# If you want to create resource group for CloudFront, the region must be us-east-1

import boto3
from botocore.config import Config
from flask import Flask
from flask_socketio import SocketIO, emit
import json
import EC2Alarm

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins = '*')


@app.route('/')

def app_run(msg):
    Service = msg['service']
    metriclist = msg['metrics']
    statistic = msg['statistic']
    period = msg['period']
    comparisonoperator = msg['comparisonoperator']
    threshold = msg['threshold']
    datapointstoalarm = msg['datapointstoalarm']
    treatmissingdata = msg['treatmissingdata']
    evaluationperiods = msg['evaluationperiods']
    alarmnameprefix = msg['alarmnameprefix']
    description = msg['description']
    snstopic = msg['snstopic']
    ec2actions = msg['ec2action']
    grouptype = msg['grouptype']
    groupvalue = msg['groupvalue']
    region = msg['region']
    notifications = msg['notification']
    ec2alarm = msg['ec2alarm']

    my_config = Config(
        region_name=region
    )

    if Service == 'EC2':
        response = EC2Alarm.ec2_alarm(metriclist, statistic, period, comparisonoperator, threshold, datapointstoalarm, treatmissingdata,
                           evaluationperiods,alarmnameprefix, description, snstopic, ec2actions, grouptype, groupvalue,
                           region, notifications, ec2alarm, my_config)

        print(response)
    else:
        response = 'null'

    return response


@socketio.on('connect')
def socketio_connect():
    print('Client has connected to the backend')
    emit('event', {'message': 'ACK'})


@socketio.on('process')
def socketio_message_event(message):
    print('Received event: ' + str(message))
    response = app_run(json.loads(message))
    emit('response', {'message': response})


if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', debug=True, port=5000)
