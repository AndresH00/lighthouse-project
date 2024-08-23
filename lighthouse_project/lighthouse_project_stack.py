from aws_cdk import (
    Duration,
    Stack,
    aws_sqs as sqs,
    aws_lambda as _lambda,
    aws_apigateway as apigateway,
    aws_lambda_event_sources as lambda_event_sources,
    aws_iam as iam,
    aws_logs as logs
)
from constructs import Construct
from pathlib import Path
import os


class LighthouseProjectStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)
        """
        Resources Used
        Sqs-creation: https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_sqs/Queue.html
        Sqs-lambda integration: https://gist.github.com/alexkates/59e3b6f582d2444e86a723d0d707a8f8
        Sqs-lambda event source: https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_lambda_event_sources.html
        Lambda-creation: https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_lambda/Function.html
        Lambda-integration: https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_apigateway/LambdaIntegration.html
        ApiRest-creation: https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_apigateway/RestApi.html
        Api-example: https://github.com/aws-samples/aws-cdk-examples/blob/main/python/api-sqs-lambda/api_sqs_lambda/api_sqs_lambda_stack.py
        Api-MethodResponse: https://docs.aws.amazon.com/cdk/api/latest/python/aws_cdk.aws_apigateway/MethodResponse.html
        Api-IntegrationResponse: https://docs.aws.amazon.com/cdk/api/latest/python/aws_cdk.aws_apigateway/IntegrationResponse.html
        Api-LambdaIntegration: https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_apigateway/LambdaIntegration.html
        Api-Deployment: https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_apigateway/StageOptions.html
        Api-AccessLogFormat: https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_apigateway/AccessLogFormat.html
        Role-creation: https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_iam/Role.html
        Policy-creation: https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_iam/PolicyStatement.html
        """
        lambda1_path = Path('./assets/lambda1').resolve()
        lambda2_path = Path('./assets/lambda2').resolve()

        # Cloudwatch policy statement so the resources are avalaible to log
        cloudwatch_log_policy = iam.PolicyStatement(
            actions=[
                "logs:CreateLogGroup",
                "logs:CreateLogStream",
                "logs:PutLogEvents"
            ],
            resources=["arn:aws:logs:*"]
        )

        # Creation of lambda2 role
        lambda2_role = iam.Role(self, "lambda2_role",
                                assumed_by=iam.ServicePrincipal(
                                    'lambda.amazonaws.com')
                                )

        # Added Cloudwatch log policy to lambda2 role
        lambda2_role.add_to_policy(cloudwatch_log_policy)

        # Creation of lambda2
        lambda2 = _lambda.Function(
            self,
            id="lambda2",
            runtime=_lambda.Runtime.PYTHON_3_12,
            handler="lambda2index.handler",
            description="Lambda 2 that triggers when sqs receives a message and logs payload",
            role=lambda2_role,
            code=_lambda.Code.from_asset(str(lambda2_path))
        )

        # Creation of SQS
        queue = sqs.Queue(
            self, "LighthouseProjectQueue",
            visibility_timeout=Duration.seconds(300),
        )

        # Creation of sqs policy so lambda resources can invoke it
        sqs_lambda_policy_statement = iam.PolicyStatement(
            actions=[
                "sqs:SendMessage"
            ],
            principals=[iam.ServicePrincipal('lambda.amazonaws.com')],
            resources=[queue.queue_arn]
        )

        # Added the policy to sqs
        queue.add_to_resource_policy(sqs_lambda_policy_statement)

        # Add neccesary policies the lambda2 consume sqs messages
        queue.grant_consume_messages(lambda2)

        # Create event source for my sqs
        event_source = lambda_event_sources.SqsEventSource(queue)

        # Connect lambda with sqs through events
        lambda2.add_event_source(event_source)

        # Create lambda 1 role
        lambda1_role = iam.Role(self, "lambda1_role",
                                assumed_by=iam.ServicePrincipal(
                                    'lambda.amazonaws.com')
                                )

        # Added policy statement so lambda1 can send message to specific sqs
        lambda1_role.add_to_policy(iam.PolicyStatement(
            actions=["sqs:SendMessage",
                     ],
            resources=[queue.queue_arn]
        ))

        # Added to role cloudwatch policy
        lambda1_role.add_to_policy(cloudwatch_log_policy)

        # Creation of lambda1
        lambda1 = _lambda.Function(
            self,
            id="lambda1",
            runtime=_lambda.Runtime.PYTHON_3_12,
            handler="lambda1index.handler",
            description="Lambda 1 that sends message from api to sqs",
            role=lambda1_role,
            code=_lambda.Code.from_asset(str(lambda1_path)),
            environment={'sqs_url': queue.queue_url}
        )

        # Creation of apigateway role
        rest_api_role = iam.Role(self, "RestAPIRole",
                                 assumed_by=iam.ServicePrincipal(
                                     "apigateway.amazonaws.com")
                                 )

        # Creation of policy statement so apigateway can invoke lamba1
        rest_api_role.add_to_policy(iam.PolicyStatement(
            actions=["lambda:InvokeFunction",
                     ],
            resources=[lambda1.function_arn]
        ))

        # Added cloudwatch policy to log
        rest_api_role.add_to_policy(cloudwatch_log_policy)

        # Creation of log group for apigateway dev stage
        dev_log_group = logs.LogGroup(self, "DevLogs")

        # Configuration for apigateway dev stage
        dev_options = apigateway.StageOptions(
            access_log_destination=apigateway.LogGroupLogDestination(
                dev_log_group),
            access_log_format=apigateway.AccessLogFormat.json_with_standard_fields(
                caller=False,
                http_method=True,
                ip=True,
                protocol=True,
                request_time=True,
                resource_path=True,
                response_length=True,
                status=True,
                user=True
            ),
            stage_name='dev',
            tracing_enabled=False,
            logging_level=apigateway.MethodLoggingLevel.INFO
        )

        # Creation of apigateway rest api
        api = apigateway.RestApi(self, "Api",
                                 rest_api_name="ApiRestLambda1",
                                 deploy=True,
                                 deploy_options=dev_options
                                 )

        # Added resource for my api named lambda1
        api_resource = api.root.add_resource('lambda1')

        # Create a method response
        method_response = apigateway.MethodResponse(status_code="200")

        # Create a integration response
        integration_response = apigateway.IntegrationResponse(
            status_code="200",
            response_templates={"application/json": ""},
        )

        # Integration of my lambda and my api
        api_lambda_integration = apigateway.LambdaIntegration(
            handler=lambda1,
            proxy=True,
            credentials_role=rest_api_role,
            integration_responses=[integration_response],
            passthrough_behavior=apigateway.PassthroughBehavior.NEVER,
            request_parameters={
                "integration.request.header.Content-Type": "'application/x-www-form-urlencoded'"},
            request_templates={
                "application/json": "Action=SendMessage&MessageBody=$input.body"}
        )

        # Create my http method post integrated with my lambda
        api_resource.add_method("POST",
                                api_lambda_integration,
                                method_responses=[method_response]
                                )
