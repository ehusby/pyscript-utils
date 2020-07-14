#!/bin/bash

#SBATCH --time 1:00:00
#SBATCH --nodes 1
#SBATCH --ntasks 2
#SBATCH --mem=5G

#SBATCH -o %x.o%j

#CONDOPT_SBATCH --mail-type=FAIL,END IF %EMAIL
#CONDOPT_SBATCH --mail-user=%EMAIL IF type(%EMAIL) is str


## NOTE: Look to 'body.sh' script for expected environment variable arguments

jobscript_path="$p0"
if [ -z "$jobscript_path" ]; then
    echo '$p0 variable (jobscript path) not set, exiting'
    exit 1
fi
jobscript_body="$(dirname "$jobscript_path")/body.sh"
if [ ! -f "$jobscript_body" ]; then
    echo "Job body script does not exist: ${jobscript_body}"
    exit 1
fi

$jobscript_body
