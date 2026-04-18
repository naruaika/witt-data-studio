# Witt Data Studio - Windows/MSYS2 Helper Makefile

PYTHON    = python
MESON     = meson
NINJA     = ninja
DIST_DIR  = $(shell pwd)/dist
BUILD_DIR = builddir

# Environment variables for execution
# We use export within the shell commands to ensure GTK finds its assets
RUN_ENV = export GSETTINGS_SCHEMA_DIR=$(DIST_DIR)/share/glib-2.0/schemas; \
          export PYTHONPATH=$(shell pwd)/src:$$PYTHONPATH;

.PHONY: all setup build install run clean distclean help

help:
	@echo "Witt Data Studio Build Shortcuts:"
	@echo "  make setup     - Configure meson build directory"
	@echo "  make install   - Build and install to ./dist"
	@echo "  make run       - Run the application from ./dist"
	@echo "  make clean     - Remove build artifacts"
	@echo "  make full      - Setup, install, and run in one go"

setup:
	@if [ ! -d "$(BUILD_DIR)" ]; then \
		$(MESON) setup $(BUILD_DIR) --prefix=$(DIST_DIR); \
	else \
		$(MESON) setup $(BUILD_DIR) --reconfigure --prefix=$(DIST_DIR); \
	fi

install:
	$(MESON) install -C $(BUILD_DIR)
	@# Ensure schemas are compiled even if post-install fails
	glib-compile-schemas $(DIST_DIR)/share/glib-2.0/schemas

run:
	@$(RUN_ENV) $(PYTHON) $(DIST_DIR)/bin/witt-data-studio

full: setup install run

clean:
	rm -rf $(BUILD_DIR)

distclean: clean
	rm -rf $(DIST_DIR)
	rm -rf .pyvenv