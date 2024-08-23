import aws_cdk as core
import aws_cdk.assertions as assertions

from lighthouse_project.lighthouse_project_stack import LighthouseProjectStack

# example tests. To run these tests, uncomment this file along with the example
# resource in lighthouse_project/lighthouse_project_stack.py
def test_sqs_queue_created():
    app = core.App()
    stack = LighthouseProjectStack(app, "lighthouse-project")
    template = assertions.Template.from_stack(stack)

#     template.has_resource_properties("AWS::SQS::Queue", {
#         "VisibilityTimeout": 300
#     })
