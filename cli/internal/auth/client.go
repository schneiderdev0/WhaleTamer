package auth

import (
	"bytes"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"strings"
)

// ValidateToken отправляет POST /auth/cli-tokens/verify с телом {"token": "..."}.
func ValidateToken(apiBase, token string) error {
	token = strings.TrimSpace(token)
	if token == "" {
		return fmt.Errorf("токен пустой")
	}
	body := map[string]string{"token": token}
	raw, err := json.Marshal(body)
	if err != nil {
		return err
	}
	url := apiBase + "/auth/cli-tokens/verify"
	req, err := http.NewRequest(http.MethodPost, url, bytes.NewReader(raw))
	if err != nil {
		return err
	}
	req.Header.Set("Content-Type", "application/json")

	client := &http.Client{}
	resp, err := client.Do(req)
	if err != nil {
		return err
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		body, _ := io.ReadAll(resp.Body)
		detail := string(body)
		if detail != "" {
			return fmt.Errorf("неверный токен или сервер вернул %s: %s", resp.Status, detail)
		}
		return fmt.Errorf("неверный токен или сервер вернул %s", resp.Status)
	}
	return nil
}
