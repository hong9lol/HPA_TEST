import os
import sys
import math
import time
import datetime
import subprocess
import argparse
import sys
import subprocess
import yaml

from config import scenarios, target_cpu_utilizations, app_start_up_delays, app_performance
from config import request_rate, duration, yamlfile_path
from threading import Thread


parser = argparse.ArgumentParser()
parser.add_argument("-u", help=" : Target url")
args = parser.parse_args()

is_one_of_tests_running = False
cur_requests = 0


class Options:
    def __init__(self, target_url: str) -> None:
        self.target_url = target_url


def init(argv, args):
    print("\n========== Start Test ==========\n")
    print("[Arguments]")
    print(" - url   : ", args.u)
    print("\n")

    return Options(args.u)


def _log_benchmark(dir_name, filename):
    global is_one_of_tests_running, cur_requests
    is_one_of_tests_running = True
    f = open("./" + dir_name + "/" + filename + ".txt", "w")
    while is_one_of_tests_running:
        running_pods = subprocess.check_output(
            "kubectl get pod | grep -c Running", shell=True, universal_newlines=True
        )
        f.write(
            str(datetime.datetime.now())
            + " "
            + str(cur_requests)
            + " "
            + str(running_pods)
        )
        time.sleep(5)
    f.close()


def main(argv, args):
    options = init(argv, args)
    global is_one_of_tests_running, cur_requests
    test_num = 0

    print("# Target URL: " + options.target_url +
          "\n# Request Rate(processed in a second):" + str(request_rate) + "\n")

    dir_name = str(int(request_rate)) + "_" + str(duration)
    os.system("rm -r " + dir_name)
    os.system("mkdir " + dir_name)
    for tcu in target_cpu_utilizations:  # each target cpu utilization
        for start_delay in app_start_up_delays:  # each app startup delay
            # update start_delay in yaml file
            with open(yamlfile_path) as f:
                doc = yaml.load(f, Loader=yaml.FullLoader)
            doc["spec"]["template"]["spec"]["containers"][0]["readinessProbe"][
                "initialDelaySeconds"
            ] = start_delay
            with open(yamlfile_path, "w") as f:
                yaml.dump(doc, f)

            # each scenario, start from 1, [0]: timeline
            for i, scenario in enumerate(scenarios[1:], start=1):
                test_num += 1

                print("[Test #" + str(test_num) + "]")
                print(f"# Target CPU Utilization: {tcu}")
                print(f"# Start up delay: {start_delay}")

                # remove origin deployment and hpa policy and wait 20s to ensure completion
                os.system(
                    "kubectl delete horizontalpodautoscalers.autoscaling simple-app-deployment"
                )
                os.system(
                    "kubectl delete deployments.apps simple-app-deployment")

                print("Wait for 20s to ensure delete completion")
                time.sleep(20)

                # deploy deployment and hpa policy and wait 10s to ensure completion
                os.system("kubectl apply -f " + yamlfile_path)
                os.system(
                    "kubectl autoscale deployment simple-app-deployment --cpu-percent="
                    + str(tcu)
                    + " --min=1 --max=20"
                )
                print("Wait for 20s to ensure deployment completion")
                time.sleep(20)

                # Thread to write the result of this test
                Thread(
                    target=_log_benchmark,
                    args=(dir_name, str(tcu) + "_" + str(start_delay) +
                          "_scenario#" + str(i),),
                ).start()

                # run load generator(hey) to test all requests in each scenario
                for requests in scenario:
                    # users for concurrency i.e. 40/20 = 2, 20/10 = 2
                    users = math.ceil(requests / request_rate)
                    cur_requests = requests
                    command = ["./hey_linux_amd64 -q " + str(request_rate) + " -c " + str(users) + " -z " + str(
                        duration) + "s " + "-disable-keepalive " + options.target_url + "/" + app_performance]
                    print(command)

                    # run and log the output of the loadgenerator
                    with open("./" + dir_name + "/hey.log", "a") as outfile:
                        # subprocess.run(command, stdout=outfile,)
                        subprocess.run(command, stdout=outfile, shell=True)
                is_one_of_tests_running = False


if __name__ == "__main__":
    argv = sys.argv
    main(argv, args)
