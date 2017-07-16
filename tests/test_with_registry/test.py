import subprocess
import http.client
import json
import time
print('Starting registry..')
reg = subprocess.Popen('./run_reg.sh',shell=True)
print('starting service A')
servicea = subprocess.Popen('./run_serviceA.sh', shell=True)
print('starting service B')
serviceb = subprocess.Popen('./run_serviceB.sh', shell=True)

try:
    conn = http.client.HTTPSConnection("localhost", 8001)
    result = conn.request('GET','/serviceA/1/').getresponse()
    if result.status == 200:
        print(json.loads(result.read()))
except Exception as e:
    print(e)

print('Cleaning...')
time.sleep(3)
servicea.kill()
serviceb.kill()
reg.kill()

