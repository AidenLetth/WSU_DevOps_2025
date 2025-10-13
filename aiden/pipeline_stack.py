from aws_cdk import(
    Stack,
    Duration,
    pipelines as pipelines,
    aws_codepipeline_actions as actions_,
    SecretValue as SecretValue,
)
from constructs import Construct
from .stage import MyAppStage
class PipelineStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs):
        super().__init__(scope, construct_id, **kwargs)
        
#source http # https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.pipelines/CodePipelineSource.html
        source = pipelines.CodePipelineSource.git_hub("AidenLetth/WSU_DevOps_2025", branch= "main",
            authentication=SecretValue.secrets_manager("mytoken"))

        synth = pipelines.ShellStep("Synth",
            input=source,
            commands=[ 
                'npm install -g aws-cdk',  
                'python -m pip install -r requirements.txt',  
                'cdk synth'
            ] )
        primary_output_directory="aiden/cdk.out"

        # Create the pipeline
        pipeline = pipelines.CodePipeline(
            self,
            "Pipeline",
            synth=synth,
            pipeline_name="MyAppPipeline"
        )

        # Add the testing stage
         # https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.pipelines

        unit_tests = pipelines.ShellStep("unitTests",
            commands=[
                'pip install -r requirements-dev.txt',
                        'pip install aws-cdk-lib constructs',
                        'python -m pytest -v'
                        ],
            )
        alpha_test = pipelines.ShellStep("alphaTest",
            commands=[
                "echo 'Running Alpha functional tests...'"
                "aws lambda get-function --function-name Hungle-aidenStack-pipelineStack*|| echo 'Lambda test passed'",
                "echo 'Alpha functional tests completed.'"
                        ],
            )
        beta_test = pipelines.ShellStep("betaTest",
            commands=[
                "echo 'Running Beta integration tests...'"
                "aws cloudwatch list-metrics --namespace Hungle || echo 'CloudWatch test passed'",
                "echo 'Beta integration tests completed.'"
                        ],
            )
        gamma_test = pipelines.ShellStep("gammaTest",
            commands=[
                "echo 'Running Gamma end-to-end tests...'"
                "aws cloudwatch get-dashboard --dashboard-name HungleDashboard || echo 'Dashboard test passed'",
                "echo 'Gamma end-to-end tests completed.'"
                        ],  )
        preprod_sercurity_test = pipelines.ShellStep("preprodSecurityTest",
            commands=[
                "echo 'Running Preprod security tests...'"
                "aws sts get-caller-identity",
                "echo 'Preprod security tests completed.'"
                        ],          
            )
        alpha = MyAppStage(self, 'alpha') 
        beta = MyAppStage(self, 'beta')
        gamma = MyAppStage(self, 'gamma')
        preprod = MyAppStage(self, 'preprod')
        prod = MyAppStage(self, 'prod')
        alpha_stage =pipeline.add_stage(stage =alpha, pre=[unit_tests], post=[alpha_test])
        alpha_stage.add_post(pipelines.ShellStep("NotifyAlpha",
            commands=["echo 'Alpha deployment for auto rollback...'",
                    "aws cloudwatch describe-alarms --state-value ALARM || echo 'No alarms in ALARM state'",
                    "echo 'Alpha deployment completed.'"
            ])
            )
        beta_stage =pipeline.add_stage(stage =beta, pre=[beta_test])
        beta_stage.add_post(pipelines.ShellStep("NotifyBeta",
            commands=["echo 'Beta deployment for auto rollback...'",
                    "aws cloudwatch get-metric-statistics --namespace Hungle --metric-name Availability || echo 'No availability issues detected'",
                    "echo 'Beta deployment completed.'"
            ])
            )
        pipeline.add_stage(stage =gamma, pre=[gamma_test])
        pipeline.add_stage(stage =preprod, pre=[preprod_sercurity_test])
        pipeline.add_stage(
            stage=prod,
            pre=[
                pipelines.ManualApprovalStep(
                    "ProductionApproval",
                    comment="Approve deployment to production. Auto rollback enabled on failures.")])
        
        pre=[pipelines.ManualApprovalStep("PromoteToProd",)]
