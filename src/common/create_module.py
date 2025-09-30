import os
import sys
import zipfile
import tempfile
import subprocess
import importlib
import shutil


class CreateModule:

    def __init__(self, logger=None):
        self._logger = logger
        self._instance_pool = {}
        self.project_dir = os.path.dirname(os.path.abspath(__file__))

    def create_package_and_remove_dir(self, dir_path: str):
        target_dir = dir_path
        print("Target dir:", target_dir)

        zip_dir = os.path.dirname(target_dir)
        zip_name = os.path.basename(target_dir) + ".zip"
        zip_path = os.path.join(zip_dir, zip_name)

        if os.path.exists(zip_path):
            os.remove(zip_path)

        init_file = os.path.join(target_dir, "__init__.py")
        if not os.path.exists(init_file):
            open(init_file, "a").close()

        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk(target_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, start=os.path.dirname(target_dir))
                    zipf.write(file_path, arcname)

            req_path = os.path.join(zip_dir, "requirements.txt")
            if os.path.exists(req_path):
                zipf.write(req_path, "requirements.txt")

        if os.path.exists(target_dir):
            shutil.rmtree(target_dir)

        print(f"Created {zip_path} and removed {target_dir}")

    def create_all_packages(self, base_dir: str):
        for name in os.listdir(base_dir):
            sub_dir = os.path.join(base_dir, name)
            if os.path.isdir(sub_dir):
                self.create_package_and_remove_dir(sub_dir)

    def register_zip_packages(self, zip_dir: str):
        if not os.path.isdir(zip_dir):
            raise ValueError(f"{zip_dir} is not a valid directory")

        for file in os.listdir(zip_dir):
            if file.endswith(".zip"):
                zip_path = os.path.join(zip_dir, file)
                if zip_path not in sys.path:
                    sys.path.insert(0, zip_path)
                    print(f"[INFO] Registered: {zip_path}")

        print("[INFO] sys.path 등록 완료")

    def install_requirements_from_module(self, module_path: str, req_name: str = "requirements.txt"):
        parts = module_path.split(".")

        zip_path = "/data/kelly/pycharm_projects/agent/src/" + os.path.join(*parts[:-1]) + ".zip"

        module_dir = parts[-2]
        req_path = f"{module_dir}/{req_name}"

        if not os.path.exists(zip_path):
            print(f"zip file not found: {zip_path}")
            return

        with zipfile.ZipFile(zip_path, "r") as zf:
            if req_path not in zf.namelist():
                print(f"{req_name} not found at {req_path} in {zip_path}")
                return

            content = zf.read(req_path).decode("utf-8")
            pkgs = [line.strip() for line in content.splitlines()
                    if line.strip() and not line.startswith("#")]

        to_install = []

        for pkg in pkgs:
            base_name = pkg.split("==")[0].split(">=")[0].split("<=")[0].split("~=")[0].strip()
            try:
                importlib.import_module(base_name)
                print(f"✅ {pkg} already installed, skipping")
            except ImportError:
                to_install.append(pkg)

        if not to_install:
            print("All requirements already satisfied.")
            return

        with tempfile.NamedTemporaryFile(delete=False, mode="w", suffix=".txt") as tmp:
            tmp.write("\n".join(to_install))
            tmp_path = tmp.name

        try:
            print("=============== start selective install ======================")
            subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", tmp_path])
        finally:
            print("=============== finish selective install ======================")
            os.remove(tmp_path)
