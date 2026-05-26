import os
import sys

import customtkinter
import PyInstaller.__main__


def build_executable():
    print("=== Invoice Designer - Build Script ===")

    customtkinter_dir = os.path.dirname(customtkinter.__file__)
    print(f"Detected customtkinter path: {customtkinter_dir}")

    templates_dir = "templates"
    if not os.path.exists(templates_dir):
        print(f"Error: '{templates_dir}' directory not found in current folder.")
        sys.exit(1)

    print("Configuring asset bundling...")

    customtkinter_data = f"{customtkinter_dir};customtkinter"
    templates_data = f"{templates_dir};templates"

    pyinstaller_args = [
        "app.py",
        "--name=Invoice Designer",
        "--onefile",
        "--noconsole",
        f"--add-data={customtkinter_data}",
        f"--add-data={templates_data}",
        "--clean",
    ]

    print("\nRunning PyInstaller compiler...")
    print(f"Arguments: {' '.join(pyinstaller_args)}")

    try:
        PyInstaller.__main__.run(pyinstaller_args)

        # Verify success
        exe_path = os.path.join("dist", "Catering Fajar Invoice Designer.exe")
        if os.path.exists(exe_path):
            print("\n" + "=" * 50)
            print(" BUILD COMPLETED SUCCESSFULLY!")
            print("=" * 50)
            print(
                f"Your standalone executable is ready at:\n--> {os.path.abspath(exe_path)}"
            )
            print("=" * 50)
        else:
            print("\nError: Build completed but executable was not found in 'dist'.")

    except Exception as e:
        print(f"\nAn error occurred during packaging: {e}")
        sys.exit(1)


if __name__ == "__main__":
    build_executable()
