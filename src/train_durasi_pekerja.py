import pandas as pd
import joblib
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import mean_absolute_error

# Load data
df = pd.read_csv("data/dataset_durasi_pekerja.csv")

# Encode kategori
encoder_jenis = LabelEncoder()
encoder_cuaca = LabelEncoder()

df["jenis_proyek"] = encoder_jenis.fit_transform(df["jenis_proyek"])
df["cuaca"] = encoder_cuaca.fit_transform(df["cuaca"])

X = df.drop(["durasi_hari", "jumlah_pekerja"], axis=1)
y_durasi = df["durasi_hari"]
y_pekerja = df["jumlah_pekerja"]

# Split
X_train, X_test, y_d_train, y_d_test = train_test_split(X, y_durasi, test_size=0.2)
_, _, y_p_train, y_p_test = train_test_split(X, y_pekerja, test_size=0.2)

# Train model
model_durasi = RandomForestRegressor()
model_pekerja = RandomForestRegressor()

model_durasi.fit(X_train, y_d_train)
model_pekerja.fit(X_train, y_p_train)

# Evaluate
print("MAE Durasi:", mean_absolute_error(y_d_test, model_durasi.predict(X_test)))
print("MAE Pekerja:", mean_absolute_error(y_p_test, model_pekerja.predict(X_test)))

# Save
joblib.dump(model_durasi, "model_durasi.pkl")
joblib.dump(model_pekerja, "model_pekerja.pkl")
joblib.dump(encoder_jenis, "encoder_jenis_proyek.pkl")
joblib.dump(encoder_cuaca, "encoder_cuaca.pkl")

print("Model durasi & pekerja disimpan")
