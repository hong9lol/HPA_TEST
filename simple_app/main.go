package main

import (
	"fmt"
	"net/http"
	"os"
	"time"
)

var DEBUG = "NO"
var performanceParams map[string]int64 = map[string]int64{
	"low":  6,
	"mid":  9,
	"high": 12,
}

func timer(w http.ResponseWriter, requestHandlingTime int64) {
	startTime := time.Now().UnixMilli()
	endTime := time.Now().UnixMilli()

	for {
		endTime = time.Now().UnixMilli()
		if (endTime - startTime) > requestHandlingTime {
			break
		}
	}

	if DEBUG == "YES" {
		fmt.Fprintf(w, "<h1>Handling Time: %d, Start Time: %d End Time: %d Diff: %d</h1>\n", requestHandlingTime, startTime, endTime, endTime-startTime)
	}
}

func requestHandler(w http.ResponseWriter, r *http.Request) {
	var requestHandlingTime int64 = performanceParams["mid"] // set default 9ms, cause sub-jobs take about 1ms
	timer(w, requestHandlingTime)
}

func requestHandlerLow(w http.ResponseWriter, r *http.Request) {
	var requestHandlingTime int64 = performanceParams["low"]
	timer(w, requestHandlingTime)
}

func requestHandlerMid(w http.ResponseWriter, r *http.Request) {
	var requestHandlingTime int64 = performanceParams["mid"]
	timer(w, requestHandlingTime)
}

func requestHandlerHigh(w http.ResponseWriter, r *http.Request) {
	var requestHandlingTime int64 = performanceParams["high"]
	timer(w, requestHandlingTime)
}

func healthChecker(w http.ResponseWriter, r *http.Request) {
	// do nothing
}

func main() {
	if DEBUG == "YES" {
		fmt.Fprintf(os.Stdout, "Web Server started. Listening on 0.0.0.0:8080\n")
	}
	http.HandleFunc("/", requestHandler)
	http.HandleFunc("/low", requestHandlerLow)
	http.HandleFunc("/mid", requestHandlerMid)
	http.HandleFunc("/high", requestHandlerHigh)
	http.HandleFunc("/healthz", healthChecker)
	http.ListenAndServe(":8080", nil)
}
