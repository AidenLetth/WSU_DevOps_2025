from aws_cdk import (
    Stack,
    Duration,
    aws_lambda as _lambda,
    aws_apigateway as apigw,
    aws_dynamodb as ddb,
    aws_iam as iam,
    aws_sns as sns,
    aws_lambda_event_sources as event_sources,
    RemovalPolicy,
)
from constructs import Construct

class Project2Stack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # The code that defines your stack goes here

        # example resource
        # queue = sqs.Queue(
        #     self, "Project2Queue",
        #     visibility_timeout=Duration.seconds(300),
        # )
        alarm_topic = sns.Topic(
            self, "WebCrawlerAlarmTopic",
            display_name="WebCrawler Alarm Topic"
        )
        table = ddb.Table(
            self, "WebCrawlerTargets",
            partition_key=ddb.Attribute(name="url_id", type=ddb.AttributeType.STRING),
            table_name="WebCrawlerTargets",
            removal_policy=RemovalPolicy.DESTROY,
            billing_mode=ddb.BillingMode.PAY_PER_REQUEST,
            stream=ddb.StreamViewType.NEW_AND_OLD_IMAGES
        )

        lambda_env = {"TABLE_NAME": table.table_name}

        # CRUD Lambdas
        create_fn = _lambda.Function(
            self, "CreateTargetFn",
            runtime=_lambda.Runtime.PYTHON_3_11,
            handler="create_target.handler",
            code=_lambda.Code.from_asset("lambda"),
            timeout=Duration.seconds(10),
            environment=lambda_env
        )

        read_fn = _lambda.Function(
            self, "ReadTargetFn",
            runtime=_lambda.Runtime.PYTHON_3_11,
            handler="read_target.handler",
            code=_lambda.Code.from_asset("lambda"),
            timeout=Duration.seconds(10),
            environment=lambda_env
        )

        update_fn = _lambda.Function(
            self, "UpdateTargetFn",
            runtime=_lambda.Runtime.PYTHON_3_11,
            handler="update_target.handler",
            code=_lambda.Code.from_asset("lambda"),
            timeout=Duration.seconds(10),
            environment=lambda_env
        )

        delete_fn = _lambda.Function(
            self, "DeleteTargetFn",
            runtime=_lambda.Runtime.PYTHON_3_11,
            handler="delete_target.handler",
            code=_lambda.Code.from_asset("lambda"),
            timeout=Duration.seconds(10),
            environment=lambda_env
        )

        for fn in [create_fn, read_fn, update_fn, delete_fn]:
            table.grant_read_write_data(fn)
            monitor_env = {
            "TABLE_NAME": table.table_name,
            "SNS_TOPIC_ARN": alarm_topic.topic_arn,
            "DASHBOARD_NAME": "WebHealthDashboard",
            "METRIC_NAMESPACE": "Hungle",
            "AVAILABILITY_METRIC": "Availability",
            "LATENCY_METRIC": "Latency"
        }

        monitor_fn = _lambda.Function(
            self, "MonitorManagerFn",
            runtime=_lambda.Runtime.PYTHON_3_11,
            handler="monitor_manager.handler",
            code=_lambda.Code.from_asset("lambda"),
            timeout=Duration.seconds(30),
            environment=monitor_env
        )
        table.grant_read_data(monitor_fn)
        monitor_fn.add_to_role_policy(iam.PolicyStatement(
            actions=[
                "cloudwatch:PutMetricAlarm",
                "cloudwatch:DeleteAlarms",
                "cloudwatch:PutDashboard",
                "cloudwatch:DescribeAlarms"
            ],
            resources=["*"]
        ))
        alarm_topic.grant_publish(monitor_fn)
        event_source = event_sources.DynamoEventSource(
            table,
            starting_position=_lambda.StartingPosition.TRIM_HORIZON,
            batch_size=5,
            bisect_batch_on_error=True,
            retry_attempts=2
        )
        monitor_fn.add_event_source(event_source)
         # API Gateway
        api = apigw.RestApi(
            self,
            "WebCrawlerApi",
            rest_api_name="WebCrawler CRUD API",
            description="CRUD API for managing crawler targets."
        )

        targets = api.root.add_resource("targets")
        targets.add_method("POST", apigw.LambdaIntegration(create_fn))
        targets.add_method("GET", apigw.LambdaIntegration(read_fn))
        targets.add_method("PUT", apigw.LambdaIntegration(update_fn))
        targets.add_method("DELETE", apigw.LambdaIntegration(delete_fn))

        self.api_endpoint = api.url


