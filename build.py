import os
import sys
import platform
import subprocess
import shutil
import time

def compile_hexintegrity():
    print("==================================================")
    print("   HEXINTEGRITY - AUTOMATED BUILD PROTOCOL")
    print("==================================================")
    
    sys_os = platform.system()
    print(f">>> [1/4] SYSTEM DETECTED: {sys_os}")
    
    print(">>> [2/4] VERIFYING DEPENDENCIES...")
    subprocess.run(
        [sys.executable, "-m", "pip", "install", "pyinstaller", "customtkinter", "pillow"], 
        stdout=subprocess.DEVNULL, 
        stderr=subprocess.DEVNULL
    )

    print(">>> [3/4] FINALIZING PACKAGING: UI AND RESOURCE INTEGRATION...")
    
    icon_file = "icono.ico" if sys_os == "Windows" else "icono.png"
    
    if not os.path.exists(icon_file):
        print(f">>> [WARNING] ICON FILE '{icon_file}' NOT FOUND. COMPILING WITHOUT ICON.")
        command = ["pyinstaller", "--noconsole", "--onefile", "--name", "HexIntegrity", "main.py"]
    else:
        command = [
            "pyinstaller", 
            "--noconsole", 
            "--onefile", 
            "--name", "HexIntegrity", 
            f"--icon={icon_file}", 
            "main.py"
        ]
    
    result = subprocess.run(command, stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)
    
    if result.returncode != 0:
        print(">>> [ERROR] BUILD FAILED.")
        return

    print(">>> [4/4] CLEANING TEMPORARY DIRECTORIES...")
    time.sleep(2) 
    
    exe_name = "HexIntegrity.exe" if sys_os == "Windows" else "HexIntegrity"
    generated_path = os.path.join("dist", exe_name)
    final_path = os.path.join(os.getcwd(), exe_name)
    
    if os.path.exists(generated_path):
        if os.path.exists(final_path):
            os.remove(final_path) 
        shutil.move(generated_path, final_path)
    
    if os.path.exists("build"): 
        shutil.rmtree("build")
    if os.path.exists("dist"): 
        shutil.rmtree("dist")
    if os.path.exists("HexIntegrity.spec"): 
        os.remove("HexIntegrity.spec")

    print("\n==================================================")
    print(f">>> [SUCCESS] COMPILATION COMPLETED.")
    print(f">>> GENERATED FILE: {exe_name}")
    print("==================================================")
    if sys_os != "Windows":
        print(f">>> LINUX EXECUTION: sudo ./{exe_name}")

if __name__ == "__main__":
    compile_hexintegrity()