from fastapi import FastAPI
import joblib
import pandas as pd

app = FastAPI(title="Sanggar Alam - Estimasi Harga Proyek")

# Load model sekali saat server jalan
model = joblib.load("model_harga.pkl")
encoder = joblib.load("encoder_jenis_proyek.pkl")

@app.get("/")
def root():
    return {"message": "API Sanggar Alam aktif 🚀"}

@app.post("/predict")
def predict(data: dict):
    df = pd.DataFrame([data])
    df["jenis_proyek"] = encoder.transform(df["jenis_proyek"])
    hasil = model.predict(df)
    return {"estimasi_harga": int(hasil[0])}
