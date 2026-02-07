import joblib
import pandas as pd

model = joblib.load("model_harga.pkl")
encoder = joblib.load("encoder_jenis_proyek.pkl")

data_baru = {
    "jenis_proyek": "kolam",
    "luas_m2": 30,
    "tingkat_detail": 4,
    "jumlah_pekerja": 3,
    "durasi_hari": 15,
    "jarak_km": 20
}

df = pd.DataFrame([data_baru])
df["jenis_proyek"] = encoder.transform(df["jenis_proyek"])


hasil = model.predict(df)

print(f"💰 Estimasi Harga Proyek: Rp {int(hasil[0]):,}")
