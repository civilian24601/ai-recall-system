from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route('/predict', methods=['POST'])
def predict():
    """Handles a machine learning model prediction request."""
    data = request.get_json()
    result = model.predict(data["input"])  # ❌ model is not defined, causes NameError
    return jsonify({"prediction": result})

if __name__ == "__main__":
    app.run(debug=True)
