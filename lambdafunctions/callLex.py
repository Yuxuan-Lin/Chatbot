"""
This sample demonstrates an implementation of the Lex Code Hook Interface
in order to serve a sample bot which manages reservations for hotel rooms and car rentals.
Bot, Intent, and Slot models which are compatible with this sample can be found in the Lex Console
as part of the 'BookTrip' template.

For instructions on how to set up and test this bot, as well as additional samples,
visit the Lex Getting Started documentation http://docs.aws.amazon.com/lex/latest/dg/getting-started.html.
"""

import json
import datetime
import time
import os
import dateutil.parser
import logging
import boto3

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

sqs = boto3.client('sqs')


# --- Helpers that build all of the responses ---

def elicit_slot(session_attributes, intent_name, slots, slot_to_elicit, message):
    return {
        'sessionState' : {
            'sessionAttributes' : session_attributes,
            'dialogAction' : {
                'type' : 'ElicitSlot',
                'slotToElicit' : slot_to_elicit
            },
            'intent' : {
                'name' : intent_name,
                'slots' : slots,
                'state' : 'InProgress'
            }
        },
        'messages': [
            {
                "content" : message,
                "contentType" : "PlainText"
            }
        ]
    }


def confirm_intent(session_attributes, intent_name, slots, message):
    return {
        'sessionAttributes': session_attributes,
        'dialogAction': {
            'type': 'ConfirmIntent',
            'intentName': intent_name,
            'slots': slots,
            'message': message
        }
    }


def close(session_attributes, fulfillment_state, message, intent_name):
    response = {
        'sessionState' : {
            'sessionAttributes' : session_attributes,
            'dialogAction' : {
                'type' : 'Close'
            },
            'intent' : {
                'name' : intent_name,
                'state' : 'Fulfilled'
            }
        },
        'messages' : [message]
    }

    return response


def delegate(session_attributes, slots, intent_name):
    return {
        'sessionState' : {
            'sessionAttributes' : session_attributes,
            'dialogAction' : {
                'type' : 'Delegate'
            },
            'intent' : {
                'name' : intent_name,
                'slots' : slots,
                'state' : 'ReadyForFulfillment'
            }
        }
    }


# --- Helper Functions ---


def safe_int(n):
    """
    Safely convert n value to int.
    """
    if n is not None:
        return int(n)
    return n


def try_ex(func):
    """
    Call passed in function in try block. If KeyError is encountered return None.
    This function is intended to be used to safely access dictionary.

    Note that this function would have negative impact on performance.
    """

    try:
        return func()
    except KeyError:
        return None

def isvalid_city(city):
    valid_cities = ['new york', 'nyc', 'new york city']
    return city.lower() in valid_cities


def isvalid_cuisine(cuisine):
    valid_cuisines = ['chinese', 'japanese', 'french', 'mexican', 'korean', 'american']
    return cuisine.lower() in valid_cuisines

def isvalid_party_num(party_num):
    return isinstance(party_num, int) and 1 <= party_num and party_num <= 10

def isvalid_dining_date(dining_date):
    try:
        dateutil.parser.parse(dining_date)
        return True
    except ValueError:
        return False

def isvalid_dining_time(dining_time):
    # TODO: need to implement this
    return True 

def isvalid_email(email):
    # TODO: need to implement this
    return True


def build_validation_result(isvalid, violated_slot, message_content):
    return {
        'isValid': isvalid,
        'violatedSlot': violated_slot,
        'message': {'contentType': 'PlainText', 'content': message_content}
    }

def validate_dining_request(slots):
    city_obj = try_ex(lambda: slots['City'])
    cuisine_obj = try_ex(lambda: slots['Cuisine'])
    party_num_obj = try_ex(lambda: slots['PartyNum'])
    dining_date_obj = try_ex(lambda: slots['Date'])
    dining_time_obj = try_ex(lambda: slots['Time'])
    email_obj = try_ex(lambda: slots['Email'])

    if city_obj:
        city = city_obj['value']['interpretedValue']
    else:
        city = None
    
    if cuisine_obj:
        cuisine = cuisine_obj['value']['interpretedValue']
    else:
        cuisine = None 
    
    if party_num_obj:
        party_num = safe_int(party_num_obj['value']['interpretedValue'])
    else:
        party_num = None 
    
    if dining_date_obj:
        dining_date = dining_date_obj['value']['interpretedValue']
    else:
        dining_date = None 
    
    if dining_time_obj:
        dining_time = dining_time_obj['value']['interpretedValue']
    else:
        dining_time = None 
    
    if email_obj:
        email = email_obj['value']['interpretedValue']
    else:
        email = None
    
    if city and not isvalid_city(city):
        return build_validation_result(
            False,
            'City',
            'We currently do not support {} as a valid destination.  Can you try a different city?'.format(city)
        )

    if cuisine and not isvalid_cuisine(cuisine):
        return build_validation_result(
            False,
            'Cuisine',
            'We currently do not support {} as a valid cuisine selection.  Can you try a different cuisine?'.format(cuisine)
        )

    if party_num and not isvalid_party_num(party_num):
        return build_validation_result(
            False,
            'PartyNum',
            'You can only reserve for party size between 1 and 10, your party number size {0} is not in this range'.format(party_num)
        )

    if dining_date and not isvalid_dining_date(dining_date):
        return build_validation_result(
            False,
            'Date',
            'Selected dining date {0} is not valid, please try a different date'.format(dining_date)
        )
    
    if dining_time and not isvalid_dining_time(dining_time):
        return build_validation_result(
            False,
            'Time',
            'Selected dining time {0} is not valid, please try a different date'.format(dining_time)
        )

    if email and not isvalid_email(email):
        return build_validation_result(
            False,
            'email',
            'The email address {0} provided is not valid, please provide a different one'.format(email)
        )
    
    return {'isValid': True}


""" --- Functions that control the bot's behavior --- """


def dining_suggestion(intent_request):
    """
    Performs dialog management and fulfillment for suggest a dining choice.

    Beyond fulfillment, the implementation for this intent demonstrates the following:
    1) Use of elicitSlot in slot validation and re-prompting
    2) Use of sessionAttributes to pass information that can be used to guide conversation
    """

    city_obj = try_ex(lambda: intent_request['sessionState']['intent']['slots']['City'])
    dining_date_obj = try_ex(lambda: intent_request['sessionState']['intent']['slots']['Date'])
    dining_time_obj = try_ex(lambda: intent_request['sessionState']['intent']['slots']['Time'])
    email_obj = try_ex(lambda: intent_request['sessionState']['intent']['slots']['Email'])
    cuisine_obj = try_ex(lambda: intent_request['sessionState']['intent']['slots']['Cuisine'])
    party_num_obj = try_ex(lambda: intent_request['sessionState']['intent']['slots']['PartyNum'])

    if city_obj:
        city = city_obj['value']['interpretedValue']
    else:
        city = None
    
    if cuisine_obj:
        cuisine = cuisine_obj['value']['interpretedValue']
    else:
        cuisine = None 
    
    if party_num_obj:
        party_num = safe_int(party_num_obj['value']['interpretedValue'])
    else:
        party_num = None 
    
    if dining_date_obj:
        dining_date = dining_date_obj['value']['interpretedValue']
    else:
        dining_date = None 
    
    if dining_time_obj:
        dining_time = dining_time_obj['value']['interpretedValue']
    else:
        dining_time = None 
    
    if email_obj:
        email = email_obj['value']['interpretedValue']
    else:
        email = None

    session_attributes = intent_request['sessionState']['sessionAttributes'] if intent_request['sessionState']['sessionAttributes'] is not None else {}

    # Load dining suggestion history and track the current dining request
    dining_request = json.dumps({
        'RequestType': 'DiningSuggestion',
        'City': city,
        'Cuisine': cuisine,
        'PartyNum': party_num,
        'Date': dining_date,
        'Time': dining_time,
        'Email': email
    })

    session_attributes['currentDiningRequest'] = dining_request

    if intent_request['invocationSource'] == 'DialogCodeHook':
        # Validate any slots which have been specified.  If any are invalid, re-elicit for their value
        validation_result = validate_dining_request(intent_request['sessionState']['intent']['slots'])
        if not validation_result['isValid']:
            slots = intent_request['sessionState']['intent']['slots']
            slots[validation_result['violatedSlot']] = None

            return elicit_slot(
                session_attributes,
                intent_request['sessionState']['intent']['name'],
                slots,
                validation_result['violatedSlot'],
                validation_result['message']
            )

        if not city:
            slots = intent_request['sessionState']['intent']['slots']

            return elicit_slot(
                session_attributes,
                intent_request['sessionState']['intent']['name'],
                slots,
                'City',
                'What city or city area are you looking to dine in?'
            )
        
        if not cuisine:
            slots = intent_request['sessionState']['intent']['slots']

            return elicit_slot(
                session_attributes,
                intent_request['sessionState']['intent']['name'],
                slots,
                'Cuisine',
                'What cuisine would you like to try?'
            )

        if not party_num:
            slots = intent_request['sessionState']['intent']['slots']

            return elicit_slot(
                session_attributes,
                intent_request['sessionState']['intent']['name'],
                slots,
                'PartyNum',
                'How many people are in your party?'
            )
        
        if not dining_date:
            slots = intent_request['sessionState']['intent']['slots']

            return elicit_slot(
                session_attributes,
                intent_request['sessionState']['intent']['name'],
                slots,
                'Date',
                'What date?'
            )
        
        if not dining_time:
            slots = intent_request['sessionState']['intent']['slots']

            return elicit_slot(
                session_attributes,
                intent_request['sessionState']['intent']['name'],
                slots,
                'Time',
                'What time?'
            )
        
        if not email:
            slots = intent_request['sessionState']['intent']['slots']

            return elicit_slot(
                session_attributes,
                intent_request['sessionState']['intent']['name'],
                slots,
                'Email',
                'I need your email address so I can send you my findings?'
            )

        session_attributes['currentDiningRequest'] = dining_request
        return delegate(session_attributes, intent_request['sessionState']['intent']['slots'], intent_request['sessionState']['intent']['name'])

    # Submit the dining request.  In a real application, this would likely involve a call to a backend service.
    logger.debug('Dining Request under={}'.format(dining_request))
    sqs_response = sqs.send_message(
            QueueUrl="https://sqs.us-east-1.amazonaws.com/993611456293/MyChatbotQueue",
            MessageBody=dining_request
        )
    print("SQS Response: " + json.dumps(sqs_response))

    try_ex(lambda: session_attributes.pop('currentDiningRequest'))
    session_attributes['lastConfirmedDiningRequest'] = dining_request

    return close(
        session_attributes,
        'Fulfilled',
        {
            'contentType': 'PlainText',
            'content': 'Thanks, I have submitted your dining request.   Please let me know if you would like to submit another request.'
        },
        intent_request['sessionState']['intent']['name']
    )


# --- Intents ---


def dispatch(intent_request):
    """
    Called when the user specifies an intent for this bot.
    """

    logger.debug('dispatch sessionId={}, intentName={}'.format(intent_request['sessionId'], intent_request['sessionState']['intent']['name']))

    intent_name = intent_request['sessionState']['intent']['name']

    # Dispatch to your bot's intent handlers
    if intent_name == 'DiningSuggestiongsIntent':
        return dining_suggestion(intent_request)

    raise Exception('Intent with name ' + intent_name + ' not supported')


# --- Main handler ---


def lambda_handler(event, context):
    """
    Route the incoming request based on intent.
    The JSON body of the request is provided in the event slot.
    """
    # By default, treat the user request as coming from the America/New_York time zone.
    os.environ['TZ'] = 'America/New_York'
    time.tzset()
    logger.debug('event.bot.name={}'.format(event['bot']['name']))

    return dispatch(event)
