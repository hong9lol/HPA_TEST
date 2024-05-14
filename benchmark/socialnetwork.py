import subprocess
import time
import math

def execute_cmd(cmd):
    return subprocess.check_output(cmd, shell=True, universal_newlines=True)

standard_deployment = "nginx-thrift"
resource_rate={"compose-post-service":12.0, 
"home-timeline-service":7.0,
"nginx-thrift":28.0,
"post-storage-service":15.0,
"social-graph-service":3.0,
"text-service":8.0,
"unique-id-service":1.0 ,
"url-shorten-service":4.0,
"user-mention-service":4.0,
"user-service":1.0,
"user-timeline-service":17.0
}

resource_usage={"compose-post-service":0, 
"home-timeline-service":0,
"nginx-thrift":0,
"post-storage-service":0,
"social-graph-service":0,
"text-service":0,
"unique-id-service":0 ,
"url-shorten-service":0,
"user-mention-service":0,
"user-service":0,
"user-timeline-service":0
}

def main():    
    while True: 
        for deployment in resource_usage:
            resource_usage[deployment] = 0
        # 1 get total resource usage of frontend
        top_pod_list = execute_cmd("kubectl top pod").split("\n")[1:-1]
        nginx_pod_list = list(map(lambda pod: pod.split(), filter(lambda pod: pod.find("nginx") != -1, top_pod_list)))
        for pod in nginx_pod_list:
            resource_usage[standard_deployment] += int(pod[1].split("m")[0])        
        print("Standard Deployment Total CPU Usage: ",resource_usage[standard_deployment])
        
        # 2 calculate all deployment usage with the rate table
        for deployment in resource_usage:
            if deployment == standard_deployment:
                continue
            resource_usage[deployment] = math.ceil(resource_usage[standard_deployment] * (resource_rate[deployment]/resource_rate[standard_deployment]))
        
        # 3 calculate the number of pods for each deployment and go scale#향후 deployment별 cpu request 가져와서 계산해야함 지금은 (100m)
        deployment_replica_status = dict()
        res=execute_cmd("kubectl get deployment --no-headers -o custom-columns=:metadata.name,custom-columns=:status.replicas").split("\n")[:-1]
        for deployment in list(map(lambda x: x.split(),res)):
            deployment_replica_status[deployment[0]]=deployment[1]
        
        # print(deployment_replica_status)
        for deployment in resource_usage:
            if deployment == standard_deployment:
                continue
            
            num_of_pod = math.ceil(resource_usage[deployment] / 100)
            if num_of_pod == int(deployment_replica_status[deployment]):
                continue
            print("do scale for " + deployment + " with " + str(num_of_pod) + " replica(s)")
            execute_cmd("kubectl scale --replicas=" + str(num_of_pod) + " deployment/" + deployment)
            
        time.sleep(30)


if __name__ == "__main__":
    main()