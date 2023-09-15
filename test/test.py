# todo
    # 1. run test with -c and -z (user, time)
    # 2. get running pod and log with current requests
    

import os, sys, math, time, datetime
import argparse, sys, subprocess
import yaml
from threading import Thread

parser = argparse.ArgumentParser()
parser.add_argument('-u', help=' : Target url')
parser.add_argument('-rtime', help=' : Duration each test', default='30')
args = parser.parse_args()

is_thread_run = False
cur_requests = 0

## total test case = 4 * 3 * 5 * 22
scenarios = [
    [0,30,60,90,120,150,180,210,240,270,300,330,360,390,420,450,480,510,540,570,600, 630], # timeline
    [10, 20, 30, 40, 50, 60, 70, 80, 90, 100, 110, 100, 90, 80, 70, 60, 50, 40, 30, 20, 10, 10], # increase gradually #1
    [10, 20, 20, 20, 20, 20, 60, 100, 140, 180, 220, 180, 140, 100, 60, 20, 20, 20, 20, 20, 10, 10], # increase gradually #2
    [10, 10, 10, 100, 100, 100, 10, 10, 10, 10, 10, 10, 10, 200, 200, 200, 10, 10, 10, 10, 10, 10], # increase abruptly
    [10, 10, 100, 100, 10, 10, 100, 100, 10, 10, 100, 100, 10, 10, 100, 100, 10, 10, 100, 100, 10, 10] # increase abruptly and repeatedly
]

target_cpu_utilizations = [40, 60, 80]
app_start_up_delays = [1, 5, 10, 30, 60]

class Options:
    def __init__(self, target_url: str, rtime: str) -> None:
        self.target_url = target_url        
        self.rtime = rtime
        
def init(argv, args):
    
    print('\n========== Start Test ==========\n')
    print('[Arguments]')
    print(' - url   : ', args.u)
    print(' - duration : ', args.rtime)    
    print('\n')
        
    return Options(args.u, args.rtime)


def data_logger(filename):    
    global is_thread_run, cur_requests
    is_thread_run = True    
    f = open(filename + ".txt", 'w')
    while(is_thread_run):
        running_pods = subprocess.check_output("kubectl get pod | grep -c Running ", shell=True, universal_newlines=True)                
        f.write(str(datetime.datetime.now()) + " " + str(cur_requests) + " " + str(running_pods))        
        time.sleep(5)
    f.close()
              
              
def main(argv, args):
    global is_thread_run, cur_requests
    options = init(argv, args)        
    yamlfile_path = "../k8s/manifests/simple_app.yaml"
    print(options.target_url)
    request_rate = 20 # fixed value    
    test_num = 0
    print("# Target URL: " + options.target_url + "\n")
    for tcu in target_cpu_utilizations:               
        for start_delay in app_start_up_delays:            
            # update start_delay in yaml
            with open(yamlfile_path) as f:
                doc = yaml.load(f, Loader=yaml.FullLoader)
                
            doc['spec']['template']["spec"]["containers"][0]["readinessProbe"]["initialDelaySeconds"] = start_delay
            with open(yamlfile_path, 'w') as f:
                yaml.dump(doc, f)
            
            for i, scenario in enumerate(scenarios[1:], start=1):
                test_num +=1
                print("[Test #" + str(test_num) + "]")
                print(f"# Target CPU Utilization: {tcu}")
                print(f"# Start up delay: {start_delay}")
                os.environ["READINESS_INIT_DELAY"] = str(start_delay)
                # os.system("echo $READINESS_INIT_DELAY")
                # need to remove deployment
                os.system("kubectl delete deployments.apps simple-app-deployment")
                time.sleep(60)
                os.system("kubectl apply -f " + yamlfile_path)
                time.sleep(10)       
                os.system(" kubectl autoscale deployment simple-app-deployment --cpu-percent=" + str(tcu) + " --min=1 --max=20")       
                Thread(target=data_logger, args=(str(tcu) + "_" + str(start_delay) + "_scenario#" + str(i),)).start()
                for requests in scenario:                                        
                    users = math.ceil(requests / request_rate)  
                    print(f"../hey_linux_amd64 -q {request_rate} -c {users} -z {options.rtime}s -disable-keepalive " + options.target_url)
                    cur_requests = requests               
                    os.system(f"../hey_linux_amd64 -q {request_rate} -c {users} -z {options.rtime}s -disable-keepalive " + options.target_url)
                    
                is_thread_run = False
    
    
if __name__ == '__main__' :
    argv = sys.argv        
    main(argv, args)
    
    