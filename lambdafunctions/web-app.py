import json
import boto3
import uuid

client = boto3.client('lexv2-runtime')

botId = '3WL24OHBCN'
botAliasId = 'TSTALIASID'
localeId = 'en_US'
sessionId = str(uuid.uuid4())

def handle_chat(request_text):
    # Send text to lex
    print(request_text)
    response = client.recognize_text(
        botId = botId,
        botAliasId = botAliasId,
        localeId = localeId,
        sessionId = sessionId,
        text = request_text)
    # Pull response message
    response_msgs = response['messages']
    response_texts = []
    for msg in response_msgs:
        response_texts.append(msg['content'])
    return response_texts


def lambda_handler(event, context):
    messages = event['messages']
    
    response_msgs = []
    
    for message in messages:
        # TODO: simple validation on message format
        request_text = message['unstructured']['text']
        response_texts = handle_chat(request_text)
        for response_text in response_texts:
            response_obj = {"type" : "unstructured", "unstructured" : {"text" : response_text}}
            response_msgs.append(response_obj)
        
    # TODO implement
    # response_text = {"messages" : [{"type" : "unstructured", "unstructured" : {"text" : "I’m still under development. Please come back later."}}]}
    #response_obj = [{"type" : "unstructured", "unstructured" : {"text" : response_text}}]
    return {
        'statusCode': 200,
        'headers': {
            'Access-Control-Allow-Headers': 'Content-Type',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'OPTIONS,POST,GET'
        },
        # 'body': json.dumps('I’m still under development. Please come back later.')
        "messages": response_msgs
    }
