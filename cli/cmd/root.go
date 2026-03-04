package cmd

import (
	"fmt"
	"os"
	"strings"

	"github.com/spf13/cobra"
	"github.com/whaletamer/cli/internal/auth"
	"github.com/whaletamer/cli/internal/config"
)

var (
	token   string
	apiBase string
)

// rootCmd represents the base command
var rootCmd = &cobra.Command{
	Use:   "wt",
	Short: "Whale Tamer CLI — автоматизация Dockerfile и docker-compose",
	Long: `CLI утилита Whale Tamer для автоматического создания 
Dockerfile и docker-compose на основе структуры проекта.`,
	RunE: func(cmd *cobra.Command, args []string) error {
		// Первый запуск `wt` без подкоманды: инициализируем токен и показываем help.
		if err := ensureAuthorizedToken(true); err != nil {
			return err
		}
		return cmd.Help()
	},
}

const defaultAPIBase = "http://localhost:8000"

func getDefaultAPIBase() string {
	if u := os.Getenv("WHALETAMER_API_URL"); u != "" {
		return u
	}
	return defaultAPIBase
}

func init() {
	rootCmd.PersistentFlags().StringVarP(&token, "token", "t", "", "Токен авторизации (если не задан — запрос при первом запуске)")
	rootCmd.PersistentFlags().StringVar(&apiBase, "api", getDefaultAPIBase(), "Базовый URL API бекенда")

	// Токен нужен для команд API. Для `wt token ...` пропускаем pre-run.
	rootCmd.PersistentPreRunE = func(cmd *cobra.Command, args []string) error {
		if isTokenCommand(cmd) {
			if apiBase == "" {
				apiBase = getDefaultAPIBase()
			}
			return nil
		}
		return ensureAuthorizedToken(true)
	}
	rootCmd.AddCommand(generateCmd)
	rootCmd.AddCommand(tokenCmd)
}

func ensureAuthorizedToken(promptIfNeeded bool) error {
	if apiBase == "" {
		apiBase = getDefaultAPIBase()
	}
	// 1) Флаг --token
	if t := strings.TrimSpace(token); t != "" {
		if err := auth.ValidateToken(apiBase, t); err != nil {
			return fmt.Errorf("ошибка авторизации (флаг --token): %w", err)
		}
		token = t
		if err := config.WriteToken(token); err != nil {
			fmt.Fprintf(os.Stderr, "Предупреждение: не удалось сохранить токен: %v\n", err)
		}
		return nil
	}

	// 2) Переменная окружения
	if t := strings.TrimSpace(os.Getenv("WHALETAMER_TOKEN")); t != "" {
		if err := auth.ValidateToken(apiBase, t); err == nil {
			token = t
			return nil
		}
		fmt.Fprintln(os.Stderr, "Токен из WHALETAMER_TOKEN невалиден.")
	}

	// 3) Сохраненный токен
	if saved, err := config.ReadToken(); err == nil && strings.TrimSpace(saved) != "" {
		if err := auth.ValidateToken(apiBase, saved); err == nil {
			token = strings.TrimSpace(saved)
			return nil
		}
		fmt.Fprintln(os.Stderr, "Сохраненный токен невалиден. Введите новый токен.")
	}

	if !promptIfNeeded {
		return fmt.Errorf("токен не найден; используйте `wt token set`")
	}

	// 4) Интерактивный ввод
	prompted, err := config.PromptToken()
	if err != nil {
		return err
	}
	if prompted == "" {
		return fmt.Errorf("токен не указан")
	}
	if err := auth.ValidateToken(apiBase, prompted); err != nil {
		return fmt.Errorf("ошибка авторизации: %w", err)
	}
	token = prompted
	if err := config.WriteToken(token); err != nil {
		fmt.Fprintf(os.Stderr, "Предупреждение: не удалось сохранить токен: %v\n", err)
	} else {
		fmt.Fprintln(os.Stderr, "Токен сохранён.")
	}
	return nil
}

func isTokenCommand(cmd *cobra.Command) bool {
	for c := cmd; c != nil; c = c.Parent() {
		if c.Name() == "token" {
			return true
		}
	}
	return false
}

func Execute() {
	if err := rootCmd.Execute(); err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
}
