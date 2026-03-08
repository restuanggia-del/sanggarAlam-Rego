# Sanggar Alam — Sistem Estimasi Proyek

Aplikasi web berbasis **FastAPI** untuk menghitung estimasi biaya proyek Sanggar Alam secara otomatis.  
Dilengkapi dengan dashboard admin, form estimasi, dan sistem autentikasi pengguna.

---

## Cara Menjalankan Project

### 1. Clone Repository

```bash
git clone https://github.com/username/sanggar-alam.git
cd sanggar-alam
```

### 2. Buat Virtual Environment
```bash
python -m venv venvtory
```
Aktifkan Environment

#### Windows
```bash
venv\Scripts\activate
```
#### Mac / Linux
```bash
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install fastapi uvicorn sqlalchemy jinja2 passlib[bcrypt]
```

### 4. Jalankan Server
```bash
uvicorn app.main:app --reload
```

### 5. Buka di Browser
```bash
http://127.0.0.1:8000
```
