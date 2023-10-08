# Scenarios List
# [0]: timeline
# [1]: increase gradually #1
# [2]: increase gradually #2
# [3]: increase abruptly
# [4]: increase abruptly and repeatedly
# [5]: add your cumstom scenario
scenarios = [
    [0, 30, 60, 90, 120, 150, 180, 210, 240, 270, 300, 330,
        360, 390, 420, 450, 480, 510, 540, 570, 600, 630,],
    [10, 20, 30, 40, 50, 60, 70, 80, 90, 100, 110,
        100, 90, 80, 70, 60, 50, 40, 30, 20, 10, 10,],
    [10, 20, 20, 20, 20, 20, 60, 100, 140, 180, 220,
        180, 140, 100, 60, 20, 20, 20, 20, 20, 10, 10,],
    # [10, 10, 10, 100, 100, 100, 10, 10, 10, 10, 10, 10,
    #     10, 200, 200, 200, 10, 10, 10, 10, 10, 10,],
    [10, 10, 100, 100, 10, 10, 100, 100, 10, 10, 100,
        100, 10, 10, 100, 100, 10, 10, 100, 100, 10, 10,]
]

target_cpu_utilizations = [60, 80]
app_start_up_delays = [1, 30, 60]

# "low", "mid", "high"
app_performance = "mid"

request_rate = 20.0
duration = 20

yamlfile_path = "./k8s/manifests/simple_app.yaml"
