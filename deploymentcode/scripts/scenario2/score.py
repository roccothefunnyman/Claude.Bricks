"""Scoring script for the .ldr validator endpoint."""
import json
import mlflow
import numpy as np
import os


def init():
    global model
    model_path = os.path.join(os.environ["AZUREML_MODEL_DIR"], "model")
    model = mlflow.sklearn.load_model(model_path)


def run(raw_data):
    data = json.loads(raw_data)
    features = np.array([[
        data["overhang_ratio"],
        data["collision_count"],
        data["height_to_base_ratio"],
        data["layer_density"],
    ]])
    prediction = model.predict(features)
    # IsolationForest: -1 = anomaly, 1 = normal
    # RandomForest: 0 = pass, 1 = fail
    result = "fail" if prediction[0] == -1 or prediction[0] == 1 else "pass"
    return json.dumps({"prediction": result})
