package cmd

import (
	"fmt"
	"os"
	"strings"

	"github.com/spf13/cobra"
	"github.com/whaletamer/cli/internal/auth"
	"github.com/whaletamer/cli/internal/config"
)

var tokenCmd = &cobra.Command{
	Use:   "token",
	Short: "Управление сохраненным CLI-токеном",
}

var tokenSetCmd = &cobra.Command{
	Use:   "set [TOKEN]",
	Short: "Установить или перезаписать токен",
	Args:  cobra.MaximumNArgs(1),
	RunE: func(cmd *cobra.Command, args []string) error {
		if apiBase == "" {
			apiBase = getDefaultAPIBase()
		}
		var newToken string
		if len(args) > 0 {
			newToken = strings.TrimSpace(args[0])
		} else {
			prompted, err := config.PromptToken()
			if err != nil {
				return err
			}
			newToken = strings.TrimSpace(prompted)
		}
		if newToken == "" {
			return fmt.Errorf("токен не указан")
		}
		if err := auth.ValidateToken(apiBase, newToken); err != nil {
			return fmt.Errorf("не удалось сохранить токен: %w", err)
		}
		if err := config.WriteToken(newToken); err != nil {
			return fmt.Errorf("ошибка записи токена: %w", err)
		}
		token = newToken
		fmt.Fprintln(os.Stderr, "Токен сохранён.")
		return nil
	},
}

func init() {
	tokenCmd.AddCommand(tokenSetCmd)
}
