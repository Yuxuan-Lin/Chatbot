import boto3
import json
import requests
from requests_aws4auth import AWS4Auth


region = 'us-east-1' # For example, us-west-1
service = 'es'
credentials = boto3.Session().get_credentials()
awsauth = AWS4Auth(credentials.access_key, credentials.secret_key, region, service, session_token=credentials.token)

host = 'https://search-chatbotelasticsearch-aovvoofcwq4lsdqbm2h56haqdm.us-east-1.es.amazonaws.com' # The OpenSearch domain endpoint with https:// and without a trailing slash
index = 'restaurants'
url = host + '/' + index + '/_search'

db = boto3.client('dynamodb')

ses = boto3.client('ses')

from_email = 'yl5445@nyu.edu'
 
 
# Lambda execution starts here
def lambda_handler(event, context):
    
    queries = []
    
    # Receive query from SQS
    for record in event['Records']:
        payload = record["body"]
        queries.append(payload)
        print(str(payload))
        
    # For each query, search in opensearch and dynamodb service, and send to user email
    for query_content in queries:
        query_object = json.loads(query_content)
        
    
        # Put the user query into the query DSL for more accurate search results.
        # Note that certain fields are boosted (^).
        query = {
            "size": 5,
            "query": {
                "multi_match": {
                    "query": query_object["Cuisine"],
                    "fields": ["restaurant_type"]
                }
            }
        }
    
        # Elasticsearch 6.x requires an explicit Content-Type header
        headers = { "Content-Type": "application/json" }
    
        # Make the signed HTTP request
        search_response = requests.get(url, auth=awsauth, headers=headers, data=json.dumps(query))

        # print(str(search_response.text))
        
        # Parse OpenSearch response into json, and get all ids of restaurants
        search_object = json.loads(search_response.text)
        search_res_keys = []
        for res in search_object["hits"]["hits"]:
            search_res_keys.append((res["_source"]["PK"], res["_source"]["SK"]))
        
        # print(str(search_res_keys))
        
        # Use some keyword from elastic search result, find records in dynamodb 
        restaurant_list = []
        for res_pk, res_sk in search_res_keys:
            
            data = db.get_item(
                    TableName="yelp-restaurants",
                    Key={
                        'PK': {'S': res_pk},
                        'SK': {'S': res_sk}
                    }
                )
                
            restaurant = data["Item"]
            del restaurant['PK']
            del restaurant['SK']
            del restaurant['id']
            
            restaurant_list.append(json.dumps(restaurant))
        
        print(str(restaurant_list)) 
        
        # Send data to customer with simple email service
        
        body_html = f"""<html>
            <head></head>
            <body>
              <h2>Here are the recommended restaurants based on your request.</h2>
              <br/>
              <p>Your request: {json.dumps(query_object)}</p>
              <p>Recommendations: {str(restaurant_list)}</p> 
            </body>
            </html>
                    """

        email_message = {
            'Body': {
                'Html': {
                    'Charset': 'utf-8',
                    'Data': body_html,
                },
            },
            'Subject': {
                'Charset': 'utf-8',
                'Data': "Restaurant Recommendations Powered by Chatbot",
            },
        }
    
        ses_response = ses.send_email(
            Destination={
                'ToAddresses': [query_object["Email"]],
            },
            Message=email_message,
            Source=from_email
        )
    
        print(f"ses response id received: {ses_response['MessageId']}.")
        
    
    return {}