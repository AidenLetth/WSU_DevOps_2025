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

        all_tests = pipelines.ShellStep("AllTests",
            commands=[
                'pip install -r requirements-dev.txt',
                        'pip install aws-cdk-lib constructs',
                        'python -m pytest -v'
                        ],
            )
        alpha = MyAppStage(self, 'alpha') 
        pipeline.add_stage(alpha, pre=[all_tests])