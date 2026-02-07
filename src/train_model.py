import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import mean_absolute_error
import joblib

df = pd.read_csv("data/dataset_sanggar_alam_v1.csv")

encoder = LabelEncoder()
df["jenis_proyek"] = encoder.fit_transform(df["jenis_proyek"])

X = df[
    [
        "jenis_proyek",
        "luas_m2",
        "tingkat_detail",
        "jumlah_pekerja",
        "durasi_hari",
        "jarak_km",
    ]
]

y = df["harga_akhir"]

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42
)

model = RandomForestRegressor(
    n_estimators=100,
    random_state=42
)

model.fit(X_train, y_train)

y_pred = model.predict(X_test)
mae = mean_absolute_error(y_test, y_pred)

print(f"MAE (rata-rata selisih): Rp {int(mae):,}")

joblib.dump(model, "model_harga.pkl")
joblib.dump(encoder, "encoder_jenis_proyek.pkl")

print("✅ Model berhasil disimpan")
