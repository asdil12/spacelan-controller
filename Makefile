.PHONEY: build install compiledb

build:
	platformio run

install:
	platformio run --t upload

# for neovim
compiledb:
	platformio run -t compiledb
