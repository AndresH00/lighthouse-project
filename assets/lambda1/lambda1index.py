import json
import boto3
import os
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def handler(event, context):
    logger.info('Received event: %s', json.dumps(event))

    statusCode = 200
    message = 'Message Successfully Delivered'

    body = event.get('body')

    if body:
        sqs = boto3.client('sqs')
        queue_url = os.getenv('sqs_url')
        logger.info('Queue URL: %s', json.dumps(queue_url))
        parsed_body = json.loads(body)

        try:
            response = sqs.send_message(
                QueueUrl=queue_url,
                MessageBody=json.dumps(parsed_body)
            )
            logger.info('Response Send Message Queue : %s',
                        json.dumps(response))
        except Exception as e:
            print(e)
            statusCode = 500
            message = 'Failed to deliver'
            logger.info('%s : %s', message, e)
    else:
        message = 'Missing message body to deliver'
        statusCode = 400

    response = {
        "statusCode": statusCode,
        "message": message
    }

    logger.info('Response: %s', json.dumps(response))
    return {
        'statusCode': 200,
        'body': json.dumps(response)
    }
