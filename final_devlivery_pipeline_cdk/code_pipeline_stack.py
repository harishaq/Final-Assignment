from aws_cdk import (
    Stack,
    aws_codepipeline as codepipeline,
    aws_codepipeline_actions as codepipeline_actions,
    aws_codecommit as codecommit,
    aws_codebuild as codebuild,
    aws_iam as iam
)
from constructs import Construct

class CodePipelineStack(Stack):

    def __init__(self, scope: Construct, id: str, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)

        # Define a CodeCommit repository
        repo = codecommit.Repository(self, "MyRepository",
                                     repository_name="java-project")
        
        # Get the CfnRepository (CloudFormation Resource) from the repository
        # source: https://stackoverflow.com/questions/72242353/init-codecommit-repository-with-seed-code-stored-in-s3-using-cdk
        cfn_repo = repo.node.default_child

        # Add a property override to the CfnRepository to initialize with code from S3
        cfn_repo.add_property_override('Code', {
            'S3': {
                'Bucket': 'seis665-public',
                'Key': 'java-project.zip',
            },
            'BranchName': 'development',
        })

        # Define the source action
        source_output = codepipeline.Artifact()
        source_action = codepipeline_actions.CodeCommitSourceAction(
            action_name="CodeCommit",
            repository=repo,
            branch="development",
            output=source_output
        )

        # Define the build project
        build_project = codebuild.PipelineProject(self, "BuildProject", 
                                                   environment=codebuild.BuildEnvironment(
                                                      compute_type=codebuild.ComputeType.SMALL,  # Specify the compute type
                                                      build_image=codebuild.LinuxBuildImage.STANDARD_5_0  # Specify the build image
                                                  ) )

        # Define the build action
        build_action = codepipeline_actions.CodeBuildAction(
            action_name="CodeBuild",
            project=build_project,
            input=source_output
        )

        # Define the pipeline
        pipeline = codepipeline.Pipeline(self, "MyPipeline",
                                         stages=[
                                             codepipeline.StageProps(
                                                 stage_name="Source",
                                                 actions=[source_action]
                                             ),
                                             codepipeline.StageProps(
                                                 stage_name="Build",
                                                 actions=[build_action]
                                             )
                                         ])

        # Grant the necessary permissions to the pipeline
        repo.grant_read(pipeline.role)
        build_project.role.add_to_policy(
            iam.PolicyStatement(
                actions=["sts:AssumeRole"],
                resources=["*"]
            )
        )

