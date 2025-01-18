#!/usr/bin/env python3
"""
===============================================================================
Script Name: sys_info.py
Description: Collects detailed system information, including OS details, CPU
             specifications, disk usage, and CUDA GPU information, and saves
             it to a TOML configuration file.
Author:      Reiyo
Email:       reiyo@sparrowup.com
Version:     1.1.0
Date:        2025-01-17
License:     MIT License
===============================================================================

Copyright (c) 2025 Reiyo

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
THE SOFTWARE.
===============================================================================
"""

import platform
import os
import sys
import toml
import psutil
from cpuinfo import get_cpu_info
from shutil import disk_usage
import logging
import argparse

# Attempt to import pynvml for CUDA information
try:
    import pynvml
    NVML_AVAILABLE = True
except ImportError:
    NVML_AVAILABLE = False

# Configure logging
logging.basicConfig(
    filename='sys_info.log',
    filemode='a',
    format='%(asctime)s - %(levelname)s - %(message)s',
    level=logging.DEBUG
)

def get_system_info():
    """
    Gathers comprehensive system information.
    
    Returns:
        dict: A dictionary containing system information.
    """
    logging.info("Starting to gather system information.")
    system_info = {
        "OS": platform.system(),
        "OS_Version": platform.version(),
        "OS_Release": platform.release(),
        "Architecture": platform.architecture()[0],
        "Machine": platform.machine(),
        "Processor": platform.processor(),
        "Python_Version": sys.version.split()[0],
        "Python_Executable": sys.executable,
        "Environment_Variables": os.environ.get("PATH", "").split(os.pathsep),
    }

    # Disk Usage Information
    try:
        usage = disk_usage('/')
        percentage_used = (usage.used / usage.total) * 100 if usage.total > 0 else 0
        system_info["Disk_Usage"] = {
            "Total": f"{usage.total / (1024 ** 3):.2f} GB",
            "Used": f"{usage.used / (1024 ** 3):.2f} GB",
            "Free": f"{usage.free / (1024 ** 3):.2f} GB",
            "Percentage_Used": f"{percentage_used:.2f}%",
        }
        logging.debug(f"Disk usage: {system_info['Disk_Usage']}")
    except Exception as e:
        system_info["Disk_Usage"] = f"Error retrieving disk usage: {e}"
        logging.error(f"Error retrieving disk usage: {e}")

    # Detailed CPU Information
    try:
        cpu_info = get_cpu_info()
        freq = psutil.cpu_freq()
        system_info["CPU_Details"] = {
            "Brand": cpu_info.get("brand_raw", "N/A"),
            "Arch": cpu_info.get("arch", "N/A"),
            "Bits": cpu_info.get("bits", "N/A"),
            "Count": psutil.cpu_count(logical=False),
            "Logical_Count": psutil.cpu_count(logical=True),
            "Frequency_MHz": freq._asdict() if freq else "N/A",
            "Flags": cpu_info.get("flags", []),
            "Cache_Size": cpu_info.get("cache_size", "N/A"),
            "L2_Cache_Size": cpu_info.get("l2_cache_size", "N/A"),
            "L3_Cache_Size": cpu_info.get("l3_cache_size", "N/A"),
        }
        logging.debug(f"CPU details: {system_info['CPU_Details']}")
    except Exception as e:
        system_info["CPU_Details"] = f"Error retrieving CPU details: {e}"
        logging.error(f"Error retrieving CPU details: {e}")

    # CUDA Information
    if NVML_AVAILABLE:
        try:
            pynvml.nvmlInit()
            device_count = pynvml.nvmlDeviceGetCount()
            cuda_info = {
                "CUDA_Available": device_count > 0,
                "Devices": []
            }
            for i in range(device_count):
                handle = pynvml.nvmlDeviceGetHandleByIndex(i)
                device_name = pynvml.nvmlDeviceGetName(handle)
                # Ensure device_name is a string
                if isinstance(device_name, bytes):
                    device_name = device_name.decode('utf-8')
                device = {
                    "Index": i,
                    "Name": device_name,
                    "Memory_Total_MB": pynvml.nvmlDeviceGetMemoryInfo(handle).total // (1024 ** 2),
                    "Memory_Free_MB": pynvml.nvmlDeviceGetMemoryInfo(handle).free // (1024 ** 2),
                    "Memory_Used_MB": pynvml.nvmlDeviceGetMemoryInfo(handle).used // (1024 ** 2),
                    "GPU_Utilization_Percent": pynvml.nvmlDeviceGetUtilizationRates(handle).gpu,
                    "Temperature_C": pynvml.nvmlDeviceGetTemperature(handle, pynvml.NVML_TEMPERATURE_GPU),
                }
                cuda_info["Devices"].append(device)
                logging.debug(f"CUDA Device {i}: {device}")
            pynvml.nvmlShutdown()
            system_info["CUDA_Info"] = cuda_info
            logging.info("CUDA information gathered successfully.")
        except pynvml.NVMLError as e:
            system_info["CUDA_Info"] = f"Error retrieving CUDA information: {e}"
            logging.error(f"Error retrieving CUDA information: {e}")
        except Exception as e:
            system_info["CUDA_Info"] = f"Unexpected error: {e}"
            logging.error(f"Unexpected error while retrieving CUDA information: {e}")
    else:
        system_info["CUDA_Info"] = "pynvml module not installed. CUDA information not available."
        logging.warning("pynvml module not installed. CUDA information not available.")

    logging.info("System information gathering completed.")
    return system_info

def save_to_toml(system_info, filename="config.toml"):
    """
    Saves the system information to a TOML file.

    Args:
        system_info (dict): The system information dictionary.
        filename (str): The output TOML file name.
    """
    config = {"system_info": system_info}
    try:
        with open(filename, "w") as toml_file:
            toml.dump(config, toml_file)
        logging.info(f"System information successfully saved to {filename}.")
        print(f"System information saved to {filename}")
    except Exception as e:
        logging.error(f"Failed to save system information to {filename}: {e}")
        print(f"Failed to save system information to {filename}: {e}")

def main():
    """
    The main function that orchestrates the gathering and saving of system information.
    """
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description="System Information Collector")
    parser.add_argument(
        '-o', '--output',
        type=str,
        default='config.toml',
        help='Output TOML file name (default: config.toml)'
    )
    args = parser.parse_args()

    logging.info("Script started.")
    
    # Gather system information
    system_info = get_system_info()
    
    # Save to TOML
    save_to_toml(system_info, args.output)
    
    logging.info("Script completed successfully.")

if __name__ == "__main__":
    main()

"""
===============================================================================
End of sys_info.py
===============================================================================
"""