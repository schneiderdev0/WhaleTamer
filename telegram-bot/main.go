package main

import (
	"bytes"
	"context"
	"encoding/json"
	"errors"
	"fmt"
	"io"
	"net/http"
	"os"
	"path/filepath"
	"strings"
	"sync"
	"time"

	tgbotapi "github.com/go-telegram-bot-api/telegram-bot-api/v5"
)

type Config struct {
	BotToken          string
	Backend           string
	StatePath         string
	UpdateMode        string
	WebhookURL        string
	WebhookListenAddr string
	WebhookPath       string
}

type State struct {
	// chat_id -> tg_token (plain, tg_...)
	Links map[string]string `json:"links"`
	// chat_id -> last sent report_id
	LastReport map[string]string `json:"last_report"`
	// chat_id -> RFC3339 timestamp of last sent notification
	LastSentAt map[string]string `json:"last_sent_at"`
}

type BackendLinkReq struct {
	Token    string `json:"token"`
	ChatID   int64  `json:"chat_id"`
	Username string `json:"username,omitempty"`
}

type LatestReportResp struct {
	ReportID        string    `json:"report_id"`
	CreatedAt       time.Time `json:"created_at"`
	Status          string    `json:"status"`
	Model           string    `json:"model"`
	Summary         string    `json:"summary"`
	Issues          []string  `json:"issues"`
	Recommendations []string  `json:"recommendations"`
}

type NotificationSettings struct {
	Enabled   bool   `json:"enabled"`
	Frequency string `json:"frequency"`
	Severity  string `json:"severity"`
}

type NotificationSettingsResp struct {
	Linked   bool                 `json:"linked"`
	ChatID   int64                `json:"chat_id"`
	Username string               `json:"username"`
	Settings NotificationSettings `json:"settings"`
}

type NotificationSettingsUpdateReq struct {
	Enabled   *bool   `json:"enabled,omitempty"`
	Frequency *string `json:"frequency,omitempty"`
	Severity  *string `json:"severity,omitempty"`
}

func main() {
	cfg, err := loadConfig()
	if err != nil {
		fmt.Fprintln(os.Stderr, err.Error())
		os.Exit(1)
	}

	bot, err := tgbotapi.NewBotAPI(cfg.BotToken)
	if err != nil {
		fmt.Fprintln(os.Stderr, "bot init error:", err.Error())
		os.Exit(1)
	}

	client := &http.Client{Timeout: 20 * time.Second}
	st := newStateStore(cfg.StatePath)
	_ = st.Load() // best-effort
	ctx, cancel := context.WithCancel(context.Background())
	defer cancel()

	updates, shutdownUpdates, err := setupUpdates(bot, cfg)
	if err != nil {
		fmt.Fprintln(os.Stderr, "updates setup error:", err.Error())
		os.Exit(1)
	}
	defer shutdownUpdates()
	go runAutoNotifications(ctx, bot, client, cfg.Backend, st)

	for update := range updates {
		if update.Message == nil {
			continue
		}
		if !update.Message.IsCommand() {
			continue
		}

		chatID := update.Message.Chat.ID
		username := update.Message.From.UserName
		cmd := update.Message.Command()
		args := strings.TrimSpace(update.Message.CommandArguments())

		switch cmd {
		case "start", "help":
			text := "Команды:\n" +
				"/start <tg_token> — привязать аккаунт\n" +
				"/latest — показать последний отчёт\n" +
				"/notify — показать настройки уведомлений\n" +
				"/notify <all|critical> <event|hourly|daily> [on|off] — изменить настройки\n"
			if cmd == "start" && args != "" {
				// treat /start <tg_token> as link command
				if err := linkAccount(context.Background(), client, cfg.Backend, args, chatID, username); err != nil {
					text = "Ошибка привязки: " + err.Error()
				} else {
					st.Set(chatID, args)
					_ = st.Save()
					text = "Аккаунт привязан. Используй /latest чтобы получить последний отчёт."
				}
			}
			bot.Send(tgbotapi.NewMessage(chatID, text))

		case "latest":
			token, ok := st.Get(chatID)
			if !ok || token == "" {
				bot.Send(tgbotapi.NewMessage(chatID, "Нет привязки. Выполни /start <tg_token>"))
				continue
			}
			rep, err := fetchLatestReport(context.Background(), client, cfg.Backend, token)
			if err != nil {
				bot.Send(tgbotapi.NewMessage(chatID, "Ошибка: "+err.Error()))
				continue
			}
			msg := formatLatestReport(rep)
			bot.Send(tgbotapi.NewMessage(chatID, msg))

		case "notify":
			token, ok := st.Get(chatID)
			if !ok || token == "" {
				bot.Send(tgbotapi.NewMessage(chatID, "Нет привязки. Выполни /start <tg_token>"))
				continue
			}

			if args == "" {
				settings, err := fetchNotificationSettings(context.Background(), client, cfg.Backend, token)
				if err != nil {
					bot.Send(tgbotapi.NewMessage(chatID, "Ошибка: "+err.Error()))
					continue
				}
				bot.Send(tgbotapi.NewMessage(chatID, formatNotificationSettings(settings)))
				continue
			}

			parts := strings.Fields(args)
			if len(parts) < 2 || len(parts) > 3 {
				bot.Send(tgbotapi.NewMessage(chatID, "Формат: /notify <all|critical> <event|hourly|daily> [on|off]"))
				continue
			}
			severity := parts[0]
			frequency := parts[1]
			if severity != "all" && severity != "critical" {
				bot.Send(tgbotapi.NewMessage(chatID, "severity: all или critical"))
				continue
			}
			if frequency != "event" && frequency != "hourly" && frequency != "daily" {
				bot.Send(tgbotapi.NewMessage(chatID, "frequency: event, hourly или daily"))
				continue
			}
			req := NotificationSettingsUpdateReq{
				Severity:  strPtr(severity),
				Frequency: strPtr(frequency),
			}
			if len(parts) == 3 {
				switch strings.ToLower(parts[2]) {
				case "on":
					req.Enabled = boolPtr(true)
				case "off":
					req.Enabled = boolPtr(false)
				default:
					bot.Send(tgbotapi.NewMessage(chatID, "enabled: on или off"))
					continue
				}
			}
			settings, err := updateNotificationSettings(context.Background(), client, cfg.Backend, token, req)
			if err != nil {
				bot.Send(tgbotapi.NewMessage(chatID, "Ошибка: "+err.Error()))
				continue
			}
			bot.Send(tgbotapi.NewMessage(chatID, "Настройки сохранены.\n"+formatNotificationSettings(settings)))

		default:
			bot.Send(tgbotapi.NewMessage(chatID, "Неизвестная команда. /help"))
		}
	}
}

func loadConfig() (Config, error) {
	token := os.Getenv("WT_TG_BOT_TOKEN")
	backend := os.Getenv("WT_BACKEND_URL")
	state := os.Getenv("WT_BOT_STATE_PATH")
	mode := strings.TrimSpace(strings.ToLower(os.Getenv("WT_TG_UPDATE_MODE")))
	webhookURL := strings.TrimSpace(os.Getenv("WT_TG_WEBHOOK_URL"))
	webhookListenAddr := strings.TrimSpace(os.Getenv("WT_TG_WEBHOOK_LISTEN_ADDR"))
	webhookPath := strings.TrimSpace(os.Getenv("WT_TG_WEBHOOK_PATH"))

	if token == "" {
		return Config{}, errors.New("WT_TG_BOT_TOKEN is required")
	}
	if backend == "" {
		return Config{}, errors.New("WT_BACKEND_URL is required (e.g. http://backend:8000)")
	}
	if state == "" {
		state = "/data/state.json"
	}
	if mode == "" {
		mode = "polling"
	}
	if mode != "polling" && mode != "webhook" {
		return Config{}, errors.New("WT_TG_UPDATE_MODE must be polling or webhook")
	}
	if webhookListenAddr == "" {
		webhookListenAddr = ":8080"
	}
	if webhookPath == "" {
		webhookPath = "/"
	}
	if mode == "webhook" && webhookURL == "" {
		return Config{}, errors.New("WT_TG_WEBHOOK_URL is required for webhook mode")
	}
	return Config{
		BotToken:          token,
		Backend:           stringsTrimRightSlash(backend),
		StatePath:         state,
		UpdateMode:        mode,
		WebhookURL:        webhookURL,
		WebhookListenAddr: webhookListenAddr,
		WebhookPath:       webhookPath,
	}, nil
}

func setupUpdates(bot *tgbotapi.BotAPI, cfg Config) (tgbotapi.UpdatesChannel, func(), error) {
	if cfg.UpdateMode == "webhook" {
		hook, err := tgbotapi.NewWebhook(cfg.WebhookURL)
		if err != nil {
			return nil, nil, err
		}
		if _, err := bot.Request(hook); err != nil {
			return nil, nil, err
		}

		updates := bot.ListenForWebhook(cfg.WebhookPath)
		server := &http.Server{Addr: cfg.WebhookListenAddr}
		go func() {
			_ = server.ListenAndServe()
		}()
		shutdown := func() {
			ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
			defer cancel()
			_ = server.Shutdown(ctx)
		}
		return updates, shutdown, nil
	}

	_, _ = bot.Request(tgbotapi.DeleteWebhookConfig{DropPendingUpdates: true})
	u := tgbotapi.NewUpdate(0)
	u.Timeout = 30
	return bot.GetUpdatesChan(u), func() {}, nil
}

func linkAccount(ctx context.Context, client *http.Client, backend, tgToken string, chatID int64, username string) error {
	body := BackendLinkReq{
		Token:    tgToken,
		ChatID:   chatID,
		Username: username,
	}
	b, _ := json.Marshal(body)
	req, err := http.NewRequestWithContext(ctx, http.MethodPost, backend+"/telegram/link", bytes.NewReader(b))
	if err != nil {
		return err
	}
	req.Header.Set("Content-Type", "application/json")

	resp, err := client.Do(req)
	if err != nil {
		return err
	}
	defer resp.Body.Close()
	if resp.StatusCode >= 300 {
		raw, _ := io.ReadAll(resp.Body)
		return fmt.Errorf("backend responded %s: %s", resp.Status, string(raw))
	}
	return nil
}

func fetchLatestReport(ctx context.Context, client *http.Client, backend, tgToken string) (LatestReportResp, error) {
	req, err := http.NewRequestWithContext(ctx, http.MethodGet, backend+"/telegram/reports/latest", nil)
	if err != nil {
		return LatestReportResp{}, err
	}
	req.Header.Set("Authorization", "Bearer "+tgToken)

	resp, err := client.Do(req)
	if err != nil {
		return LatestReportResp{}, err
	}
	defer resp.Body.Close()
	raw, _ := io.ReadAll(resp.Body)
	if resp.StatusCode == 404 {
		return LatestReportResp{}, errors.New("отчётов пока нет")
	}
	if resp.StatusCode >= 300 {
		return LatestReportResp{}, fmt.Errorf("backend responded %s: %s", resp.Status, string(raw))
	}
	var out LatestReportResp
	if err := json.Unmarshal(raw, &out); err != nil {
		return LatestReportResp{}, err
	}
	return out, nil
}

func fetchNotificationSettings(ctx context.Context, client *http.Client, backend, tgToken string) (NotificationSettingsResp, error) {
	req, err := http.NewRequestWithContext(ctx, http.MethodGet, backend+"/telegram/notification-settings", nil)
	if err != nil {
		return NotificationSettingsResp{}, err
	}
	req.Header.Set("Authorization", "Bearer "+tgToken)

	resp, err := client.Do(req)
	if err != nil {
		return NotificationSettingsResp{}, err
	}
	defer resp.Body.Close()
	raw, _ := io.ReadAll(resp.Body)
	if resp.StatusCode >= 300 {
		return NotificationSettingsResp{}, fmt.Errorf("backend responded %s: %s", resp.Status, string(raw))
	}
	var out NotificationSettingsResp
	if err := json.Unmarshal(raw, &out); err != nil {
		return NotificationSettingsResp{}, err
	}
	return out, nil
}

func updateNotificationSettings(
	ctx context.Context,
	client *http.Client,
	backend, tgToken string,
	body NotificationSettingsUpdateReq,
) (NotificationSettingsResp, error) {
	b, _ := json.Marshal(body)
	req, err := http.NewRequestWithContext(ctx, http.MethodPut, backend+"/telegram/notification-settings", bytes.NewReader(b))
	if err != nil {
		return NotificationSettingsResp{}, err
	}
	req.Header.Set("Authorization", "Bearer "+tgToken)
	req.Header.Set("Content-Type", "application/json")

	resp, err := client.Do(req)
	if err != nil {
		return NotificationSettingsResp{}, err
	}
	defer resp.Body.Close()
	raw, _ := io.ReadAll(resp.Body)
	if resp.StatusCode >= 300 {
		return NotificationSettingsResp{}, fmt.Errorf("backend responded %s: %s", resp.Status, string(raw))
	}
	var out NotificationSettingsResp
	if err := json.Unmarshal(raw, &out); err != nil {
		return NotificationSettingsResp{}, err
	}
	return out, nil
}

func runAutoNotifications(ctx context.Context, bot *tgbotapi.BotAPI, client *http.Client, backend string, st *stateStore) {
	ticker := time.NewTicker(1 * time.Minute)
	defer ticker.Stop()

	checkOnce := func() {
		links := st.LinksSnapshot()
		for chatID, token := range links {
			settingsResp, err := fetchNotificationSettings(ctx, client, backend, token)
			if err != nil || !settingsResp.Linked || !settingsResp.Settings.Enabled {
				continue
			}
			rep, err := fetchLatestReport(ctx, client, backend, token)
			if err != nil {
				continue
			}
			if settingsResp.Settings.Severity == "critical" && !isCriticalReport(rep) {
				continue
			}
			if !shouldSendForFrequency(st, chatID, settingsResp.Settings.Frequency, rep.ReportID) {
				continue
			}

			msg := "Авто-уведомление\n\n" + formatLatestReport(rep)
			if _, err := bot.Send(tgbotapi.NewMessage(chatID, msg)); err != nil {
				continue
			}
			st.MarkSent(chatID, rep.ReportID, time.Now().UTC())
			_ = st.Save()
		}
	}

	checkOnce()
	for {
		select {
		case <-ctx.Done():
			return
		case <-ticker.C:
			checkOnce()
		}
	}
}

func shouldSendForFrequency(st *stateStore, chatID int64, frequency, reportID string) bool {
	lastReportID, _ := st.GetLastReport(chatID)
	lastSentAt, hasLastSentAt := st.GetLastSentAt(chatID)

	switch frequency {
	case "event":
		return reportID != "" && reportID != lastReportID
	case "hourly":
		if !hasLastSentAt {
			return true
		}
		return time.Since(lastSentAt) >= time.Hour
	case "daily":
		if !hasLastSentAt {
			return true
		}
		return time.Since(lastSentAt) >= 24*time.Hour
	default:
		return reportID != "" && reportID != lastReportID
	}
}

func isCriticalReport(rep LatestReportResp) bool {
	if strings.EqualFold(rep.Status, "failed") {
		return true
	}
	return len(rep.Issues) > 0
}

func formatLatestReport(rep LatestReportResp) string {
	lines := []string{
		fmt.Sprintf("Последний отчёт (%s)", rep.CreatedAt.Format(time.RFC3339)),
		fmt.Sprintf("Модель: %s", rep.Model),
		fmt.Sprintf("Статус: %s", rep.Status),
		"",
		"Сводка:",
		rep.Summary,
	}
	if len(rep.Issues) > 0 {
		lines = append(lines, "", "Проблемы:")
		limit := minInt(3, len(rep.Issues))
		for i := 0; i < limit; i++ {
			lines = append(lines, "- "+rep.Issues[i])
		}
	}
	if len(rep.Recommendations) > 0 {
		lines = append(lines, "", "Рекомендации:")
		limit := minInt(5, len(rep.Recommendations))
		for i := 0; i < limit; i++ {
			lines = append(lines, "- "+rep.Recommendations[i])
		}
	}
	return strings.Join(lines, "\n")
}

func formatNotificationSettings(resp NotificationSettingsResp) string {
	if !resp.Linked {
		return "Telegram ещё не привязан. Выполни /start <tg_token>"
	}
	state := "on"
	if !resp.Settings.Enabled {
		state = "off"
	}
	return fmt.Sprintf(
		"Текущие настройки:\n- severity: %s\n- frequency: %s\n- enabled: %s",
		resp.Settings.Severity,
		resp.Settings.Frequency,
		state,
	)
}

func minInt(a, b int) int {
	if a < b {
		return a
	}
	return b
}

func boolPtr(v bool) *bool {
	return &v
}

func strPtr(v string) *string {
	return &v
}

func stringsTrimRightSlash(s string) string {
	for len(s) > 0 && s[len(s)-1] == '/' {
		s = s[:len(s)-1]
	}
	return s
}

type stateStore struct {
	path string
	mu   sync.Mutex
	st   State
}

func newStateStore(path string) *stateStore {
	return &stateStore{
		path: path,
		st: State{
			Links:      map[string]string{},
			LastReport: map[string]string{},
			LastSentAt: map[string]string{},
		},
	}
}

func (s *stateStore) Load() error {
	s.mu.Lock()
	defer s.mu.Unlock()

	b, err := os.ReadFile(s.path)
	if err != nil {
		return err
	}
	var st State
	if err := json.Unmarshal(b, &st); err != nil {
		return err
	}
	if st.Links == nil {
		st.Links = map[string]string{}
	}
	if st.LastReport == nil {
		st.LastReport = map[string]string{}
	}
	if st.LastSentAt == nil {
		st.LastSentAt = map[string]string{}
	}
	s.st = st
	return nil
}

func (s *stateStore) Save() error {
	s.mu.Lock()
	defer s.mu.Unlock()

	if err := os.MkdirAll(filepath.Dir(s.path), 0o755); err != nil {
		return err
	}
	b, err := json.MarshalIndent(s.st, "", "  ")
	if err != nil {
		return err
	}
	return os.WriteFile(s.path, b, 0o600)
}

func (s *stateStore) Set(chatID int64, token string) {
	s.mu.Lock()
	defer s.mu.Unlock()
	s.st.Links[fmt.Sprintf("%d", chatID)] = token
}

func (s *stateStore) Get(chatID int64) (string, bool) {
	s.mu.Lock()
	defer s.mu.Unlock()
	v, ok := s.st.Links[fmt.Sprintf("%d", chatID)]
	return v, ok
}

func (s *stateStore) LinksSnapshot() map[int64]string {
	s.mu.Lock()
	defer s.mu.Unlock()

	out := make(map[int64]string, len(s.st.Links))
	for key, value := range s.st.Links {
		var id int64
		if _, err := fmt.Sscanf(key, "%d", &id); err == nil {
			out[id] = value
		}
	}
	return out
}

func (s *stateStore) GetLastReport(chatID int64) (string, bool) {
	s.mu.Lock()
	defer s.mu.Unlock()
	v, ok := s.st.LastReport[fmt.Sprintf("%d", chatID)]
	return v, ok
}

func (s *stateStore) GetLastSentAt(chatID int64) (time.Time, bool) {
	s.mu.Lock()
	defer s.mu.Unlock()
	v, ok := s.st.LastSentAt[fmt.Sprintf("%d", chatID)]
	if !ok || strings.TrimSpace(v) == "" {
		return time.Time{}, false
	}
	t, err := time.Parse(time.RFC3339, v)
	if err != nil {
		return time.Time{}, false
	}
	return t, true
}

func (s *stateStore) MarkSent(chatID int64, reportID string, sentAt time.Time) {
	s.mu.Lock()
	defer s.mu.Unlock()
	key := fmt.Sprintf("%d", chatID)
	s.st.LastReport[key] = reportID
	s.st.LastSentAt[key] = sentAt.UTC().Format(time.RFC3339)
}
