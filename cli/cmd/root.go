package cmd

import (
	"fmt"
	"os"

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

	// Требуем токен для всех команд: флаг > env > сохранённый файл > запрос при запуске
	rootCmd.PersistentPreRunE = func(cmd *cobra.Command, args []string) error {
		if apiBase == "" {
			apiBase = getDefaultAPIBase()
		}
		if token == "" {
			token = os.Getenv("WHALETAMER_TOKEN")
		}
		if token == "" {
			if saved, err := config.ReadToken(); err == nil && saved != "" {
				token = saved
			}
		}
		if token == "" {
			fmt.Fprintln(os.Stderr, "Токен не найден. Введите его один раз — он будет сохранён для следующих запусков.")
			prompted, err := config.PromptToken()
			if err != nil {
				return err
			}
			if prompted == "" {
				return fmt.Errorf("токен не указан")
			}
			token = prompted
			if err := config.WriteToken(token); err != nil {
				fmt.Fprintf(os.Stderr, "Предупреждение: не удалось сохранить токен: %v\n", err)
			} else {
				fmt.Fprintln(os.Stderr, "Токен сохранён.")
			}
		}
		if err := auth.ValidateToken(apiBase, token); err != nil {
			return fmt.Errorf("ошибка авторизации: %w", err)
		}
		return nil
	}
	rootCmd.AddCommand(generateCmd)
}

func Execute() {
	if err := rootCmd.Execute(); err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
}
