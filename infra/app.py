#!/usr/bin/env python3
"""AnalytIQ CDK App entrypoint"""

import aws_cdk as cdk
from analytiq_stack import AnalytIQStack

app = cdk.App()

AnalytIQStack(
    app,
    "AnalytIQStack",
    env=cdk.Environment(
        account=app.node.try_get_context("account"),
        region=app.node.try_get_context("region") or "ap-southeast-2",  # Sydney
    ),
)

app.synth()
