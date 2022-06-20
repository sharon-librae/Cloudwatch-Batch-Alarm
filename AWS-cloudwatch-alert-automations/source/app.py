#!/usr/bin/env python3


from batch_monitor.batch_monitor_stack import BatchMonitorStack
from aws_cdk import core

app = core.App()

BatchMonitorStack(app, "BatchMonitor")

app.synth()
