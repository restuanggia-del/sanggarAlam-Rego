from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import joblib
import pandas as pd

app = FastAPI(title="Sanggar Alam - Estimasi Harga Proyek")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

model = joblib.load("model_harga.pkl")
encoder = joblib.load("encoder_jenis_proyek.pkl")

@app.get("/")
def root():
    return {"message": "API Sanggar Alam aktif"}

@app.post("/predict")
def predict(data: dict):
    df = pd.DataFrame([data])
    df["jenis_proyek"] = encoder.transform(df["jenis_proyek"])
    hasil = model.predict(df)
    return {"estimasi_harga": int(hasil[0])}
