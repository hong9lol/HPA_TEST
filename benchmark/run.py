import os
import sys
import math
import time
import datetime
import argparse
import sys
import yaml
import datetime
import subprocess

from config.hey import scenarios, target_cpu_utilizations, app_start_up_delays, app_performance
from config.hey import request_rate, duration, yamlfile_path
from utils.cmd import execute_cmd
from threading import Thread


parser = argparse.ArgumentParser()
parser.add_argument("-u", help=" : Target url")
parser.add_argument("-c", action='store_true', help=" : Custom HPA Mode")
args = parser.parse_args()


class Status:
    test_status = False
    current_requests = 0
    is_custom_hpa = False
    active_pods = 1


class Options:
    def __init__(self, target_url: str, custom) -> None:
        self.target_url = target_url
        setattr(Status, "is_custom_hpa", custom)


def init(argv, args):
    print("\n========== Start Test ==========\n")
    print("[Arguments]")
    print(" - url   : ", args.u)
    print(" - cumstom mode   : ", args.c)
    print("\n")

    return Options(args.u, args.c)


def init_custom_hpa():
    pod_name_list = execute_cmd(
        "kubectl get pods --no-headers -o custom-columns=:metadata.name").split("\n")[:-1]
    print("Pod List[20]")
    print(pod_name_list)

    # set first pod as an active pod
    pod_status = {pod_name: 0 for pod_name in pod_name_list}
    pod_status[pod_name_list[0]] = 1
    execute_cmd("kubectl patch pod " + pod_name_list[0]
                + """ -p '{"metadata":{"labels":{"status": "active"}}}'""")

    # set cpu request/limit to 10m of inactive pods
    for pod_name in pod_name_list[1:]:
        execute_cmd("kubectl patch pod " + pod_name +
                    """ --patch '{"spec":{"containers":[{"name":"simple-app", "resources":{"requests":{"cpu":"10m"}, "limits":{"cpu":"400m"}}}]}}'""")
        execute_cmd("kubectl patch pod " + pod_name +
                    """ -p '{"metadata":{"labels":{"status": "inactive"}}}'""")

    execute_cmd(
        """kubectl patch service simple-app-deployment -p '{"spec":{"selector":{"status": "active"}}}'""")
    return pod_name_list, pod_status


def _custom_hpa(tcu, pod_name_list, pod_status):

    avg_cpu_usage_percent = 0
    desired_pod_replicas = 0
    down_cool_time = 60
    current_down_cool_time = 0
    is_cool_time = False
    # check average cpu usage in every 15s 초마다 현대 동작중인 파드 기준으로 평균 cpu 사용량 계산
    while getattr(Status, "test_status"):
        # calculate total cpu usage of active pods
        sum_of_pod_cpu_usage = 0
        running_pod = 0
        for pod_name in pod_name_list:
            if pod_status[pod_name] == 1:
                running_pod += 1
                pod_cpu_usage = execute_cmd("kubectl top pod " + pod_name +
                                            """ --no-headers | awk '/[[:space:]]/ {print $2}'""").split("m")[0]
                print("pod_name: " + pod_name +
                      ", pod cpu usage: " + pod_cpu_usage)
                sum_of_pod_cpu_usage += int(pod_cpu_usage)

        # /2 == /200*100, 200 == cpu request
        avg_cpu_usage_percent = (float(sum_of_pod_cpu_usage)/running_pod)/2
        desired_pod_replicas = math.ceil(
            running_pod * (avg_cpu_usage_percent/tcu))  # hpa algorithm
        if desired_pod_replicas < 1:
            desired_pod_replicas = 1

        print("avg_usage_percent: " + str(avg_cpu_usage_percent) + "%\n" +
              "desired_replica: " + str(desired_pod_replicas) + "\n" +
              "tcu: " + str(tcu) + "\n" +
              "is cool time: " + str(is_cool_time) + "\n" +
              "current down cool time: " + str(current_down_cool_time))

        if current_down_cool_time > 0:
            if running_pod > desired_pod_replicas:
                is_cool_time = True
                current_down_cool_time -= 15
                time.sleep(15)
                continue

        # change resource and label
        for i, pod_name in enumerate(pod_name_list):
            if i < desired_pod_replicas:
                pod_status[pod_name] = 1
                execute_cmd("kubectl patch pod " + pod_name +
                            """ -p '{"metadata":{"labels":{"status": "active"}}}'""")
                execute_cmd("kubectl patch pod " + pod_name +
                            """ --patch '{"spec":{"containers":[{"name":"simple-app", "resources":{"requests":{"cpu":"200m"}, "limits":{"cpu":"400m"}}}]}}'""")

            else:
                pod_status[pod_name] =  0
                execute_cmd("kubectl patch pod " + pod_name +
                            """ --patch '{"spec":{"containers":[{"name":"simple-app", "resources":{"requests":{"cpu":"10m"}, "limits":{"cpu":"400m"}}}]}}'""")
                execute_cmd("kubectl patch pod " + pod_name +
                            """ -p '{"metadata":{"labels":{"status": "inactive"}}}'""")

        setattr(Status, "active_pods", desired_pod_replicas)
        is_cool_time = False
        current_down_cool_time = down_cool_time
        time.sleep(15)


def _log_benchmark(dir_name, filename):
    setattr(Status, "test_status", True)
    f = open("./log/" + dir_name + "/" + filename + ".txt", "w")
    while getattr(Status, "test_status"):
        if getattr(Status, "is_custom_hpa"):
            running_pods = getattr(Status, "active_pods")
            f.write(str(datetime.datetime.now()) + " " +
                    str(getattr(Status, "current_requests")) + " " + str(running_pods) + "\n")
        else:
            running_pods = execute_cmd(
                "kubectl get pod | grep Running | grep -c simple-app")
            f.write(str(datetime.datetime.now()) + " " +
                    str(getattr(Status, "current_requests")) + " " + str(running_pods))
        time.sleep(5)
    f.close()


def reset_test_hpa_environment(test_num, tcu, start_delay):
    print("[Test #" + str(test_num) + "]")
    print(f"# Target CPU Utilization: {tcu}")
    print(f"# Start up delay: {start_delay}")

    # remove origin deployment and hpa policy and wait 20s to ensure completion
    execute_cmd(
        """kubectl patch service simple-app-deployment -p '{"spec":{"selector":{"status": null}}}'""")
    os.system(
        "kubectl delete horizontalpodautoscalers.autoscaling simple-app-deployment"
    )
    os.system(
        "kubectl delete deployments.apps simple-app-deployment")

    print("Wait for 20s to ensure delete completion")
    time.sleep(20)

    # deploy deployment and hpa policy and wait 10s to ensure completion
    os.system("kubectl apply -f " + yamlfile_path)
    if not getattr(Status, "is_custom_hpa"):
        # os.system(
        #     "kubectl autoscale deployment simple-app-deployment --cpu-percent="
        #     + str(tcu)
        #     + " --min=1 --max=20"
        # )
        if tcu == 60:
            os.system("kubectl apply -f hpa_60.yaml")
        else:
            os.system("kubectl apply -f hpa_80.yaml")
        # a = """kubectl patch horizontalpodautoscalers.autoscaling simple-app-deployment -p '{"spec":{"metrics":[{"type":"Resource","resource":{"name":"cpu","target":{"averageUtilization": """ + str(
        #    tcu) + ""","type":"Utilization"}}}]}}"""
        # print(a)
        # os.system(
        #     """kubectl patch horizontalpodautoscalers.autoscaling simple-app-deployment -p '{"spec":{"metrics":[{"type":"Resource","resource":{"name":"cpu","target":{"averageUtilization": """ + str(tcu) + ""","type":"Utilization"}}}]}}""")
    print("Wait for 60s to ensure deployment work finished")
    time.sleep(60)


def get_target_url(argv, args):
    options = init(argv, args)
    print("# Target URL: " + options.target_url +
          "\n# Request Rate(processed in a second):" + str(request_rate) + "\n")
    return options.target_url


def create_dir():
    current_time = datetime.datetime.today().strftime('%Y%m%d%H%M%S')
    dir_name = current_time + "_" + \
        str(int(request_rate)) + "_" + str(duration)
    os.system("rm -r ./log/" + dir_name)
    os.system("mkdir ./log/" + dir_name)

    print("# Create directory: " + dir_name + "\n")
    return dir_name


def set_start_delay(start_delay):
    with open(yamlfile_path) as f:
        doc = yaml.load(f, Loader=yaml.FullLoader)
    doc["spec"]["template"]["spec"]["containers"][0]["readinessProbe"][
        "initialDelaySeconds"
    ] = start_delay
    if getattr(Status, "is_custom_hpa"):
        doc["spec"]["replicas"] = 20
    else:
        doc["spec"]["replicas"] = 1
    with open(yamlfile_path, "w") as f:
        yaml.dump(doc, f)


def main(argv, args):
    test_num = 0
    target_service_url = get_target_url(argv, args)
    dir_name = create_dir()

    for tcu in target_cpu_utilizations:  # each target cpu utilization
        for start_delay in app_start_up_delays:  # each app startup delay
            # update start_delay in yaml file (app's start up time delay)
            set_start_delay(start_delay)

            # each scenario, start from 1 // [0]: timeline
            for i, scenario in enumerate(scenarios[1:], start=1):
                test_num += 1
                reset_test_hpa_environment(test_num, tcu, start_delay)

                # Thread to write the result of the current test
                Thread(target=_log_benchmark,
                       args=(dir_name, str(tcu) + "_" +
                             str(start_delay) + "_scenario#" + str(i),),
                       ).start()
                if getattr(Status, "is_custom_hpa"):
                    pod_name_list, pod_status = init_custom_hpa()
                    Thread(
                        target=_custom_hpa,
                        args=(tcu, pod_name_list, pod_status),
                    ).start()

                # run load generator(hey)
                for requests in scenario:
                    # users for concurrency i.e. 40/20 = 2, 20/10 = 2
                    users = math.ceil(requests / request_rate)
                    setattr(Status, "current_requests", requests)
                    command = ["./hey_linux_amd64 -q " + str(request_rate) + " -c " + str(users) + " -z " + str(
                        duration) + "s " + "-t 15 -disable-keepalive " + target_service_url + "/" + app_performance]
                    print(command)

                    # log load generator output
                    with open("./log/" + dir_name + "/hey.log", "a") as outfile:
                        subprocess.run(command, stdout=outfile, shell=True)
                setattr(Status, "test_status", False)


if __name__ == "__main__":
    argv = sys.argv
    main(argv, args)
