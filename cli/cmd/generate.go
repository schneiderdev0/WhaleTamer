package cmd

import (
	"fmt"
	"os"
	"path/filepath"

	"github.com/spf13/cobra"
	"github.com/whaletamer/cli/internal/api"
	"github.com/whaletamer/cli/internal/files"
	"github.com/whaletamer/cli/internal/project"
)

var (
	outputFormat  string // "tree" | "markdown"
	saveStructure string // путь к файлу для сохранения структуры (пусто = не сохранять)
	projectRoot   string
)

var generateCmd = &cobra.Command{
	Use:   "generate",
	Short: "Сгенерировать Dockerfile и docker-compose по структуре проекта",
	Long: `Собирает структуру проекта (дерево или Markdown), сохраняет её при необходимости,
отправляет на API /generate и создаёт полученные Dockerfile и docker-compose файлы.`,
	RunE: runGenerate,
}

func init() {
	generateCmd.Flags().StringVarP(&outputFormat, "format", "f", "tree", "Формат структуры: tree | markdown")
	generateCmd.Flags().StringVarP(&saveStructure, "save-structure", "s", "", "Сохранить структуру в файл (например project-structure.md или structure.txt)")
	generateCmd.Flags().StringVarP(&projectRoot, "project-root", "p", ".", "Корень проекта")
}

func runGenerate(cmd *cobra.Command, args []string) error {
	root, err := filepath.Abs(projectRoot)
	if err != nil {
		return err
	}
	if _, err := os.Stat(root); os.IsNotExist(err) {
		return fmt.Errorf("директория не существует: %s", root)
	}

	var structure string
	switch outputFormat {
	case "tree":
		structure, err = project.BuildTree(root)
	case "markdown":
		structure, err = project.BuildTreeMarkdown(root)
	default:
		return fmt.Errorf("неизвестный формат: %s (используйте tree или markdown)", outputFormat)
	}
	if err != nil {
		return fmt.Errorf("построение структуры: %w", err)
	}

	if saveStructure != "" {
		if err := os.WriteFile(saveStructure, []byte(structure), 0644); err != nil {
			return fmt.Errorf("сохранение структуры в %s: %w", saveStructure, err)
		}
		fmt.Fprintf(os.Stderr, "Структура сохранена в %s\n", saveStructure)
	}

	ctx, err := project.BuildContext(root)
	if err != nil {
		return fmt.Errorf("сбор контекста проекта: %w", err)
	}
	reqContext := &api.ProjectContext{
		Paths:       ctx.Paths,
		Manifests:   ctx.Manifests,
		Entrypoints: ctx.Entrypoints,
		Commands:    ctx.Commands,
	}

	resp, err := api.Generate(apiBase, token, structure, outputFormat, reqContext)
	if err != nil {
		return err
	}

	if len(resp.Files) == 0 {
		fmt.Fprintln(os.Stderr, "API не вернул файлов для записи.")
		return nil
	}

	if err := files.WriteGeneratedFiles(root, resp.Files); err != nil {
		return fmt.Errorf("запись файлов: %w", err)
	}

	fmt.Fprintf(os.Stderr, "Создано файлов: %d\n", len(resp.Files))
	for _, f := range resp.Files {
		fmt.Println(f.Path)
	}
	return nil
}
