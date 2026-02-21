package project

import (
	"bufio"
	"encoding/json"
	"io"
	"io/fs"
	"os"
	"path/filepath"
	"sort"
	"strings"
)

const maxManifestBytes = 24 * 1024

// Context содержит сигнал для LLM помимо дерева файлов.
type Context struct {
	Paths       []string
	Manifests   map[string]string
	Entrypoints []string
	Commands    []string
}

var manifestCandidates = []string{
	"pyproject.toml",
	"requirements.txt",
	"requirements-dev.txt",
	"poetry.lock",
	"Pipfile",
	"package.json",
	"package-lock.json",
	"pnpm-lock.yaml",
	"yarn.lock",
	"go.mod",
	"Cargo.toml",
	"Gemfile",
}

var entrypointCandidates = []string{
	"main.py",
	"app.py",
	"manage.py",
	"main.ts",
	"main.js",
	"server.ts",
	"server.js",
	"index.ts",
	"index.js",
	"main.go",
}

// BuildContext собирает компактный контекст проекта для генерации.
func BuildContext(root string) (*Context, error) {
	absRoot, err := filepath.Abs(root)
	if err != nil {
		return nil, err
	}
	ctx := &Context{
		Manifests: map[string]string{},
	}
	if err := filepath.WalkDir(absRoot, func(path string, d fs.DirEntry, walkErr error) error {
		if walkErr != nil {
			return walkErr
		}
		rel, err := filepath.Rel(absRoot, path)
		if err != nil {
			return err
		}
		if rel == "." {
			return nil
		}
		base := d.Name()
		if d.IsDir() {
			if DefaultIgnore[base] || strings.HasPrefix(base, ".") {
				return filepath.SkipDir
			}
			return nil
		}
		if strings.HasPrefix(base, ".") {
			return nil
		}
		rel = filepath.ToSlash(rel)
		ctx.Paths = append(ctx.Paths, rel)
		return nil
	}); err != nil {
		return nil, err
	}
	sort.Strings(ctx.Paths)

	for _, rel := range ctx.Paths {
		base := filepath.Base(rel)
		if contains(manifestCandidates, base) {
			content, err := readAtMost(filepath.Join(absRoot, rel), maxManifestBytes)
			if err == nil && strings.TrimSpace(content) != "" {
				ctx.Manifests[rel] = content
			}
		}
		if contains(entrypointCandidates, base) || strings.HasSuffix(rel, "/main.py") || strings.HasSuffix(rel, "/app/main.py") {
			ctx.Entrypoints = append(ctx.Entrypoints, rel)
		}
	}
	ctx.Entrypoints = dedupeSorted(ctx.Entrypoints)
	ctx.Commands = dedupeSorted(collectCommandsFromManifests(ctx.Manifests))
	return ctx, nil
}

func readAtMost(path string, limit int64) (string, error) {
	f, err := os.Open(path)
	if err != nil {
		return "", err
	}
	defer f.Close()
	data, err := io.ReadAll(io.LimitReader(f, limit))
	if err != nil {
		return "", err
	}
	return string(data), nil
}

func collectCommandsFromManifests(manifests map[string]string) []string {
	var out []string
	for path, content := range manifests {
		base := filepath.Base(path)
		switch base {
		case "package.json":
			out = append(out, parsePackageJSONScripts(content)...)
		case "pyproject.toml":
			out = append(out, parsePyprojectCommands(content)...)
		}
	}
	return out
}

func parsePackageJSONScripts(content string) []string {
	var parsed struct {
		Scripts map[string]string `json:"scripts"`
	}
	if err := json.Unmarshal([]byte(content), &parsed); err != nil {
		return nil
	}
	var out []string
	for _, cmd := range parsed.Scripts {
		if strings.TrimSpace(cmd) != "" {
			out = append(out, cmd)
		}
	}
	return out
}

func parsePyprojectCommands(content string) []string {
	var out []string
	inTasks := false
	scanner := bufio.NewScanner(strings.NewReader(content))
	for scanner.Scan() {
		line := strings.TrimSpace(scanner.Text())
		if strings.HasPrefix(line, "[") && strings.HasSuffix(line, "]") {
			inTasks = line == "[tool.poe.tasks]" || line == "[project.scripts]"
			continue
		}
		if !inTasks {
			continue
		}
		if line == "" || strings.HasPrefix(line, "#") {
			continue
		}
		parts := strings.SplitN(line, "=", 2)
		if len(parts) != 2 {
			continue
		}
		val := strings.TrimSpace(parts[1])
		val = strings.Trim(val, "\"'")
		if val != "" {
			out = append(out, val)
		}
	}
	return out
}

func contains(values []string, needle string) bool {
	for _, v := range values {
		if v == needle {
			return true
		}
	}
	return false
}

func dedupeSorted(items []string) []string {
	if len(items) == 0 {
		return items
	}
	sort.Strings(items)
	out := make([]string, 0, len(items))
	last := ""
	for _, it := range items {
		if it == "" || it == last {
			continue
		}
		out = append(out, it)
		last = it
	}
	return out
}
