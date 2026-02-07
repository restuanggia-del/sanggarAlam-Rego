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

HARGA_MATERIAL = {
    "kolam": 500_000,
    "taman": 300_000,
    "gazebo": 700_000
}

UPAH_HARIAN = 150_000
TARIF_KM = 5_000

FAKTOR_DETAIL = {
    1: 1.0,
    2: 1.1,
    3: 1.2,
    4: 1.3,
    5: 1.5
}

FAKTOR_CUACA = {
    "cerah": 1.0,
    "mendung": 1.05,
    "hujan": 1.15
}

@app.get("/")
def root():
    return {"message": "API Sanggar Alam aktif"}

@app.post("/estimasi")
def estimasi(data: dict):

    jenis_proyek_asli = data["jenis_proyek"]
    cuaca_asli = data["cuaca"]

    df = pd.DataFrame([data])

    df["jenis_proyek"] = encoder_jenis.transform(df["jenis_proyek"])
    df["cuaca"] = encoder_cuaca.transform(df["cuaca"])

    fitur_ml = df[[
        "jenis_proyek",
        "luas_m2",
        "tingkat_detail",
        "cuaca",
        "jarak_km"
    ]]

    durasi = int(model_durasi.predict(fitur_ml)[0])
    pekerja = int(model_pekerja.predict(fitur_ml)[0])

    harga_material = (
        data["luas_m2"] *
        HARGA_MATERIAL.get(jenis_proyek_asli, 400_000)
    )

    biaya_upah = pekerja * UPAH_HARIAN * durasi
    biaya_transport = data["jarak_km"] * TARIF_KM

    subtotal = harga_material + biaya_upah + biaya_transport

    faktor_detail = FAKTOR_DETAIL[data["tingkat_detail"]]
    faktor_cuaca = FAKTOR_CUACA[cuaca_asli]
    
    DEFAULT_MARGIN = 0.20
    MAX_DISKON = 0.15

    estimasi_harga = int(subtotal * faktor_detail * faktor_cuaca)
    
    margin = DEFAULT_MARGIN
    nilai_margin = int(estimasi_harga * margin)
    
    harga_jual = estimasi_harga + nilai_margin
    
    diskon = data.get("diskon", 0)
    if diskon > MAX_DISKON:
        diskon = MAX_DISKON
    
    nilai_diskon = int(harga_jual * diskon)
    harga_final = harga_jual - nilai_diskon

    return {
    "biaya_produksi": estimasi_harga,
    "estimasi_durasi_hari": durasi,
    "estimasi_jumlah_pekerja": pekerja,

    "margin_persen": margin * 100,
    "nilai_margin": nilai_margin,
    "harga_sebelum_diskon": harga_jual,

    "diskon_persen": diskon * 100,
    "nilai_diskon": nilai_diskon,

    "harga_final": harga_final,

    "breakdown": {
        "material": harga_material,
        "upah": biaya_upah,
        "transport": biaya_transport,
        "subtotal": subtotal,
        "faktor_detail": faktor_detail,
        "faktor_cuaca": faktor_cuaca
    }
}
    