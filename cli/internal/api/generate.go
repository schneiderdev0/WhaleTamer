package api

import (
	"bytes"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
)

// GenerateRequest — тело запроса на /generate.
type GenerateRequest struct {
	ProjectStructure string          `json:"project_structure"`
	Format           string          `json:"format,omitempty"` // "tree" | "markdown"
	ProjectContext   *ProjectContext `json:"project_context,omitempty"`
}

// ProjectContext — дополнительный контекст проекта для более точной генерации.
type ProjectContext struct {
	Paths       []string          `json:"paths,omitempty"`
	Manifests   map[string]string `json:"manifests,omitempty"`
	Snippets    map[string]string `json:"snippets,omitempty"`
	Entrypoints []string          `json:"entrypoints,omitempty"`
	Commands    []string          `json:"commands,omitempty"`
}

// FileContent — один файл в ответе бекенда.
type FileContent struct {
	Path    string `json:"path"` // например "Dockerfile", "backend/Dockerfile", "docker-compose.yaml"
	Content string `json:"content"`
}

// GenerateResponse — ответ API /generate.
type GenerateResponse struct {
	Files []FileContent `json:"files"`
}

// Generate вызывает POST /generate и возвращает список файлов с содержимым.
func Generate(apiBase, token, projectStructure, format string, context *ProjectContext) (*GenerateResponse, error) {
	if format == "" {
		format = "tree"
	}
	body := GenerateRequest{
		ProjectStructure: projectStructure,
		Format:           format,
		ProjectContext:   context,
	}
	raw, err := json.Marshal(body)
	if err != nil {
		return nil, err
	}

	url := apiBase + "/generate"
	req, err := http.NewRequest(http.MethodPost, url, bytes.NewReader(raw))
	if err != nil {
		return nil, err
	}
	req.Header.Set("Authorization", "Bearer "+token)
	req.Header.Set("Content-Type", "application/json")

	client := &http.Client{}
	resp, err := client.Do(req)
	if err != nil {
		return nil, err
	}
	defer resp.Body.Close()

	respBody, err := io.ReadAll(resp.Body)
	if err != nil {
		return nil, err
	}
	if resp.StatusCode != http.StatusOK {
		return nil, fmt.Errorf("API вернул %s: %s", resp.Status, string(respBody))
	}

	var out GenerateResponse
	if err := json.Unmarshal(respBody, &out); err != nil {
		return nil, fmt.Errorf("разбор ответа: %w", err)
	}
	return &out, nil
}
