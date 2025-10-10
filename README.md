# TikTok Comment Scraper

Sebuah skrip Python sederhana untuk mengambil (scrape) semua komentar dari sebuah video TikTok menggunakan Selenium.

## Fitur

- Mengambil semua komentar (username dan isi komentar) dari satu URL video TikTok.
- Menyimpan hasil dalam format **CSV** (`tiktok_comments.csv`) dan **JSON** (`tiktok_comments.json`).
- Menggunakan profil browser Edge yang sudah ada untuk menangani login secara otomatis (jika Anda sudah login ke TikTok di browser).
- Mudah dijalankan melalui terminal (command line).

## Persyaratan

Sebelum memulai, pastikan Anda sudah menginstal:
1.  [Python 3](https://www.python.org/downloads/)
2.  Browser [Microsoft Edge](https://www.microsoft.com/edge)
3.  `pip` (biasanya sudah terinstal bersama Python)

## 1. Instalasi & Konfigurasi

Ikuti langkah-langkah ini untuk menyiapkan proyek.

**a. Instal Library Python yang Dibutuhkan**

Buka terminal atau Command Prompt, lalu jalankan perintah berikut untuk menginstal `pandas` dan `selenium`:
```bash
pip install pandas selenium
```

**b. Konfigurasi Profil Browser Edge**

Skrip ini perlu tahu lokasi profil Edge Anda agar bisa berjalan seolah-olah Anda yang membukanya (termasuk menggunakan login TikTok Anda).

1.  Buka browser **Microsoft Edge**.
2.  Ketik `edge://version` di address bar dan tekan Enter.
3.  Cari baris **"Profile path"**. Alamatnya akan terlihat seperti ini:
    `C:\Users\NamaAnda\AppData\Local\Microsoft\Edge\User Data\Default`
4.  Buka file `tiktok_comment_scraper.py` dengan teks editor.
5.  Cari dan edit dua baris berikut sesuai dengan path profil Anda:

    ```python
    # GANTI sesuai profil Edge kamu
    EDGE_USER_DATA_DIR = r"C:\Users\Dell\AppData\Local\Microsoft\Edge\User Data"
    PROFILE_DIR = "Default"
    ```
    - `EDGE_USER_DATA_DIR` adalah bagian path **sebelum** `\Default`.
    - `PROFILE_DIR` adalah nama folder profilnya (biasanya `Default` atau `Profile 1`, `Profile 2`, dst).

## 2. Cara Penggunaan

1.  Pastikan `msedgedriver.exe` berada di dalam folder `Edge`.
2.  Buka terminal atau Command Prompt di dalam folder proyek ini.
3.  Jalankan skrip dengan perintah:
    ```bash
    python tiktok_comment_scraper.py
    ```
4.  Saat diminta, masukkan URL video TikTok yang ingin Anda scrape, lalu tekan Enter.
    ```
    Masukkan URL video TikTok: https://www.tiktok.com/@username/video/1234567890123456789
    ```
5.  Tunggu hingga proses selesai. Browser Edge akan terbuka dan melakukan scraping secara otomatis.

## 3. Hasil (Output)

Setelah selesai, Anda akan menemukan dua file baru di folder proyek:
- **`tiktok_comments.csv`**: Berisi data komentar dalam format tabel.
- **`tiktok_comments.json`**: Berisi data komentar dalam format JSON.
