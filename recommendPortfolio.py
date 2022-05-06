### Required Libraries ###
from datetime import datetime
from dateutil.relativedelta import relativedelta
import logging

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

### Functionality Helper Functions ###
def parse_int(n):
    """
    Securely converts a non-integer value to integer.
    """
    try:
        return int(n)
    except ValueError:
        return float("nan")


def build_validation_result(is_valid, violated_slot, message_content):
    """
    Define a result message structured as Lex response.
    """
    if message_content is None:
        return {"isValid": is_valid, "violatedSlot": violated_slot}

    return {
        "isValid": is_valid,
        "violatedSlot": violated_slot,
        "message": {"contentType": "PlainText", "content": message_content},
    }

def validate_data(age, investmentAmount, intent_request):
    """
    Validates the data provided by the user.
    """

    # Validate that the user is greater than 0 and less than 65 years old
    if age is not None:
            age = parse_int(age)
            if age >= 65 or age <= 0:
                return build_validation_result(
                    False,
                    "age",
                    "You should be less than 65 years in age to use this service, "
                    "please provide a different age."
                )

    # Validate the investment amount, it should be > 5000
    if investmentAmount is not None:
        investmentAmount = parse_int(
            investmentAmount
        )  # Since parameters are strings it's important to cast values
        if investmentAmount <= 5000:
            return build_validation_result(
                False,
                "investmentAmount",
                "The amount to invest should be greater than $5000, "
                "please re-enter the amount in dollars to invest.",
            )

    # A True results are returned if age or amount are valid
    return build_validation_result(True, None, None)
    
    
### Dialog Actions Helper Functions ###
def get_slots(intent_request):
    """
    Fetch all the slots and their values from the current intent.
    """
    return intent_request["currentIntent"]["slots"]

def elicit_slot(session_attributes, intent_name, slots, slot_to_elicit, message):
    """
    Defines an elicit slot type response.
    """

    return {
        "sessionAttributes": session_attributes,
        "dialogAction": {
            "type": "ElicitSlot",
            "intentName": intent_name,
            "slots": slots,
            "slotToElicit": slot_to_elicit,
            "message": message,
        },
    }
    
def delegate(session_attributes, slots):
    """
    Defines a delegate slot type response.
    """

    return {
        "sessionAttributes": session_attributes,
        "dialogAction": {"type": "Delegate", "slots": slots},
    }
    
def recommendation(intent_request):
    risk_level = get_slots(intent_request)["riskLevel"]
    x = risk_level
    if x == "None":
            rec = '100% bonds (AGG), 0% equities (SPY)'
    elif x == "Low":
            rec = '60% bonds (AGG), 40% equities (SPY)'
    elif x == "Medium":
            rec = '40% bonds (AGG), 60% equities (SPY)'
    else:
            rec = '20% bonds (AGG), 80% equities (SPY)'
    return rec
    


def close(session_attributes, fulfillment_state, message):
    """
    Defines a close slot type response.
    """

    response = {
        "sessionAttributes": session_attributes,
        "dialogAction": {
            "type": "Close",
            "fulfillmentState": fulfillment_state,
            "message": message
        },
    }

    return response
    
    ### Intents Handlers ###
def recommend_portfolio(intent_request):
    """
    Performs dialog management and fulfillment for recommending a portfolio.
    """

    first_name = get_slots(intent_request)["firstName"]
    age = get_slots(intent_request)["age"]
    investment_amount = get_slots(intent_request)["investmentAmount"]
    risk_level = get_slots(intent_request)["riskLevel"]
    
    source = intent_request["invocationSource"]

    if source == "DialogCodeHook":
        
        slots = get_slots(intent_request)
        
        validation_result = validate_data(age, investment_amount, intent_request)
        
        if not validation_result["isValid"]:
            slots[validation_result["violatedSlot"]] = None
            
            return elicit_slot(
                intent_request["sessionAttributes"],
                intent_request["currentIntent"]["name"],
                slots,
                validation_result["violatedSlot"],
                validation_result["message"],
            )
            
        output_session_attributes = intent_request["sessionAttributes"]
        
        return delegate(output_session_attributes, get_slots(intent_request))
        
    adv = recommendation(
        intent_request)
            
    return close(
        intent_request["sessionAttributes"],
        "Fulfilled",
        {
            "contentType": "PlainText",
            "content": 'Based on your risk level, we recommend a portfolio of {}'.format(adv)
        },
    )
            
### Intents Dispatcher ###
def dispatch(intent_request):
    """
    Called when the user specifies an intent for this bot.
    """

    intent_name = intent_request["currentIntent"]["name"]

    # Dispatch to bot's intent handlers
    if intent_name == "recommendPortfolio":
        return recommend_portfolio(intent_request)

    raise Exception("Intent with name " + intent_name + " not supported")


### Main Handler ###
def lambda_handler(event, context):
    """
    Route the incoming request based on intent.
    The JSON body of the request is provided in the event slot.
    """
    logger.debug('event={}'.format(event))
    response = dispatch(event)
    logger.debug(response)
    return response

