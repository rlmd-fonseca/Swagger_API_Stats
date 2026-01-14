import json
from collections import Counter


def get_properties_info(definition_name, definitions, visited=None):
    """Recursively returns the count and names of all properties in a definition."""
    if visited is None:
        visited = set()

    if definition_name not in definitions or definition_name in visited:
        return 0, []

    visited.add(definition_name)
    definition = definitions[definition_name]
    props = definition.get("properties", {})
    names = list(props.keys())
    count = len(props)

    for prop_name, prop_data in props.items():
        sub_count = 0
        sub_names = []
        if "$ref" in prop_data:
            ref_name = prop_data["$ref"].split("/")[-1]
            sub_count, sub_names = get_properties_info(ref_name, definitions, visited)
        elif prop_data.get("type") == "array" and "items" in prop_data:
            items = prop_data["items"]
            if "$ref" in items:
                ref_name = items["$ref"].split("/")[-1]
                sub_count, sub_names = get_properties_info(ref_name, definitions, visited)

        count += sub_count
        names.extend(sub_names)

    return count, names


with open("swagger.json") as json_file:
    data = json.load(json_file)

definitions = data.get("definitions", {})
paths = data.get("paths", {})

# Counters
metrics = {
    "methods": {
        "get": {"count": 0, "params": 0},
        "post": {"count": 0, "params": 0},
        "put": {"count": 0, "params": 0},
        "patch": {"count": 0, "params": 0},
        "delete": {"count": 0, "params": 0},
    },
    "total_params_raw": 0,  # Original shallow count
    "deep_attack_surface": 0,  # Recursive JSON count
    "file_uploads": 0,
    "auth_endpoints": 0,
    "deprecated": 0
}
parameter_frequency = Counter()

for path, methods in paths.items():
    for method, details in methods.items():
        method = method.lower()
        params = details.get("parameters", [])

        # 1. Method Classification & Parameter Logic
        if method in metrics["methods"]:
            metrics["methods"][method]["count"] += 1

        method_total_fields = 0
        for p in params:
            param_name = p.get("name")
            if p.get("in") != "body":
                method_total_fields += 1
                parameter_frequency[param_name] += 1
            else:
                # Resolve JSON Body Complexity
                schema = p.get("schema", {})
                body_count = 0
                body_names = []
                if "$ref" in schema:
                    ref_name = schema["$ref"].split("/")[-1]
                    body_count, body_names = get_properties_info(ref_name, definitions)
                elif schema.get("type") == "array" and "$ref" in schema.get("items", {}):
                    ref_name = schema["items"]["$ref"].split("/")[-1]
                    body_count, body_names = get_properties_info(ref_name, definitions)
                elif schema.get("type") == "object":
                    props = schema.get("properties", {})
                    body_count = len(props)
                    body_names = list(props.keys())

                # Add the 'body' parameter itself to the frequency counter?
                # The user asked for "total fields", usually 'body' is just a wrapper in Swagger 2.0.
                # However, previous version counted 'body'. Let's keep 'body' but add its children.
                parameter_frequency[param_name] += 1
                method_total_fields += body_count

                for name in body_names:
                    parameter_frequency[name] += 1

        if method in metrics["methods"]:
            metrics["methods"][method]["params"] += method_total_fields

        metrics["total_params_raw"] += len(params)
        metrics["deep_attack_surface"] += method_total_fields

        # 2. Risk Indicators
        if details.get("deprecated"):
            metrics["deprecated"] += 1
        if "multipart/form-data" in details.get("consumes", []):
            metrics["file_uploads"] += 1
        if any(keyword in path.lower() for keyword in ["login", "auth", "password", "token"]):
            metrics["auth_endpoints"] += 1

# Output Formatting
print("=" * 30)
print("PRE-SALES API SCOPING REPORT")
print("=" * 30)
print("METHOD BREAKDOWN")
for m, stats in metrics["methods"].items():
    print(f"  {m.upper()}: {stats['count']} requests, {stats['params']} parameters")
print("-" * 30)
print(f"Total Parameters (Shallow): {metrics['total_params_raw']}")
print(f"Deep Attack Surface (Total fields): {metrics['deep_attack_surface']}")
print(f"  * This counts every nested property in JSON bodies.")
print("-" * 30)
print("TOP 10 COMMON PARAMETERS")
for param, count in parameter_frequency.most_common(10):
    print(f"  - {param}: {count}")
print("-" * 30)
print(f"High-Risk Flags:")
print(f"  - File Upload Endpoints: {metrics['file_uploads']}")
print(f"  - Auth/Identity Endpoints: {metrics['auth_endpoints']}")
print(f"  - Deprecated Endpoints: {metrics['deprecated']}")
print("=" * 30)