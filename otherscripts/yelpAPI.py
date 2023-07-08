import requests
import json

def get_businesses(location, term, api_key):
    headers = {'Authorization': 'Bearer %s' % api_key}
    url = 'https://api.yelp.com/v3/businesses/search'

    data = []
    for offset in range(0, 1000, 50):
        params = {
            'limit': 50, 
            'location': location.replace(' ', '+'),
            'term': term.replace(' ', '+'),
            'offset': offset
        }

        response = requests.get(url, headers=headers, params=params)
        if response.status_code == 200:
            data += response.json()['businesses']
        elif response.status_code == 400:
            print('400 Bad Request')
            break

    return data


api_key = "XVjQYBGJ8qiIECXH4ibSJxFkZIrFAUfDuIhLmGDQakcT8QDR6yJbeI1LAioOQ-ZzZ0diWiUsO7OUMBWx9O7WZvg_WtSD7-0g-kYJ_0S_XnKo_AvSBIPD676tammcZHYx"
cuisines = ["chinese restaurant", "japanese restaurant", "french restaurant", "mexican restaurant", "korean restaurant", "american restaurant"]
location = "Manhattan"

restaurants = {}
for cuisine in cuisines:
    restaurants[cuisine] = get_businesses(location, cuisine, api_key)

with open("restaurants_data.txt", "w") as f:
    json_object = json.dumps(restaurants, indent = 4)
    f.write(json_object)
