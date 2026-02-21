package config

import (
	"bufio"
	"fmt"
	"os"
	"path/filepath"
	"strings"
)

const configDirName = "whaletamer"
const tokenFileName = "token"

// TokenPath returns the path to the file where the token is stored.
func TokenPath() (string, error) {
	dir, err := os.UserConfigDir()
	if err != nil {
		dir, err = os.UserHomeDir()
		if err != nil {
			return "", err
		}
		dir = filepath.Join(dir, ".config")
	}
	return filepath.Join(dir, configDirName, tokenFileName), nil
}

// ReadToken reads the stored token from disk. Returns empty string if file does not exist or cannot be read.
func ReadToken() (string, error) {
	p, err := TokenPath()
	if err != nil {
		return "", err
	}
	data, err := os.ReadFile(p)
	if err != nil {
		if os.IsNotExist(err) {
			return "", nil
		}
		return "", err
	}
	return strings.TrimSpace(string(data)), nil
}

// WriteToken saves the token to disk, creating the config directory if needed.
func WriteToken(token string) error {
	p, err := TokenPath()
	if err != nil {
		return err
	}
	dir := filepath.Dir(p)
	if err := os.MkdirAll(dir, 0700); err != nil {
		return err
	}
	return os.WriteFile(p, []byte(strings.TrimSpace(token)+"\n"), 0600)
}

// PromptToken asks the user for the token on stdin and returns it.
func PromptToken() (string, error) {
	fmt.Fprint(os.Stderr, "Введите токен авторизации: ")
	scanner := bufio.NewScanner(os.Stdin)
	if !scanner.Scan() {
		if err := scanner.Err(); err != nil {
			return "", err
		}
		return "", fmt.Errorf("ввод отменён")
	}
	return strings.TrimSpace(scanner.Text()), nil
}
