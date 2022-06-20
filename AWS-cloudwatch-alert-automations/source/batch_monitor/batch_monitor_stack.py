from aws_cdk import (
    aws_ec2 as ec2,
    aws_iam as iam,
    core
)


class BatchMonitorStack(core.Stack):

    def __init__(self, scope: core.Construct, id: str, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)

        # The code that defines your stack goes here
        # VPC
        vpc = ec2.Vpc(self, "BatchMonitor VPC",
                      cidr='10.0.0.0/28',
                      nat_gateways=0,
                      max_azs=1,
                      subnet_configuration=[ec2.SubnetConfiguration(name="public", subnet_type=ec2.SubnetType.PUBLIC)]
                      )

        # AMI
        amzn_linux = ec2.MachineImage.latest_amazon_linux(
            generation=ec2.AmazonLinuxGeneration.AMAZON_LINUX_2,
            edition=ec2.AmazonLinuxEdition.STANDARD,
            virtualization=ec2.AmazonLinuxVirt.HVM,
            storage=ec2.AmazonLinuxStorage.GENERAL_PURPOSE
        )

        # Instance Role
        role = iam.Role(self, "BatchMonitor", assumed_by=iam.ServicePrincipal("ec2.amazonaws.com"))

        role.add_managed_policy(
            iam.ManagedPolicy.from_aws_managed_policy_name("AutoScalingReadOnlyAccess"))
        role.add_managed_policy(
            iam.ManagedPolicy.from_aws_managed_policy_name("AmazonEC2ReadOnlyAccess"))
        role.add_managed_policy(
            iam.ManagedPolicy.from_aws_managed_policy_name("CloudWatchFullAccess"))
        role.add_managed_policy(
            iam.ManagedPolicy.from_aws_managed_policy_name("AWSResourceGroupsReadOnlyAccess"))

        # parameters
        instancetype = core.CfnParameter(self, "instance type", type="String", description="the type of instance")
        keyname = core.CfnParameter(self, "key name", type="String", description="SSH key pair Name for accessing EC2")
        visitip = core.CfnParameter(self, "visit ip", type="String", description="the ip connect to server, format: x.x.x.x/x")

        # Security Group
        securitygroup = ec2.SecurityGroup(self, id="SGForBatchMonitor", vpc=vpc,
                                          description="Security group for Batch monitoring")

        securitygroup.add_ingress_rule(ec2.Peer.ipv4(visitip.value_as_string), ec2.Port.tcp(22), "SSH from ip")
        securitygroup.add_ingress_rule(ec2.Peer.ipv4(visitip.value_as_string), ec2.Port.tcp(80),
                                       "HTTP connection from ip")
        securitygroup.add_ingress_rule(ec2.Peer.ipv4(visitip.value_as_string), ec2.Port.tcp(5000), "Server port")

        # Instance
        instance = ec2.Instance(self, "Instance",
                                instance_type=ec2.InstanceType(instancetype.value_as_string),
                                machine_image=amzn_linux,
                                vpc=vpc,
                                role=role,
                                key_name=keyname.value_as_string,
                                security_group=securitygroup,
                                vpc_subnets=vpc.select_subnets(subnet_type=ec2.SubnetType.PUBLIC).subnets[0]
                                )

        instance.add_user_data("yum install -y python3\n"
                               "curl -O https://bootstrap.pypa.io/get-pip.py\n"
                               "python3 get-pip.py --user\n"
                               "pip3 install boto3\n"
                               "pip3 install flask\n"
                               "pip3 install flask_socketio\n"
                               "pip3 install eventlet\n"
                               "pip3 install gevent\n"
                               "pip3 install gevent-websocket\n"
                               "yum install -y git\n"
                               "yum install -y httpd\n"
                               "systemctl start httpd\n"
                               "systemctl enable httpd\n"
                               "cd /home/ec2-user\n"
                               "git clone https://github.com/sharon-librae/Cloudwatch-Batch-Alarm.git\n"
                               "cd Cloudwatch-Batch-Alarm/\n"
                               "mv cloudwatch.html /var/www/html\n"
                               "chmod +x start.sh\n"
                               "python3 createAlarm.py\n")

        instanceip = instance.instance_public_ip

        core.CfnOutput(self, id="connection ip", value=instanceip + "/cloudwatch.html")
