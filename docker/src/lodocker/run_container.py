import logging
import os
import platform
import subprocess

from pathlib import Path

import netifaces

from lodocker.colors import green_color
from lodocker.constants import Paths
from lodocker.helpers import Helpers

class RunContainer:
    def __init__(self):
        self.shared_doc_dir = "parts"
        self.git_root = Path(__file__).resolve().parents[3]
        logging.info(f"git_root: {self.git_root}")
        self.document_dir = self.git_root / self.shared_doc_dir
        # The home directory of the user in the Docker container
        self.docker_home = Paths.container_home
        # Directory where fonts are stored in the repository
        self.font_dir = self.git_root / "fonts"
        # Directory inside the Docker container where fonts will be stored
        self.docker_font_dir = "/usr/local/share/fonts"
        self.home = str(Path.home())
        self.display = self.get_display_variable()

    def doc_mount_string(self) -> str:
        return f"{self.document_dir}:{self.docker_home}/{self.shared_doc_dir}"

    def font_mount_string(self) -> str:
        return f"{self.font_dir}:{self.docker_font_dir}:ro"

    def get_display_variable(self) -> str:
        """Get the value of the DISPLAY environment variable.
        :return: The value of the DISPLAY environment variable.
        """
        if platform.system() == "Darwin":
            xquartz_ip = self.get_xquartz_ip()
            return f"{xquartz_ip}:0"
        elif platform.system() == "Linux":
            display = os.getenv("DISPLAY")
            if display is None:
                raise ValueError("DISPLAY environment variable is not set.")
            return display
        elif platform.system() == "Windows":
            if ip := self.get_suitable_ip():
                return f"{ip}:0.0"
            raise ValueError("Cannot determine the value of the DISPLAY environment variable.")
        else:
            raise ValueError(f"Unsupported platform: {platform.system()}")

    def get_suitable_ip(self) -> str | None:
        assert platform.system() == "Windows", "This function is only for Windows."
        if os.getenv("XSERVER_IP"):
            return os.getenv("XSERVER_IP")
        for interface in netifaces.interfaces():
            try:
                addrs = netifaces.ifaddresses(interface)
                ipv4_info = addrs.get(netifaces.AF_INET)
                if ipv4_info:
                    for addr_info in ipv4_info:
                        ip_address = addr_info.get('addr')
                        # Check if the IP address meets the criteria
                        if ip_address and not ip_address.startswith("169.254") and not ip_address == "127.0.0.1":
                            print(f"Automatically detected suitable IPv4 address: {ip_address}")
                            return ip_address
            except ValueError:
                continue

        print("No suitable IPv4 address found for the DISPLAY variable using automatic detection.")
        return None

    def get_xquartz_ip(self) -> str:
        """Get the IP address of the XQuartz server.
        :return: The IP address of the XQuartz server.
        """
        assert platform.system() == "Darwin", "This function is only for macOS."
        # Get the IP address of the XQuartz server
        # Check if environment variable XQUARTZ_IP is set by the user,
        # otherwise obtain it dynamically
        xquartz_ip = os.getenv("XQUARTZ_IP")
        if xquartz_ip is None:
            # Get the IP address of the XQuartz server using ipconfig
            # Change 'en0' to your active network interface
            xquartz_ip = subprocess.run(
                ["ipconfig", "getifaddr", "en0"], capture_output=True, text=True
            ).stdout.strip()
        return xquartz_ip

    def run_container(self, filename: str, image_name: str, exec_name: str):
        if platform.system() == "Linux":
            Helpers.run_command(["xhost", "+"])
        args = ["docker", "run"]
        args.extend(["-v", self.doc_mount_string()])
        args.extend(["-v", self.font_mount_string()])
        args.extend(["--rm"])
        args.extend(["-e", f"DISPLAY={self.display}"])
        if platform.system() == "Linux":
            args.extend(["-v", self.x11_socket_mount_string()])
        elif platform.system() == "Darwin":
            args.extend(["-v", self.xauthority_mount_string()])
        args.extend([image_name])
        args.extend([exec_name, f"{self.docker_home}/{self.shared_doc_dir}/{filename}"])
        command_str = " ".join(args)
        exit_code = Helpers.run_command(args)
        if platform.system() == "Linux":
            Helpers.run_command(["xhost", "-"])
        if exit_code == 0:
            logging.info(f"docker run for image {image_name} was successful.")
        else:
            logging.error(f"docker run for image {image_name} failed with exit code: {exit_code}.")
        print("NOTE: You can also run this \"docker run\" command manually like this: ")
        print(f"{green_color(command_str)}")

    def start_container(
        self,
        image_name: str,
        exec_name: str,
        lo_userdir: str,
    ) -> None:
        if platform.system() == "Linux":
            Helpers.run_command(["xhost", "+"])
        args = ["docker", "run"]
        args.extend(["-v", self.doc_mount_string()])
        args.extend(["-v", self.font_mount_string()])
        args.extend(["--rm"])
        args.extend(["-e", f"DISPLAY={self.display}"])
        # Default to 2002 if not set
        libreoffice_port = os.getenv("LIBREOFFICE_PORT", 2002)
        args.extend(["-e", f"LIBREOFFICE_PORT={libreoffice_port}"])
        # Default to 8080 if not set
        flask_port = os.getenv("FLASK_PORT", 8080)
        args.extend(["-e", f"FLASK_PORT={flask_port}"])
        args.extend(["-e", f"LIBREOFFICE_EXE={exec_name}"])
        args.extend(["-e", f"LIBREOFFICE_USERDIR={lo_userdir}"])
        args.extend(["-p", f"{flask_port}:{flask_port}"])
        if platform.system() == "Linux":
            args.extend(["-v", self.x11_socket_mount_string()])
        elif platform.system() == "Darwin":
            args.extend(["-v", self.xauthority_mount_string()])
        args.extend([image_name])
        command_str = " ".join(args)
        print("NOTE: You can also run this \"docker run\" command manually like this: ")
        print(f"{green_color(command_str)}")
        exit_code = Helpers.run_command(args)
        if platform.system() == "Linux":
            Helpers.run_command(["xhost", "-"])
        if exit_code == 0:
            logging.info(f"docker run for image {image_name} was successful.")
        else:
            logging.error(f"docker run for image {image_name} failed with exit code: {exit_code}.")

    def x11_socket_mount_string(self) ->str:
        return "/tmp/.X11-unix:/tmp/.X11-unix"

    def xauthority_mount_string(self) -> str:
        return f"{self.home}/.Xauthority:/home/docker-user/.Xauthority:rw"
