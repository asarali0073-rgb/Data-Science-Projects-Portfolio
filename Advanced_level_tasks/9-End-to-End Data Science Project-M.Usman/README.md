# Product Discount Predictor

A Flask web app that estimates a product discount from its category, actual
price, rating, and rating count. The estimate is based on the bundled Amazon
product dataset and is not a guaranteed offer.

## Requirements

- Python 3.10 or newer
- Flask, installed from `requirements.txt`

## Run locally

From this directory, create and activate a virtual environment, install the
dependencies, and start the app:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python app.py
```

Open <http://127.0.0.1:5000> in your browser. The `/health` endpoint returns
the app health status, and `/predict` accepts the prediction form or a JSON
request.

## Run tests

```powershell
python -m unittest discover -s tests
```

## Retrain the model

The app uses the lightweight `discount_model.json` model. To regenerate it
from `amazon.csv`, run:

```powershell
python train_model.py
```

The app loads this JSON model using Python's standard library and does not
require scikit-learn, SciPy, pandas, or joblib at runtime.

## Input validation

Prices must be positive, ratings must be between 0 and 5, rating counts must
be non-negative whole numbers, and the category must be present in the
training data.
