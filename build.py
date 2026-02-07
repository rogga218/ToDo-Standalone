import os
import subprocess
import sys
from pathlib import Path


def build_executable():
    """
    Builds the ToDo App executable using PyInstaller.
    """
    print("Starting build process...")

    # Ensure requirements are installed
    print("Installing dependencies...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "--upgrade", "pip"])
    subprocess.check_call(
        [
            sys.executable,
            "-m",
            "pip",
            "install",
            "--upgrade",
            "setuptools<81.0.0",
            "wheel",
        ]
    )
    subprocess.check_call(
        [sys.executable, "-m", "pip", "install", "-r", "requirements.txt"]
    )
    subprocess.check_call(
        [sys.executable, "-m", "pip", "install", "--upgrade", "pyinstaller"]
    )

    # Import config AFTER installing dependencies
    try:
        from src.config import Settings

        settings = Settings()
        app_name = settings.APP_NAME
        # Sanitize app name for filename (remove spaces, special chars)
        exe_name = "".join(x for x in app_name.title() if x.isalnum())
    except ImportError:
        print("Could not import settings, using default name.")
        app_name = "ToDo App"
        exe_name = "ToDoAppV2"

    print(f"Building {app_name} ({exe_name}.exe)...")

    # Define paths
    base_dir = Path(__file__).parent
    src_dir = base_dir / "src"
    main_script = src_dir / "main.py"
    assets_dir = src_dir / "assets"
    icon_path = assets_dir / "logo.png"  # Use logo as icon if ico doesn't exist

    dist_dir = base_dir / "dist"
    # work_dir = base_dir / "build"

    # Clean previous builds
    # shutil.rmtree(dist_dir, ignore_errors=True)
    # shutil.rmtree(work_dir, ignore_errors=True)

    # Prepare Icon
    icon_argument = []
    if icon_path.exists():
        icon_argument = ["--icon", str(icon_path)]
    elif (assets_dir / "logo.png").exists():
        # Try to convert PNG to ICO if Pillow is installed
        try:
            from PIL import Image

            print("Converting logo.png to logo.ico for build...")
            img = Image.open(assets_dir / "logo.png")
            # Convert to ICO
            icon_path = assets_dir / "logo.ico"
            img.save(icon_path, format="ICO")
            icon_argument = ["--icon", str(icon_path)]
        except ImportError:
            print(
                "Pillow not installed. Skipping icon conversion (Build will have default icon)."
            )
        except Exception as e:
            print(f"Failed to convert icon: {e}")

    # PyInstaller Command
    cmd = [
        "pyinstaller",
        "--name",
        exe_name,
        "--onefile",
        "--windowed",
        "--clean",
        "--add-data",
        f"{src_dir}{os.pathsep}src",
        "--add-data",
        f"{assets_dir}{os.pathsep}src/assets",
        # Hidden imports
        "--hidden-import",
        "uvicorn",
        "--hidden-import",
        "passlib.handlers.bcrypt",
        "--hidden-import",
        "pydantic_settings",
        "--hidden-import",
        "python-multipart",
        str(main_script),
    ] + icon_argument

    print(f"Running: {' '.join(cmd)}")
    subprocess.check_call(cmd)

    print("\nBuild Complete!")
    print(f"Executable is located at: {dist_dir / (exe_name + '.exe')}")


if __name__ == "__main__":
    build_executable()
