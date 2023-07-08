import json

# Load restaurants_data.txt file into json format
with open("restaurants_data.txt") as f:
    data =  json.load(f)

with open('restaurants.json', 'w') as f:
    # f.write("{\n")
    for rtype in data.keys():
        for r in data[rtype]:
            r['restaurant type'] = rtype
            item_dict = {}
            item_dict['Item'] = r 
            f.write(json.dumps(item_dict))
            f.write("\n")
    # f.write("}\n")