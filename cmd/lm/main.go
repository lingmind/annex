package main

import (
	"os"

	"github.com/lingmind/annex/internal/cli"
)

func main() {
	os.Exit(cli.Main(os.Args))
}
