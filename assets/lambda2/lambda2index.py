import json
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def handler(event, context):
    """
    Lambda2 recives a message from and sqs if there is a message
    it logs it and return an status code 200
    """
    logger.info('Received event: %s', json.dumps(event))
    # Obtains the records message from sqs trigger
    records = event.get('Records', None)

    # Check if there is records
    if records:
        for record in records:
            body = record.get('body', None)
            logger.info('Received message: %s', body)
    else:
        logger.info('No Records')

    response = {
        "statusCode": 200
    }

    return response
