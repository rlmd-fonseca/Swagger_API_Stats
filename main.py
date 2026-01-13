import json

with open("swagger.json") as json_file:
    data = json.load(json_file)

total_number_parameters = 0
total_number_of_post_requests = 0
total_number_of_get_requests_with_parameters = 0
total_number_of_get_requests_without_parameters = 0

for path in data["paths"]:
    for method in data["paths"][path]:
        if method == "post" or method == "put":
            total_number_of_post_requests += 1
        if method == "get" or method == "delete":
            if data["paths"][path][method]["parameters"]:
                total_number_of_get_requests_with_parameters += 1
            else:
                total_number_of_get_requests_without_parameters += 1
        total_number_parameters += len(data["paths"][path][method]["parameters"])

print(f"Total number of parameters: {total_number_parameters}")
print(f"Total number of POST and PUT requests: {total_number_of_post_requests}")
print(f"Total number of GET and DELETE requests with parameters: {total_number_of_get_requests_with_parameters}")
print(f"Total number of GET and DELETE requests without parameters: {total_number_of_get_requests_without_parameters}")
