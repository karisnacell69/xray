# VLESS Panel

Panel manajemen user VLESS berbasis Python Flask.

## Fitur
- Login admin
- Tambah/hapus user VLESS
- Generate link VLESS otomatis
- Sync konfigurasi Xray
- Status aktif/expired user

## Cara Install (Termux)

```bash
pkg update && pkg install python xray cloudflared
pip install flask
git clone https://github.com/karisnacell69/xray.git
cd xray
python panel.py
```

## Login Default
- Username: `admin`
- Password: `admin`

## Domain
`anugerah-ternak-sejagad.xyz`
