PYTHON ?= python3
VARIANTS ?= 10 12 14
BUILD_FLAGS ?=
.PHONY: check render audit update build test record
check:
	$(PYTHON) scripts/check.py
	$(PYTHON) -m unittest discover -s tests
render:
	$(PYTHON) scripts/render.py
audit:
	$(PYTHON) scripts/update.py
	$(PYTHON) scripts/audit.py
update:
	$(PYTHON) scripts/update.py --write --resolve --features
	$(PYTHON) scripts/audit.py --write
build:
	$(PYTHON) scripts/build.py --variants $(VARIANTS) $(BUILD_FLAGS)
test:
	$(PYTHON) scripts/build.py --variants $(VARIANTS) --test $(BUILD_FLAGS)
record:
	$(PYTHON) scripts/record.py

# Requires a completed native build/test with the same image ID.
security:
	$(PYTHON) scripts/security.py --variant $(VARIANT) --arch $(ARCH)
