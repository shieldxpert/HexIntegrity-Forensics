# HexIntegrity Forensics Advanced Tactical Suite

![HexIntegrity Logo](HexIntegrity_forensics.png)

![HexIntegrity Forensics Interface](interfaz_win.png)

![HexIntegrity Forensics Interface](interfaz_lin.png)



![Python](https://img.shields.io/badge/Python-3.8%2B-FFD43B?style=for-the-badge&logo=python&logoColor=blue)
![Windows](https://img.shields.io/badge/Windows-0078D6?style=for-the-badge&logo=windows&logoColor=white)
![Linux](https://img.shields.io/badge/Linux-FCC624?style=for-the-badge&logo=linux&logoColor=black)
![Tkinter](https://img.shields.io/badge/CustomTkinter-UI-1572B6?style=for-the-badge&logo=figma&logoColor=white)
![Zenity](https://img.shields.io/badge/Zenity-POSIX_Dialogs-4EAA25?style=for-the-badge&logo=gnometerminal&logoColor=white)
![Security](https://img.shields.io/badge/Security-Forensic_Grade-red?style=for-the-badge&logo=security&logoColor=white)
![License](https://img.shields.io/badge/License-Proprietary-black?style=for-the-badge)

> *"The operating system tells you the file no longer exists; the hardware knows it’s lying to you. Welcome to ground zero of the data."*

---

## Overview and IR (Incident Response) Philosophy

HexIntegrity Forensics is an advanced digital forensics and auditing solution designed to operate directly on hardware and low-level storage. It completely bypasses logical file system abstractions (which may be manipulated or corrupted) to natively access physical magnetic or solid-state (NAND) blocks.

Developed under Live Forensics standards, the application features an asynchronous core decoupled from the graphical interface (customtkinter). This ensures the forensic engine processes data streams at maximum speed without freezing the UI or altering the metadata of original evidence at the incident scene.

---

## Core Architecture and Tactical Capabilities

```text
[RAW Device / Block] ──► [Hybrid Async Engine] ──► Cryptographic Wipe (3 Passes)
                                   │
                                   ├──► RAW Carving (Magic Numbers)
                                   ├──► Cryptographic Sealing (SHA-256)
                                   └──► Immutable Record (Audit Log)

1. RAW Acquisition and Iron Carving (Logical Table Bypass)
The recovery module does not trust the Master File Table (MFT) or OS logical descriptors. It uses direct hardware mapping via elevated kernel capabilities (\.\ in critical Windows architectures and native POSIX/dd calls in Linux) to parse Unallocated Space.

Heuristic Extraction: Analyzes binary streams byte-by-byte looking for Magic Numbers and Footers to isolate and reconstruct injected or deleted evidence:

JPEG: FF D8 FF ──► FF D9

PDF: %PDF- ──► %%EOF

PNG: 89 50 4E 47 0D 0A 1A 0A ──► 49 45 4E 44 AE 42 60 82

ZIP/DOCX: 50 4B 03 04 ──► 50 4B 05 06

OOM (Out-Of-Memory) Mitigation: Implements a static 1024 * 1024 bytes cyclic buffer to scan multi-terabyte mass storage media without compromising the analysis station's RAM.

2. Anti-Forensic Sanitization (Cryptographic Wipe)
Molecular structured data destruction designed to evade recovery by advanced laboratory analytical techniques or magnetic force microscopy.

Targeted Wipe: Overwrites the physical address occupied by files through a strict 3-pass complete protocol, injecting pure hardware-generated pseudo-random entropy (os.urandom). Breaks the physical node link before invoking logical deallocation (os.remove).

Slack Space & Drive Wiping: Massively injects dynamic 10 MB random vectors into the target drive's free sectors until it triggers a controlled physical cluster saturation failure (OSError: errno 28), guaranteeing the absolute erasure of ghost file remnants.

3. Cryptographic Sealing and Forensic Integrity
Guarantees the unalterable preservation of the chain of custody for external auditing processes and judicial ratifications.

Dynamic Hashing: Splits read streams into 8192-byte blocks to calculate the SHA-256 cryptographic signature in record time on forensic images (.RAW, .dd, .E01) or massive databases.

Local Blind Auditing: Immutably seals every interaction in the local HEX_SESSION_AUDIT.log file. Every USB device connection/disconnection, target drive selection, destructive protocol initiation, or critical system alert is recorded with atomic timestamps.

4. Heuristic Log Intelligence (Log Engine)
Rapid triage engine for identifying Indicators of Compromise (IoC) and data leaks.

Parallel analysis of plain configuration and log files (.txt, .log, .json, .ini, .conf).

Extracts and categorizes into independent reports: exposed IPv4 addressing, email strings, system anomalies (CRITICAL, FATAL, FAIL), and plaintext credential or access vector leaks.

Universal Installation and Deployment
The source code incorporates a native Auto-Assembly architecture. When executed in raw text (main.py), it dynamically injects its own dependencies, embeds the GUI images, and compiles a silent, standalone tactical binary named HexIntegrity_forensics.exe.

Step Zero: Environment Preparation (Mandatory)
Before interacting with the terminal, you must structure the files correctly on your hard drive so the packager can find them.

Create a new folder on your desktop (or wherever you prefer). For example: folder name.

Download and save strictly the following files from this repository inside that folder:

The main code: main.py

Icon resources: icono.ico and icono.png

UI resources: interfaz_win.png and interfaz_lin.png

Control buttons: btn_min_off.png, btn_min_on.png, btn_cerrar_off.png, btn_cerrar_on.png

Windows Deployment (CMD)
Open your Windows Command Prompt (CMD).

Use the cd (Change Directory) command to navigate to the folder you just created. Make sure to use quotes if your folder name has spaces. Replace the example with your actual path: cd "C:\Users\User\Desktop\folder name"

Execute the plaintext file to initialize the automated compilation phase: python main.py

The engine will detect the absence of the binary and execute the background assembly phase:

>>> [HEXINTEGRITY] INITIATING AUTO-ASSEMBLY FUNCTION...
>>> [1/3] Installing dependencies in the background...
>>> [2/3] Compiling forensic engine (Please wait 1-2 minutes)...
>>> [3/3] Extracting final executable and cleaning up traces...

Close the terminal. In your folder, you will see the new binary HexIntegrity_forensics.exe.

Double-click on it. Windows will intercept the call via UAC requesting Administrator Permissions. Accept to grant the engine the NT AUTHORITY\SYSTEM privilege and evade the file system logical layer.

Linux Deployment (WSL, Manjaro, Ubuntu, Debian)

In UNIX distributions, disk mapping is performed directly on the root directory or mount points. To deploy the graphical interface for native menus, installing the zenity dependency is mandatory.

Open the terminal and install the system dependencies according to your distribution:

Debian/Ubuntu/Mint/WSL Base: sudo apt update && sudo apt install python3-pip python3-tk zenity -y

Arch/Manjaro Base: sudo pacman -Sy python-pip tk zenity --noconfirm

Install the Python graphical libraries:

pip install customtkinter pillow

Navigate to your working directory. If you are using Linux WSL inside Windows, remember that the C:\ hard drive is mounted at /mnt/c/: cd "/mnt/c/Users/User/Desktop/folder name"

Forensic Grade Execution: Launch the application using superuser privileges (sudo) to unlock the native dd pipe and allow RAW hardware read access: python3 main.py

Disclaimer of Liability
This software is a real, highly sensitive, and operational forensic cybersecurity tool. The destructive sanitization modules (WIPE FILE and WIPE DRIVE) eliminate binary bitstrings via direct low-level overwrite. There is no recycle bin, intermediate storage, or rollback option. The author is not responsible for accidental data loss resulting from negligent use or use outside of controlled forensic laboratory environments.

