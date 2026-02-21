package files

import (
	"os"
	"path/filepath"

	"github.com/whaletamer/cli/internal/api"
)

// WriteGeneratedFiles создаёт файлы из ответа API (Dockerfile, docker-compose и т.д.).
// rootDir — корень проекта, куда писать (для относительных path в FileContent).
func WriteGeneratedFiles(rootDir string, files []api.FileContent) error {
	for _, f := range files {
		fpath := filepath.Join(rootDir, f.Path)
		dir := filepath.Dir(fpath)
		if err := os.MkdirAll(dir, 0755); err != nil {
			return err
		}
		if err := os.WriteFile(fpath, []byte(f.Content), 0644); err != nil {
			return err
		}
	}
	return nil
}
