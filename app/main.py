from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import joblib
import pandas as pd

app = FastAPI(title="Sanggar Alam - Estimasi Proyek")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

model_harga = joblib.load("model_harga.pkl")
model_durasi = joblib.load("model_durasi.pkl")
model_pekerja = joblib.load("model_pekerja.pkl")

encoder_jenis = joblib.load("encoder_jenis_proyek.pkl")
encoder_cuaca = joblib.load("encoder_cuaca.pkl")

@app.get("/")
def root():
    return {"message": "API Sanggar Alam aktif"}

@app.post("/estimasi")
def estimasi(data: dict):
    df = pd.DataFrame([data])

    df["jenis_proyek"] = encoder_jenis.transform(df["jenis_proyek"])
    df["cuaca"] = encoder_cuaca.transform(df["cuaca"])

    fitur_dp = df[[
        "jenis_proyek",
        "luas_m2",
        "tingkat_detail",
        "cuaca",
        "jarak_km"
    ]]

    durasi = int(model_durasi.predict(fitur_dp)[0])
    pekerja = int(model_pekerja.predict(fitur_dp)[0])

    fitur_harga = pd.DataFrame([{
        "jenis_proyek": df["jenis_proyek"][0],
        "luas_m2": df["luas_m2"][0],
        "tingkat_detail": df["tingkat_detail"][0],
        "jumlah_pekerja": pekerja,
        "durasi_hari": durasi,
        "jarak_km": df["jarak_km"][0]
    }])

    harga = int(model_harga.predict(fitur_harga)[0])

    return {
        "estimasi_harga": harga,
        "estimasi_durasi_hari": durasi,
        "estimasi_jumlah_pekerja": pekerja
    }
    