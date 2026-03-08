"""Scoring script for the facade classifier endpoint."""
import json
import mlflow
import numpy as np
import os
from PIL import Image
import io
import base64


def init():
    global model
    model_path = os.path.join(os.environ["AZUREML_MODEL_DIR"], "model")
    model = mlflow.sklearn.load_model(model_path)


def run(raw_data):
    data = json.loads(raw_data)

    if "image_base64" in data:
        img_bytes = base64.b64decode(data["image_base64"])
        img = Image.open(io.BytesIO(img_bytes)).convert("RGB").resize((64, 64))
        features = np.array(img).flatten().reshape(1, -1)
    elif "features" in data:
        features = np.array(data["features"]).reshape(1, -1)
    else:
        return json.dumps({"error": "Provide 'image_base64' or 'features'"})

    prediction = model.predict(features)
    return json.dumps({"prediction": prediction[0]})
