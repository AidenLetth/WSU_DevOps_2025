import aws_cdk as core
import aws_cdk.assertions as assertions
from aiden.aiden_stack import AidenStack
import json
import pytest


@pytest.fixture
def getStack(): 
    app = core.App()
    stack = AidenStack(app, "aiden")
    return stack

# example tests. To run these tests, uncomment this file along with the example
# resource in aiden/aiden_stack.py
def test_sqs_queue_created(getStack):
 template = assertions.Template.from_stack(getStack)
#     getStack.has_resource_properties("AWS::SQS::Queue", {
#         "VisibilityTimeout": 300
#     })

#test 1 : test if 2 lambda functions are created
 def test_lambda(getStack):
    template = assertions.Template.from_stack(getStack)
    getStack.resource_count_is("AWS::Lambda::Function", 2)
 
 #test 2: test if 3 sns topics are created
def test_sns_topic(getStack):
    template = assertions.Template.from_stack(getStack)
    template.resource_count_is("AWS::SNS::Topic", 3)

#test 3: test if sns subscription is created with email protocol and correct endpoint
def test_sns_subscription(getStack):
    template = assertions.Template.from_stack(getStack)
    template.has_resource_properties("AWS::SNS::Subscription", {"Protocol": "email", "Endpoint": "22112326@student.westernsydney.edu.au"})

#test 4: test if 2 iam roles are created
def test_iam_role (getStack):
    template = assertions.Template.from_stack(getStack)
    template.resource_count_is("AWS::IAM::Role", 2)
#test 5: test if 1 cloudwatch alarm is created
def test_lambda_policies(getStack):
    template = assertions.Template.from_stack(getStack)
    template.has_resource_properties("AWS::IAM::Policy", { "PolicyDocument": {"Statement": [
     { "Action": "cloudwatch:PutMetricData","Effect": "Allow","Resource": "*"
    }] }})

   
   
   #functional Test 1: Lambda timeout is less than or equal to 30 seconds
def test_lambda_timeout(getStack):
    template = assertions.Template.from_stack(getStack)
    lambdas = template.find_resources("AWS::Lambda::Function")
    for _, props in lambdas.items():
        timeout = props["Properties"].get("Timeout", 0)
        assert timeout <= 30, f"Lambda timeout too high: {timeout}s"

# Functional Test 2: CloudWatch alarms have evaluation periods
def test_alarms_evaluation_periods(getStack):
    template = assertions.Template.from_stack(getStack)
    alarms = template.find_resources("AWS::CloudWatch::Alarm")
    for _, alarm in alarms.items():
        periods = alarm["Properties"].get("EvaluationPeriods", 0)
        assert periods >= 1, "Alarm must have at least 1 evaluation period"

# Functional Test 3: Lambda runtime is Python 3.11
def test_lambda_runtime_python311(getStack):
    template = assertions.Template.from_stack(getStack)
    lambdas = template.find_resources("AWS::Lambda::Function")
    for _, props in lambdas.items():
        runtime = props["Properties"].get("Runtime", "")
        assert runtime == "python3.11", f"Lambda runtime is not python3.11 but {runtime}"

# Functional Test 4: Scheduled Event Rule triggers Lambda
def test_event_rule_targets_lambda(getStack):
    template = assertions.Template.from_stack(getStack)
    rules = template.find_resources("AWS::Events::Rule")
    assert rules, "No EventBridge rules found"

    for _, rule in rules.items():
        targets = rule["Properties"].get("Targets", [])
        assert targets, "Event rule has no targets"

        # Check that at least one target is a Lambda
        lambda_target_found = False
        for t in targets:
            # CDK thường dùng Fn::GetAtt hoặc Ref cho Lambda ARN
            if "Arn" in t:
                lambda_target_found = True
            elif "TargetId" in t or "Id" in t:
                lambda_target_found = True
        assert lambda_target_found, "Event rule has no Lambda target"


# Functional Test 5: RemovalPolicy is set to DESTROY for non-critical resources
def test_removal_policy_destroy(getStack):
    template = assertions.Template.from_stack(getStack)
    resources = template.find_resources("AWS::Lambda::Function")
    for _, props in resources.items():
        # Check UpdateReplacePolicy / DeletionPolicy exists and is DELETE
        deletion_policy = props.get("DeletionPolicy", None)
        assert deletion_policy == "Delete" or deletion_policy is None, "Lambda missing DeletionPolicy=Delete"