import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import mean_absolute_error
import joblib

# Load dataset
df = pd.read_csv("data/dataset_sanggar_alam_v1.csv")

# Encoder
encoder = LabelEncoder()
df["jenis_proyek"] = encoder.fit_transform(df["jenis_proyek"])

print("Jenis proyek dikenal model:", encoder.classes_)

# Fitur input (samakan dengan API!)
X = df[
    [
        "jenis_proyek",
        "luas_m2",
        "tingkat_detail",
        "cuaca",
        "jarak_km",
    ]
]

y = df["harga_akhir"]

# Split data
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42
)

# Training model
model = RandomForestRegressor(
    n_estimators=200,
    random_state=42
)

model.fit(X_train, y_train)

# Evaluasi
y_pred = model.predict(X_test)
mae = mean_absolute_error(y_test, y_pred)

print(f"MAE: Rp {int(mae):,}")

# Simpan
joblib.dump(model, "model_harga.pkl")
joblib.dump(encoder, "encoder_jenis_proyek.pkl")

print("Model & encoder disimpan")
