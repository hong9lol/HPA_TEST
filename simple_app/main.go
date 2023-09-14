package main

import (
	"fmt"
	"net/http"
	"os"
	"time"
)

var DEBUG = "NO"

func requestHandler(w http.ResponseWriter, r *http.Request) {
	var RequestHandlingTime int64 = 10 // Unit: ms
	startTime := time.Now().UnixMilli()
	endTime := time.Now().UnixMilli()

	for {
		endTime = time.Now().UnixMilli()
		if (endTime - startTime) > RequestHandlingTime {
			break
		}
	}

	if DEBUG == "YES" {
		fmt.Fprintf(w, "<h1>Start Time: %d End Time: %d Diff: %d</h1>\n", startTime, endTime, endTime-startTime)
	}
}

func main() {
	if DEBUG == "YES" {
		fmt.Fprintf(os.Stdout, "Web Server started. Listening on 0.0.0.0:8080\n")
	}
	http.HandleFunc("/", requestHandler)
	http.ListenAndServe(":8080", nil)
}