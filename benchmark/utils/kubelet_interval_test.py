from cmd import execute_cmd
import time
import datetime

count = 360
config = execute_cmd(
    'kubectl get --raw "/api/v1/nodes/minikube/proxy/configz" | jq | grep nodeStatusUpdateFrequency')
f = open("./" + config.split("\n")
         [0].split(": ")[1].split(",")[0].split("\"")[1] + "_kubelet_interval_check.log", 'w')
f.write(config + "\n")
while True:

    ret = execute_cmd("curl -k --cacert /home/leejaehong/.minikube/ca.crt --key /home/leejaehong/.minikube/profiles/minikube/client.key --cert /home/leejaehong/.minikube/profiles/minikube/client.crt https://192.168.49.2:10250/metrics/resource").split("\n")
    # ret = execute_cmd(
    #    "echo " + ret + " | grep pod_cpu_usage_seconds_total")
    output = str(datetime.datetime.now().second) + \
        " " + ret[46].split("\"}")[1] + "\n"
    print(output)
    f.write(output)
    count -= 1
    if count <= 0:
        break
f.close
