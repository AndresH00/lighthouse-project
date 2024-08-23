import json
import boto3
import os
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def handler(event, context):
    """
    Lambda1 the lambda recives any type of request in json format through
    aws apigateway and it will send it as a message to an aws sqs and the
    sqs will follow to deliver the message to lambda2
    """
    logger.info('Received event: %s', json.dumps(event))

    statusCode = 200
    message = 'Message Successfully Delivered'

    body = event.get('body')

    # Making sure it have a message
    if body:
        # Initialize boto3 sqs client
        sqs = boto3.client('sqs')
        # Getting sqs url from enviroment
        queue_url = os.getenv('sqs_url')
        logger.info('Queue URL: %s', json.dumps(queue_url))
        parsed_body = json.loads(body)

        try:
            # Sending message to sqs
            response = sqs.send_message(
                QueueUrl=queue_url,
                MessageBody=json.dumps(parsed_body)
            )
            logger.info('Response Send Message Queue : %s',
                        json.dumps(response))
        except Exception as e:
            # Failed to send message stablish error status code and new message response
            statusCode = 500
            message = 'Failed to deliver'
            logger.info('%s : %s', message, e)
    else:
        # No message stablish error status code and new message response
        message = 'Missing message body to deliver'
        statusCode = 400

    # Format response
    response = {
        "statusCode": statusCode,
        "message": message
    }

    logger.info('Response: %s', json.dumps(response))
    return {
        'statusCode': 200,
        'body': json.dumps(response)
    }
