from aws_cdk import (
    Stack,
    Duration,
    RemovalPolicy,
    aws_lambda as _lambda,
    aws_events as events,
    aws_events_targets as targets,
    aws_cloudwatch as cloudwatch,
    aws_iam as iam,
    aws_sns as sns,
    aws_sns_subscriptions as subscriptions,
    aws_dynamodb as dynamodb,
    aws_cloudwatch_actions as cw_actions,
)
from constructs import Construct


URL_MONITORITY_AVAILABILITY= "Availability"
URL_MONITORITY_LATENCY = "Latency"
URL_NAMESPACE = "Hungle"
URLS = ['https://www.google.com','https://www.youtube.com','https://www.facebook.com']
class AidenStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs):
        super().__init__(scope, construct_id, **kwargs)
       
        #LAMBDA FUNCTION
        fn = _lambda.Function(
            self, "Hungle",
            runtime=_lambda.Runtime.PYTHON_3_11,
            handler="publish_metric.handler",
            code=_lambda.Code.from_asset("lambda"),
            timeout=Duration.seconds(30),
            environment={"WEBSITES": ",".join(URLS)}  
        )

        # IAM policy for lambda 
        # https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_iam/PolicyStatement.html
        fn.add_to_role_policy(
            iam.PolicyStatement(
                actions=["cloudwatch:PutMetricData"],
                resources=["*"]
            )
        )
       
        schedule=events.Schedule.rate(Duration.minutes(5))
        # make the rule to trigger the Lambda function every 5 minutes
        rule = events.Rule(
            self, "HungleScheduleRule",
            schedule = schedule
        )
        rule.apply_removal_policy(RemovalPolicy.DESTROY)
        rule.add_target(targets.LambdaFunction(fn))

# dashboard https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_cloudwatch/Dashboard.html
        
        dashboard = cloudwatch.Dashboard(self, "Project1Dashboard")
        cloudwatch.GraphWidget(
                title="Website Availability",
                left=[
                    cloudwatch.Metric(namespace="Hungle",
                                      metric_name="Availability", 
                                      statistic="Average")
                ]
                )
        cloudwatch.GraphWidget(
                title="Website Latency",
                left=[
                    cloudwatch.Metric(namespace="Hungle", 
                                      metric_name="Latency", 
                                      statistic="Average")
                ]
                )
        



#DynamoDb https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_dynamodb/Table.html
        table = dynamodb.Table(
    self, "WebHealthAlarmtable",
    partition_key=dynamodb.Attribute(name="Website", type=dynamodb.AttributeType.STRING),
     sort_key=dynamodb.Attribute(name="Timestamp", type=dynamodb.AttributeType.STRING)
)
        table.apply_removal_policy(RemovalPolicy.DESTROY)
#log alarms
        log_alarm_fn = _lambda.Function(
    self, "LogAlarmFunction",
    runtime=_lambda.Runtime.PYTHON_3_11,
    handler="log_alarm.lambda_handler",
    code=_lambda.Code.from_asset("lambda"),
    timeout=Duration.seconds(30),
    environment={
        "TABLE_NAME": table.table_name
    }
)
        log_alarm_fn.apply_removal_policy(RemovalPolicy.DESTROY)
        log_alarm_fn.add_to_role_policy(iam.PolicyStatement(
        actions=[
            "dynamodb:PutItem",
            "dynamodb:UpdateItem",
            "dynamodb:GetItem",
            "dynamodb:Scan",
            "dynamodb:Query"
        ],
        resources=[table.table_arn]
    )
)
  
        table.grant_read_write_data(log_alarm_fn)
        
        for url in URLS:
            availability_metric = cloudwatch.Metric(
                namespace="Hungle",
                metric_name="Availability",
                statistic="Average",
                dimensions_map={"Website": url} 
                   )
            latency_metric = cloudwatch.Metric(
                namespace="Hungle",
                metric_name="Latency",
                statistic="Average",
                dimensions_map={"Website": url} 
        )
            dashboard.add_widgets(
            cloudwatch.GraphWidget(
                title=f"Website Availability and Latency for {url} ",
                left=[availability_metric,latency_metric],
                legend_position=cloudwatch.LegendPosition.RIGHT, 
                period=Duration.minutes(1),  
                left_y_axis=cloudwatch.YAxisProps(min=0),
                )
            )
 # metrics 
        # alarm https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_cloudwatch/Alarm.html 
            availability_alarm = cloudwatch.Alarm(
                self, f"AvailabilityAlarm-{url.replace('https://','').replace('.','-')}",
                metric=availability_metric,
                threshold=0,
                evaluation_periods=1,
                comparison_operator=cloudwatch.ComparisonOperator.LESS_THAN_OR_EQUAL_TO_THRESHOLD
        )
            latency_alarm= cloudwatch.Alarm(
                self, f"LatencyAlarm-{url.replace('https://','').replace('.','-')}",
                metric=latency_metric,
                threshold=0.31,
                datapoints_to_alarm=1,
                evaluation_periods=1,
                comparison_operator=cloudwatch.ComparisonOperator.GREATER_THAN_OR_EQUAL_TO_THRESHOLD
        )
            
#sns topic https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_sns/Topic.html
        for i, url in enumerate(URLS):
         topic = sns.Topic(
        self,
        f"AvailabilityAlarm-{i}-{url.replace('https://','').replace('.','-')}",
        display_name=f"Alarm for) {URLS} " 
    )
# give permission for sns to invoke lambda https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_lambda/Function.html#aws_cdk.aws_lambda.Function.add_permission
        log_alarm_fn.add_permission(
    "AllowSNSInvoke",
    principal=iam.ServicePrincipal("sns.amazonaws.com"),
    action="lambda:InvokeFunction",
    source_arn=topic.topic_arn
)
        topic.add_subscription(subscriptions.LambdaSubscription(log_alarm_fn))
        topic.add_subscription(subscriptions.EmailSubscription("22112326@student.westernsydney.edu.au"))


        availability_alarm.add_alarm_action(cw_actions.SnsAction(topic))
        latency_alarm.add_alarm_action(cw_actions.SnsAction(topic))

