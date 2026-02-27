# 👮 imageCop — Duplicate Image Detector

> ⚠️ **Archived project.** This repository is no longer actively maintained and is open-sourced for reference and learning purposes.

**imageCop** is a desktop GUI tool that scans a folder and detects duplicate images. Point it at a directory, and it finds what your eyes would miss — identical or near-identical images wasting your storage.

---

## ✨ Features

- 🖼️ Scans a folder and identifies duplicate images
- 🖥️ Simple graphical interface — no command line needed
- 📦 Available as a standalone executable (no Python install required)
- ⚡ Built with Python and compiled with PyInstaller

---

## 🚀 Getting Started

### Option 1 — Run the executable (easiest)

Download the `main` binary from the repository and run it directly. No dependencies needed.

On Windows, you can also use the provided PowerShell script:

```powershell
.\main.ps1
```

### Option 2 — Run from source

**Prerequisites:** Python 3.x

```bash
# Clone the repository
git clone https://github.com/jdalmeida/imageCop.git
cd imageCop

# Install dependencies
pip install -r requirements.txt

# Run the app
python main.py
```

---

## 🛠️ Build from source

This project uses [PyInstaller](https://pyinstaller.org/) to generate a standalone executable.

```bash
pyinstaller imagecop.spec
```

The compiled binary will be available in the `dist/` folder.

---

## 🗂️ Project Structure

```
imageCop/
├── main.py               # App entry point
├── image_comparator.py   # Duplicate detection logic
├── imagecop.spec         # PyInstaller build config
├── main                  # Pre-compiled binary
└── main.ps1              # PowerShell run script (Windows)
```

---

## 📄 License

This project is open-sourced under the [MIT License](LICENSE).
