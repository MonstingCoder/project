# 🚀 User Management API  
Sebuah layanan API berbasis **FastAPI**, **SQLAlchemy**, dan **Pydantic** yang menyediakan fitur manajemen pengguna lengkap — mulai dari registrasi, update, hingga validasi data tingkat lanjut seperti hashing password, validasi nomor telepon, serta timestamp otomatis.

---

## ✨ Fitur Utama

- 🔐 **Hashing password otomatis** menggunakan Argon2  
- 📞 **Validasi nomor telepon** (wajib diawali `08`)  
- 📧 **Email unik dan tervalidasi**  
- 🛠 **CRUD User** (Create, Read, Update, Delete)  
- ⚡ **Partial update (PATCH)**  
- 🗂 **Struktur model bersih**: SQLAlchemy + Pydantic  
- 🕒 **Timestamp otomatis** (`created_at`, `updated_at`)  
- 🐘 Dukungan database: SQLite, PostgreSQL, MySQL  

---

## 📁 Struktur Proyek

```text
project/
│
├── app/
│   ├── database/
│   │   ├── models.py
│   │   ├── conn.py
│   │   └── **init**.py
│   │
│   ├── routers/
│   │   └── users.py
│   │
│   ├── helpers/
│   │   └── default_e_h.py
│   │
│   ├── main.py
│   └── schema.py
│
├── requirements.txt
└── README.md
```

---

## 🧩 Instalasi

### 1️⃣ Clone repo
```bash
git clone https://github.com/monstingcoder/project.git
cd your-project

```

### 2️⃣ Buat virtual environment

```bash
python -m venv venv
source venv/bin/activate   # Linux/Mac
venv\Scripts\activate      # Windows
```

### 3️⃣ Install dependensi

```bash
pip install -r requirements.txt
```

---

## ▶️ Menjalankan Aplikasi

```bash
uvicorn app.main:app --reload
```

Akses API di:

👉 [http://localhost:8000](http://localhost:8000)
👉 Swagger Docs: [http://localhost:8000/docs](http://localhost:8000/docs)

---

## 📡 Contoh Endpoint

### 🔹 Registrasi User (POST)

```
POST /users
```

### 🔹 Update User (PATCH)

```
PATCH /users/{id}
```

Body berisi field yang ingin diperbarui:

```json
{
  "username": "monsco_dev",
  "email": "example@gmail.com"
}
```

### 🔹 Mendapatkan User

```
GET /users/{id}
```

### 🔹 Menghapus User

```
DELETE /users/{id}
```

---

## 🔐 Validasi Otomatis

### ✔ Password

* Huruf besar
* Huruf kecil
* Angka
* Simbol
* Minimal 8 karakter
* Terenkripsi via Argon2

### ✔ Nomor Telepon

* Harus mulai dengan `08`
* Panjang minimal 10, maksimal 13 digit

---

## 🛠 Teknologi yang Digunakan

* **FastAPI** – Web framework
* **SQLAlchemy ORM** – Manajemen database
* **Pydantic v2** – Validasi dan serialisasi
* **Argon2 (pwdlib)** – Hashing password modern
* **Uvicorn** – Server ASGI

---

## 🤝 Kontribusi

Pull request sangat diterima!
Pastikan kode tetap rapi, diberi komentar, dan mengikuti gaya penulisan PEP8.

---

## 📜 Lisensi

Distribusi mengikuti lisensi MIT — silakan gunakan dan modifikasi sesuka hati.

---

## 💬 Kontak

Jika ingin berdiskusi atau butuh bantuan tambahan, silakan buka issue atau DM saya.
Selamat ngoding! 🚀🔥

---
