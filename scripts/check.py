"""Run standard-library static checks and the complete Python suite."""
import argparse
import os
from pathlib import Path
import subprocess
import sys
ROOT=Path(__file__).resolve().parents[1]
if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--pipe",action="store_true",help="Use the HTTP parser without a network socket")
    args=parser.parse_args()
    env=os.environ.copy()
    if args.pipe:
        env["MEDCURA_HTTP_TRANSPORT"]="memory"
    for command in (["-m","tabnanny","apps"],["-m","compileall","-q","apps","scripts","tests","run.py"],["-m","unittest","discover","-s","tests","-v"]):
        subprocess.run([sys.executable,*command],cwd=ROOT,env=env,check=True)

