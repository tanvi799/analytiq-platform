"""
AnalytIQ — AWS CDK Infrastructure Stack
Provisions: S3 (data lake) + Kinesis Data Stream + Redshift Serverless
"""

import aws_cdk as cdk
from aws_cdk import (
    Stack,
    aws_s3 as s3,
    aws_kinesis as kinesis,
    aws_glue as glue,
    aws_iam as iam,
    aws_redshiftserverless as redshift,
    RemovalPolicy,
    Duration,
)
from constructs import Construct


class AnalytIQStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs):
        super().__init__(scope, construct_id, **kwargs)

        # ── 1. S3 Data Lake ──────────────────────────────────────────────────
        # Raw events land here from Kinesis consumer
        self.raw_bucket = s3.Bucket(
            self,
            "RawEventsBucket",
            bucket_name=f"analytiq-raw-events-{self.account}",
            versioned=False,
            removal_policy=RemovalPolicy.DESTROY,       # safe for dev
            auto_delete_objects=True,                   # clean teardown
            lifecycle_rules=[
                s3.LifecycleRule(
                    id="MoveToIA",
                    transitions=[
                        s3.Transition(
                            storage_class=s3.StorageClass.INFREQUENT_ACCESS,
                            transition_after=Duration.days(30),
                        )
                    ],
                )
            ],
        )

        # Processed/transformed data lands here after Glue ETL
        self.processed_bucket = s3.Bucket(
            self,
            "ProcessedEventsBucket",
            bucket_name=f"analytiq-processed-{self.account}",
            removal_policy=RemovalPolicy.DESTROY,
            auto_delete_objects=True,
        )

        # ── 2. Kinesis Data Stream ────────────────────────────────────────────
        # Real-time event ingestion — 1 shard handles ~1MB/s (plenty for dev)
        self.stream = kinesis.Stream(
            self,
            "EventStream",
            stream_name="analytiq-events",
            shard_count=1,
            retention_period=Duration.hours(24),    # free tier: 24h retention
        )

        # ── 3. IAM Role for Glue ETL jobs ────────────────────────────────────
        self.glue_role = iam.Role(
            self,
            "GlueRole",
            assumed_by=iam.ServicePrincipal("glue.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name(
                    "service-role/AWSGlueServiceRole"
                )
            ],
        )
        self.raw_bucket.grant_read(self.glue_role)
        self.processed_bucket.grant_read_write(self.glue_role)

        # ── 4. Glue Database (catalogue for raw S3 data) ─────────────────────
        self.glue_db = glue.CfnDatabase(
            self,
            "GlueDatabase",
            catalog_id=self.account,
            database_input=glue.CfnDatabase.DatabaseInputProperty(
                name="analytiq_raw",
                description="Raw events catalogued from S3",
            ),
        )

        # ── 5. Redshift Serverless ────────────────────────────────────────────
        # Serverless = no cluster to manage, pay per query — perfect for students
        self.redshift_namespace = redshift.CfnNamespace(
            self,
            "RedshiftNamespace",
            namespace_name="analytiq-ns",
            admin_username="analytiq_admin",
            admin_user_password="ChangeMe123!",     # ⚠ change before sharing
            db_name="analytiq",
        )

        self.redshift_workgroup = redshift.CfnWorkgroup(
            self,
            "RedshiftWorkgroup",
            workgroup_name="analytiq-wg",
            namespace_name="analytiq-ns",
            base_capacity=8,    # minimum RPUs — lowest cost
            publicly_accessible=False,
        )
        self.redshift_workgroup.add_dependency(self.redshift_namespace)

        # ── 6. IAM Role for FastAPI / Lambda to read Redshift ─────────────────
        self.api_role = iam.Role(
            self,
            "APIRole",
            assumed_by=iam.ServicePrincipal("lambda.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name(
                    "AmazonRedshiftDataFullAccess"
                )
            ],
        )
        self.stream.grant_read(self.api_role)

        # ── 7. Stack Outputs (printed after cdk deploy) ───────────────────────
        cdk.CfnOutput(self, "OutputRawBucket", value=self.raw_bucket.bucket_name)
        cdk.CfnOutput(self, "OutputProcessedBucket", value=self.processed_bucket.bucket_name)
        cdk.CfnOutput(self, "OutputKinesisStream", value=self.stream.stream_name)
        cdk.CfnOutput(self, "OutputRedshiftWorkgroup", value="analytiq-wg")
        cdk.CfnOutput(self, "OutputRedshiftDatabase", value="analytiq")
