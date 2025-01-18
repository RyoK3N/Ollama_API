#!/bin/bash

# ==============================================================================
# Script Name: pipeline.py
# Description: This pipeline sets up ollama using Docker and serves ollama on port
# 11434 based on the device used to serve ollama(CPU/GPU(NVIDIA)). Also the functionality
# extends to being able to download model from ollama and run it on this port using API 
# calls from other terminals in the same network.
# Author:      Reiyo
# Email:       reiyo@sparrowup.com
# Version:     1.0.0
# Date:        2025-01-17
# License:     MIT License
# ==============================================================================
#
# ==============================================================================
# Copyright (c) 2025 Reiyo
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
# ==============================================================================


import os
import argparse
import toml  
import subprocess


#Run sys_info.py
def parse_args():
    parser = argparse.ArgumentParser(
        description='Run sys_info.py with specified configuration.'
    )
    parser.add_argument(
        '--sys_config',
        default='./config.toml',
        help='Path to the system configuration file (default: ./config.toml)'
    )
    args = parser.parse_args()
    return args

def run_scripts(script_path):
    """ 
        Runs various scripts created for specefic purposes inside the pipeline 
    
    """
    try:
        if not os.path.isfile(script_path):
            print(f"{script_path} does not exists , try cloning from git again")
            return False
        print(f"Running {script_path}")
        result = subprocess.run(['python',script_path],check=True,capture_output=True,text=True)
        print(result.stdout)
        print('Configuration File Generated.')
        return True
    except subprocess.CalledProcessError as e :
        print(f"An error occured while running {script_path} : ")
        print(e.stderr)
        return False
    except Exception as e:
        print(f"Unexpeced error: {e}")
        return False

if __name__ == "__main__":
    args = parse_args()
    fpath = args.sys_config 

    if os.path.exists(fpath):
        with open(fpath, 'r') as f:  
            config = toml.load(f)
        # Accessing the configuration safely
        try:
            cuda_available = config['system_info']['CUDA_Info']['CUDA_Available']
            print(f"CUDA Available: {cuda_available}")
        except KeyError as e:
            print(f"Configuration key missing: {e}")
    else:
        print(f"Configuration file does not exist at path: {fpath}")
        print(f'Running the system_info.py to generate Configuration file')
        print(f'Running...')
        config_gen = run_scripts('./sys_info.py')

    print("Step 2 : Load config.toml  ")
    with open('./config.toml','r') as f :
        config = toml.load(f)
    if config['system_info']['CUDA_Info']['CUDA_Available'] == True :
        cpu_flag = 0
        gpu_flag = 1  # Run on GPU 
    else :
        cpu_flag = 1  # Run on CPU
        gpu_flag = 0   

    print(f"cpu_flag :{cpu_flag}")
    print(f"gpu_flag :{gpu_flag}")
    

#Saves the system info in config.toml 
#python sys_info.py

#Load config.toml 
#Load the important parameters for running docker 

# with open('./config.toml','r') as f :
#     config = toml.load(f)

# if config['system_info']['CUDA_Info']['CUDA_Available'] = True :
#     cpu_flag = 0
#     gpu_flag = 1  # Run on GPU 
# else :
#     cpu_flag = 1  # Run on CPU
#     gpu_flag = 0   


#Run docker based on the requirements 



#Once docker successfully is installed and returns a flag==1 which states that docker is running


#Rnder UI for downloading the desired model 
#The UI should have the port that we are hosting the downloaded model on 

#Once the model is hosted , pind the model on that port to see if its hosted and running 

#Once true flag is returned .


#We can use the chat.py script to give request and response to the model 


