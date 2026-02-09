from fastapi import FastAPI
from fastapi.templating import Jinja2Templates
from fastapi.requests import Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
import joblib
import pandas as pd
import os
from pathlib import Path

from sqlalchemy import create_engine, Column, Integer, String, Float, func
from sqlalchemy.orm import declarative_base, sessionmaker
from datetime import datetime

BASE_DIR = Path(__file__).parent.parent
DATABASE_URL = "sqlite:///./app.db"

engine = create_engine(
    DATABASE_URL, connect_args={"check_same_thread": False}
)

SessionLocal = sessionmaker(bind=engine)

Base = declarative_base()

class HistoriEstimasi(Base):
    __tablename__ = "histori_estimasi"

    id = Column(Integer, primary_key=True, index=True)
    tanggal = Column(String, default=lambda: datetime.now().strftime("%Y-%m-%d %H:%M"))

    jenis_proyek = Column(String)
    luas_m2 = Column(Float)
    tingkat_detail = Column(Integer)
    cuaca = Column(String)
    jarak_km = Column(Float)

    durasi_hari = Column(Integer)
    jumlah_pekerja = Column(Integer)

    biaya_produksi = Column(Integer)
    harga_final = Column(Integer)
    diskon = Column(Float)
    
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Sanggar Alam - Estimasi Proyek")
templates = Jinja2Templates(directory="templates")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

try:
    model_harga = joblib.load(BASE_DIR / "model_harga.pkl")
    model_durasi = joblib.load(BASE_DIR / "model_durasi.pkl")
    model_pekerja = joblib.load(BASE_DIR / "model_pekerja.pkl")

    encoder_jenis = joblib.load(BASE_DIR / "encoder_jenis_proyek.pkl")
    encoder_cuaca = joblib.load(BASE_DIR / "encoder_cuaca.pkl")

    print("Jenis proyek dikenal encoder:", encoder_jenis.classes_)

except Exception as e:
    print(f"Warning: Gagal load model atau encoder: {e}")
    model_harga = None
    model_durasi = None
    model_pekerja = None
    encoder_jenis = None
    encoder_cuaca = None

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
    if not all([model_harga, model_durasi, model_pekerja, encoder_jenis, encoder_cuaca]):
        return {"error": "Model belum dimuat. Pastikan file .pkl ada di direktori root."}

    if data["jenis_proyek"] not in encoder_jenis.classes_:
        return {
            "error": f"jenis_proyek '{data['jenis_proyek']}' tidak dikenali",
            "valid_jenis_proyek": encoder_jenis.classes_.tolist()
        }

    if data["cuaca"] not in encoder_cuaca.classes_:
        return {
            "error": f"cuaca '{data['cuaca']}' tidak dikenali",
            "valid_cuaca": encoder_cuaca.classes_.tolist()
        }

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
    
    db = SessionLocal()

    histori = HistoriEstimasi(
        jenis_proyek=jenis_proyek_asli,
        luas_m2=data["luas_m2"],
        tingkat_detail=data["tingkat_detail"],
        cuaca=cuaca_asli,
        jarak_km=data["jarak_km"],
        durasi_hari=durasi,
        jumlah_pekerja=pekerja,
        biaya_produksi=estimasi_harga,
        harga_final=harga_final,
        diskon=diskon
    )

    db.add(histori)
    db.commit()
    db.close()

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

@app.get("/analitik/summary")
def analitik_summary():
    db = SessionLocal()

    total_proyek = db.query(func.count(HistoriEstimasi.id)).scalar()
    total_omzet = db.query(func.sum(HistoriEstimasi.harga_final)).scalar() or 0
    rata_rata_harga = db.query(func.avg(HistoriEstimasi.harga_final)).scalar() or 0

    db.close()

    return {
        "total_proyek": total_proyek,
        "total_omzet": int(total_omzet),
        "rata_rata_harga": int(rata_rata_harga)
    }

@app.get("/analitik/top-proyek")
def top_proyek():
    db = SessionLocal()

    data = (
        db.query(
            HistoriEstimasi.jenis_proyek,
            func.count(HistoriEstimasi.id).label("jumlah")
        )
        .group_by(HistoriEstimasi.jenis_proyek)
        .order_by(func.count(HistoriEstimasi.id).desc())
        .all()
    )

    db.close()

    return [
        {
            "jenis_proyek": row.jenis_proyek,
            "jumlah_proyek": row.jumlah
        }
        for row in data
    ]

@app.get("/analitik/harga")
def analitik_harga():
    db = SessionLocal()

    termahal = (
        db.query(HistoriEstimasi)
        .order_by(HistoriEstimasi.harga_final.desc())
        .first()
    )

    termurah = (
        db.query(HistoriEstimasi)
        .order_by(HistoriEstimasi.harga_final.asc())
        .first()
    )

    db.close()

    return {
        "termahal": {
            "jenis_proyek": termahal.jenis_proyek,
            "harga": termahal.harga_final
        } if termahal else None,

        "termurah": {
            "jenis_proyek": termurah.jenis_proyek,
            "harga": termurah.harga_final
        } if termurah else None
    }
    
@app.get("/histori")
def get_histori():
    db = SessionLocal()

    data = db.query(HistoriEstimasi).order_by(HistoriEstimasi.id.desc()).all()

    db.close()

    hasil = []
    for item in data:
        hasil.append({
            "id": item.id,
            "tanggal": item.tanggal,
            "jenis_proyek": item.jenis_proyek,
            "luas_m2": item.luas_m2,
            "tingkat_detail": item.tingkat_detail,
            "cuaca": item.cuaca,
            "jarak_km": item.jarak_km,
            "durasi_hari": item.durasi_hari,
            "jumlah_pekerja": item.jumlah_pekerja,
            "biaya_produksi": item.biaya_produksi,
            "harga_final": item.harga_final,
            "diskon": item.diskon
        })

    return hasil

@app.get("/analitik/chart/omzet-per-jenis")
def chart_omzet_per_jenis():
    db = SessionLocal()

    data = (
        db.query(
            HistoriEstimasi.jenis_proyek,
            func.sum(HistoriEstimasi.harga_final)
        )
        .group_by(HistoriEstimasi.jenis_proyek)
        .all()
    )

    db.close()

    labels = [d[0] for d in data]
    values = [d[1] for d in data]

    return {
        "labels": labels,
        "datasets": [
            {
                "label": "Total Omzet (Rp)",
                "data": values
            }
        ]
    }

@app.get("/analitik/chart/proyek-per-bulan")
def chart_proyek_per_bulan():
    db = SessionLocal()

    data = (
        db.query(
            func.substr(HistoriEstimasi.tanggal, 1, 7).label("bulan"),
            func.count(HistoriEstimasi.id)
        )
        .group_by("bulan")
        .order_by("bulan")
        .all()
    )

    db.close()

    labels = [d[0] for d in data]
    values = [d[1] for d in data]

    return {
        "labels": labels,
        "datasets": [
            {
                "label": "Jumlah Proyek",
                "data": values
            }
        ]
    }

@app.get("/analitik/chart/harga")
def chart_harga():
    db = SessionLocal()

    result = db.query(
        func.min(HistoriEstimasi.harga_final),
        func.avg(HistoriEstimasi.harga_final),
        func.max(HistoriEstimasi.harga_final),
    ).one()

    db.close()

    return {
        "labels": ["Termurah", "Rata-rata", "Termahal"],
        "datasets": [
            {
                "label": "Harga Proyek (Rp)",
                "data": [
                    result[0] or 0,
                    int(result[1] or 0),
                    result[2] or 0
                ]
            }
        ]
    }

@app.get("/form", response_class=HTMLResponse)
def form_page(request: Request):
    return templates.TemplateResponse("form.html", {"request": request})

@app.get("/admin", response_class=HTMLResponse)
def admin_page():
    db = SessionLocal()
    data = db.query(HistoriEstimasi).order_by(HistoriEstimasi.id.desc()).all()
    db.close()

    rows = ""
    for item in data:
        rows += f"""
        <tr class="hover:bg-emerald-50 transition">
            <td class="px-4 py-3 text-center">{item.tanggal}</td>
            <td class="px-4 py-3 text-center">{item.jenis_proyek}</td>
            <td class="px-4 py-3 text-center">{item.luas_m2}</td>
            <td class="px-4 py-3 text-center">{item.cuaca}</td>
            <td class="px-4 py-3 text-center">{item.durasi_hari} hari</td>
            <td class="px-4 py-3 text-center">{item.jumlah_pekerja}</td>
            <td class="px-4 py-3 text-center font-semibold text-emerald-700">
                Rp {item.harga_final:,}
            </td>
        </tr>
        """

    html = f"""
<!DOCTYPE html>
<html lang="id">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Admin Sanggar Alam</title>

  <script src="https://cdn.tailwindcss.com"></script>

  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">

  <style>
    body {{
      font-family: 'Inter', sans-serif;
    }}
  </style>
</head>

<body class="bg-gradient-to-br from-green-50 to-emerald-100 min-h-screen">
  <div class="max-w-7xl mx-auto px-6 py-10">

    <div class="mb-8 flex flex-col md:flex-row md:items-center md:justify-between gap-4">
      <div>
        <h1 class="text-3xl md:text-4xl font-bold text-emerald-700">
          🌿 Admin Sanggar Alam
        </h1>
        <p class="text-gray-600 mt-1">Histori Estimasi Proyek</p>
      </div>

      <div class="relative w-full md:w-80">
        <input
          type="text"
          id="searchInput"
          placeholder="Cari data..."
          class="w-full px-4 py-2 rounded-xl border border-gray-300 shadow-sm focus:outline-none focus:ring-2 focus:ring-emerald-500"
        />
      </div>
    </div>

    <div class="bg-white rounded-2xl shadow-lg overflow-hidden">
      <div class="overflow-x-auto">
        <table class="min-w-full text-sm">
          <thead class="bg-emerald-600 text-white">
            <tr>
              <th class="px-4 py-3 text-center">Tanggal</th>
              <th class="px-4 py-3 text-center">Jenis Proyek</th>
              <th class="px-4 py-3 text-center">Luas</th>
              <th class="px-4 py-3 text-center">Cuaca</th>
              <th class="px-4 py-3 text-center">Durasi</th>
              <th class="px-4 py-3 text-center">Pekerja</th>
              <th class="px-4 py-3 text-center">Harga Final</th>
            </tr>
          </thead>
          <tbody id="tableBody" class="divide-y divide-gray-200">
            {rows}
          </tbody>
        </table>
      </div>
    </div>

    <p class="text-center text-gray-500 text-sm mt-6">
      © 2026 Sanggar Alam — Dashboard Admin
    </p>
  </div>

  <script>
    const searchInput = document.getElementById('searchInput');
    const tableBody = document.getElementById('tableBody');

    searchInput.addEventListener('keyup', () => {{
      const filter = searchInput.value.toLowerCase();
      const rows = tableBody.getElementsByTagName('tr');

      for (let i = 0; i < rows.length; i++) {{
        const text = rows[i].innerText.toLowerCase();
        rows[i].style.display = text.includes(filter) ? '' : 'none';
      }}
    }});
  </script>
</body>
</html>
"""
    return html
