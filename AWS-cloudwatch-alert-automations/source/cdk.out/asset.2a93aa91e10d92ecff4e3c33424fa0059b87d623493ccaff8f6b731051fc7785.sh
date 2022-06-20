#!/bin/bash
yum install -y python3
curl -O https://bootstrap.pypa.io/get-pip.py
python3 get-pip.py --user
pip3 install boto3
pip3 install flask
pip3 install flask_socketio
pip3 install eventlet
pip3 install gevent
pip3 install gevent-websocket
yum install -y git
yum install -y httpd
systemctl start httpd
systemctl enable httpd
cd /home/ec2-user
git clone https://github.com/sharon-librae/Cloudwatch-Batch-Alarm.git
cd Cloudwatch-Batch-Alarm/
mv cloudwatch.html /var/www/html
chmod +x start.sh
python3 createAlarm.py