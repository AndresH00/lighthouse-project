import json
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def handler(event, context):
    logger.info('Received event: %s', json.dumps(event))
    records = event.get('Records', None)

    if records:
        for record in records:
            body = record.get('body', None)
            logger.info('Received message: %s', json.dumps(body))
    else:
        logger.info('No Records')

    response = {
        "statusCode": 200
    }

    return response
