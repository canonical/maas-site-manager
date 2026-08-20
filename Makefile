.DEFAULT_GOAL := ci-build

# Uncomment and use if statement in directive below to determine if changes were
# made in frontend or backend once we have visibility of the main branch in lpci
# TOP_LEVEL_CHANGES := $(shell git diff-tree --no-commit-id --name-only -r main HEAD | cut -d/ -f1| sort | uniq)

install-dependencies ci-dep ci-build ci-lint ci-test:
	$(MAKE) -C backend $@
	$(MAKE) -C frontend $@
.PHONY: install-dependencies ci-dep ci-build ci-lint ci-test

e2e-dep e2e-test:
	$(MAKE) -C frontend $@
.PHONY: e2e-dep e2e-test

# run by the build-env-prepare job
ci-dep-docker-prepare:
	$(MAKE) -C backend ci-dep
	$(MAKE) -C frontend ci-dep
	chmod -R a+w /var/cache/yarn || true
.PHONY: ci-dep-docker-prepare


rock:
	rockcraft pack -v
.PHONY: rock

rock-clean:
	rockcraft clean
	rm -f maas-site-manager_*.rock
.PHONY: rock-clean
