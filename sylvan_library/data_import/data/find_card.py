import subprocess
from data_import import _paths, _query

cmd = 'grep ' + _paths.json_data_path
ps = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)