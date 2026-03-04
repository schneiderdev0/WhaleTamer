package main

import (
	"bytes"
	"context"
	"encoding/json"
	"errors"
	"fmt"
	"net/http"
	"os"
	"strconv"
	"time"

	"github.com/shirou/gopsutil/v3/cpu"
	"github.com/shirou/gopsutil/v3/host"
	"github.com/shirou/gopsutil/v3/mem"
)

type Config struct {
	BackendURL      string
	Token           string
	Source          string
	IntervalSeconds int
	MaxBatchErrors  int
}

type CollectorPayload struct {
	Hostname  string                 `json:"hostname"`
	Timestamp time.Time              `json:"timestamp"`
	Metrics   map[string]any         `json:"metrics"`
	Logs      map[string]string      `json:"logs"`
}

type IngestRequest struct {
	Source  string          `json:"source"`
	Payload CollectorPayload `json:"payload"`
}

func main() {
	cfg, err := loadConfig()
	if err != nil {
		fmt.Fprintln(os.Stderr, err.Error())
		os.Exit(1)
	}

	client := &http.Client{Timeout: 20 * time.Second}
	ticker := time.NewTicker(time.Duration(cfg.IntervalSeconds) * time.Second)
	defer ticker.Stop()

	for {
		_ = sendWithRetry(context.Background(), client, cfg)
		<-ticker.C
	}
}

func loadConfig() (Config, error) {
	backendURL := os.Getenv("WT_BACKEND_URL")
	token := os.Getenv("WT_DC_TOKEN")
	source := os.Getenv("WT_SOURCE")
	intervalStr := os.Getenv("WT_INTERVAL_SECONDS")
	maxErrStr := os.Getenv("WT_MAX_BATCH_ERRORS")

	if backendURL == "" {
		return Config{}, errors.New("WT_BACKEND_URL is required (e.g. http://backend:8000)")
	}
	if token == "" {
		return Config{}, errors.New("WT_DC_TOKEN is required (dc_...)")
	}
	if source == "" {
		h, _ := os.Hostname()
		source = h
	}
	interval := 15
	if intervalStr != "" {
		if v, err := strconv.Atoi(intervalStr); err == nil && v > 0 {
			interval = v
		}
	}

	maxBatchErrors := 10
	if maxErrStr != "" {
		if v, err := strconv.Atoi(maxErrStr); err == nil && v > 0 {
			maxBatchErrors = v
		}
	}

	return Config{
		BackendURL:      backendURL,
		Token:           token,
		Source:          source,
		IntervalSeconds: interval,
		MaxBatchErrors:  maxBatchErrors,
	}, nil
}

func sendOnce(ctx context.Context, client *http.Client, cfg Config) error {
	payload, err := collectPayload(ctx, cfg.MaxBatchErrors)
	if err != nil {
		return err
	}

	reqBody := IngestRequest{
		Source:  cfg.Source,
		Payload: payload,
	}
	b, err := json.Marshal(reqBody)
	if err != nil {
		return err
	}

	url := stringsTrimRightSlash(cfg.BackendURL) + "/collector/ingest"
	req, err := http.NewRequestWithContext(ctx, http.MethodPost, url, bytes.NewReader(b))
	if err != nil {
		return err
	}
	req.Header.Set("Authorization", "Bearer "+cfg.Token)
	req.Header.Set("Content-Type", "application/json")

	resp, err := client.Do(req)
	if err != nil {
		return err
	}
	defer resp.Body.Close()
	if resp.StatusCode >= 300 {
		return fmt.Errorf("backend responded %s", resp.Status)
	}
	return nil
}

func sendWithRetry(ctx context.Context, client *http.Client, cfg Config) error {
	const maxAttempts = 5
	var lastErr error
	backoff := time.Second

	for attempt := 1; attempt <= maxAttempts; attempt++ {
		if err := sendOnce(ctx, client, cfg); err != nil {
			lastErr = err
			fmt.Fprintln(os.Stderr, "send error:", err.Error())
			time.Sleep(backoff)
			backoff *= 2
			continue
		}
		return nil
	}
	return lastErr
}

func collectPayload(ctx context.Context, maxBatchErrors int) (CollectorPayload, error) {
	hostInfo, _ := host.InfoWithContext(ctx)
	hostname := hostInfo.Hostname
	if hostname == "" {
		h, _ := os.Hostname()
		hostname = h
	}

	vm, _ := mem.VirtualMemoryWithContext(ctx)
	cpuPercents, _ := cpu.PercentWithContext(ctx, 0, false)
	cpuPercent := 0.0
	if len(cpuPercents) > 0 {
		cpuPercent = cpuPercents[0]
	}

	metrics := map[string]any{}
	metrics["cpu_percent"] = cpuPercent
	if maxBatchErrors >= 3 {
		metrics["mem_total"] = vm.Total
		metrics["mem_used"] = vm.Used
		metrics["mem_free"] = vm.Free
	}

	return CollectorPayload{
		Hostname:  hostname,
		Timestamp: time.Now().UTC(),
		Metrics:   metrics,
		Logs:      map[string]string{},
	}, nil
}

func stringsTrimRightSlash(s string) string {
	for len(s) > 0 && s[len(s)-1] == '/' {
		s = s[:len(s)-1]
	}
	return s
}

