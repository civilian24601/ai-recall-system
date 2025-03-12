def nested_function(x, y):
    def inner(z):
        return x / z if z else "error"  # TypeError potential
    return inner(y) + str(y)  # ValueError potential

def process_data(data):
    return data["key"]  # KeyError potential
