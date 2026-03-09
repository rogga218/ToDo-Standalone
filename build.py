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
    subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
    subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements-build.txt"])

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
        exe_name = "ToDoApp"

    print(f"Building {app_name} ({exe_name}.exe)...")

    # Define paths
    base_dir = Path(__file__).parent
    src_dir = base_dir / "src"
    main_script = src_dir / "main.py"
    assets_dir = src_dir / "assets"

    dist_dir = base_dir / "dist"
    # work_dir = base_dir / "build"

    dist_path = dist_dir / (exe_name + ".exe")
    if dist_path.exists():
        try:
            print(f"Removing existing build: {dist_path}")
            os.remove(dist_path)
        except PermissionError:
            print(f"\nERROR: Permission denied when removing {dist_path.name}")
            print("Please make sure the application is closed and try again.")
            return

    # Prepare Icon
    icon_path_ico = assets_dir / "logo.ico"
    icon_path_png = assets_dir / "logo.png"
    icon_argument = []

    if icon_path_ico.exists():
        print(f"Found icon: {icon_path_ico}")
        icon_argument = ["--icon", str(icon_path_ico)]
    else:
        # Check for SVG first, then PNG
        icon_path_svg = assets_dir / "logo.svg"

        if icon_path_svg.exists():
            print("logo.ico not found, looking for logo.svg...")
            try:
                print("Installing svglib, reportlab, Pillow for icon conversion...")
                subprocess.check_call(
                    [
                        sys.executable,
                        "-m",
                        "pip",
                        "install",
                        "svglib",
                        "reportlab",
                        "Pillow",
                    ]
                )

                from PIL import Image
                from reportlab.graphics import renderPM
                from svglib.svglib import svg2rlg

                print("Converting logo.svg to logo.ico...")
                # SVG -> RL Drawing
                drawing = svg2rlg(str(icon_path_svg))

                if not drawing:
                    raise ValueError(f"Failed to load SVG: {icon_path_svg}")

                # RL Drawing -> PNG (temp)
                temp_png = assets_dir / "temp_logo.png"
                renderPM.drawToFile(drawing, str(temp_png), fmt="PNG")

                # PNG -> ICO
                img = Image.open(temp_png)
                img.save(icon_path_ico, format="ICO")

                # Cleanup
                if temp_png.exists():
                    os.remove(temp_png)

                icon_argument = ["--icon", str(icon_path_ico)]
                print("Successfully created logo.ico from logo.svg")
            except Exception as e:
                print(f"Failed to convert SVG icon: {e}")
                import traceback

                traceback.print_exc()

        elif icon_path_png.exists():
            print("logo.ico and logo.svg not found, looking for logo.png...")
            # Try to convert PNG to ICO
            try:
                print("Installing Pillow for icon conversion...")
                subprocess.check_call([sys.executable, "-m", "pip", "install", "Pillow"])
                from PIL import Image

                print("Converting logo.png to logo.ico...")
                img = Image.open(icon_path_png)
                img.save(icon_path_ico, format="ICO")
                icon_argument = ["--icon", str(icon_path_ico)]
            except Exception as e:
                print(f"Failed to convert PNG icon: {e}")
                print("Build will proceed without a specific icon.")
        else:
            print("No logo.ico, logo.svg, or logo.png found. Build will proceed without an icon.")

    cmd = [
        sys.executable,
        "-m",
        "PyInstaller",
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
        "python_multipart",  # Correct module name with underscore
        "--hidden-import",
        "_cffi_backend",
        "--hidden-import",
        "cffi",
        "--hidden-import",
        "PySide6.QtWebEngineWidgets",
        str(main_script),
    ] + icon_argument

    print(f"Running: {' '.join(cmd)}")
    subprocess.check_call(cmd)

    print("\nBuild Complete!")
    print(f"Executable is located at: {dist_dir / (exe_name + '.exe')}")


if __name__ == "__main__":
    build_executable()
