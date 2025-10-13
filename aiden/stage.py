
from aws_cdk import Stage
from constructs import Construct
from .aiden_stack import AidenStack

# Define the stage
class MyAppStage(Stage):
    def __init__(self, scope: Construct, id: str, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)
        self.Stage = AidenStack(self, "AidenStack")