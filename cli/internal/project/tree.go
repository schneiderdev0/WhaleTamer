package project

import (
	"os"
	"path/filepath"
	"strings"
)

// DefaultIgnore — каталоги и файлы, исключаемые из дерева (как в .gitignore).
var DefaultIgnore = map[string]bool{
	".git": true, "node_modules": true, ".venv": true, "venv": true,
	"__pycache__": true, ".idea": true, ".vscode": true, "vendor": true,
	"dist": true, "build": true, ".next": true, ".nuxt": true,
}

// BuildTree строит текстовое дерево структуры проекта (как tree).
// root — корневая директория (обычно ".").
func BuildTree(root string) (string, error) {
	var b strings.Builder
	absRoot, err := filepath.Abs(root)
	if err != nil {
		return "", err
	}
	baseName := filepath.Base(absRoot)
	if baseName == "." {
		baseName = "."
	}
	b.WriteString(baseName + "\n")
	err = walkTree(&b, absRoot, "", true, DefaultIgnore)
	return b.String(), err
}

func walkTree(b *strings.Builder, dir, prefix string, isLast bool, ignore map[string]bool) error {
	entries, err := os.ReadDir(dir)
	if err != nil {
		return err
	}
	var dirs, files []os.DirEntry
	for _, e := range entries {
		name := e.Name()
		if ignore[name] || strings.HasPrefix(name, ".") && name != "." && name != ".." {
			continue
		}
		if e.IsDir() {
			dirs = append(dirs, e)
		} else {
			files = append(files, e)
		}
	}
	all := append(dirs, files...)
	for i, e := range all {
		last := i == len(all)-1
		connector := "├── "
		nextPrefix := "│   "
		if last {
			connector = "└── "
			nextPrefix = "    "
		}
		b.WriteString(prefix + connector + e.Name() + "\n")
		if e.IsDir() {
			subDir := filepath.Join(dir, e.Name())
			if err := walkTree(b, subDir, prefix+nextPrefix, last, ignore); err != nil {
				return err
			}
		}
	}
	return nil
}

// BuildTreeMarkdown строит структуру в формате Markdown (вложенные списки).
func BuildTreeMarkdown(root string) (string, error) {
	var b strings.Builder
	absRoot, err := filepath.Abs(root)
	if err != nil {
		return "", err
	}
	baseName := filepath.Base(absRoot)
	if baseName == "." {
		baseName = "."
	}
	b.WriteString("- " + baseName + "\n")
	err = walkTreeMarkdown(&b, absRoot, "  ", DefaultIgnore)
	return b.String(), err
}

func walkTreeMarkdown(b *strings.Builder, dir, indent string, ignore map[string]bool) error {
	entries, err := os.ReadDir(dir)
	if err != nil {
		return err
	}
	var dirs, files []os.DirEntry
	for _, e := range entries {
		name := e.Name()
		if ignore[name] || (strings.HasPrefix(name, ".") && name != "." && name != "..") {
			continue
		}
		if e.IsDir() {
			dirs = append(dirs, e)
		} else {
			files = append(files, e)
		}
	}
	for _, e := range dirs {
		b.WriteString(indent + "- " + e.Name() + "/\n")
		subDir := filepath.Join(dir, e.Name())
		if err := walkTreeMarkdown(b, subDir, indent+"  ", ignore); err != nil {
			return err
		}
	}
	for _, e := range files {
		b.WriteString(indent + "- " + e.Name() + "\n")
	}
	return nil
}
