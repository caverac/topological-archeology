TEX      = pdflatex
BIB      = bibtex
MAIN     = ms

SRCIMGS  = ../docs/static/img/results

# Labeled name  → numbered name for the pre-print
# Labeled name (in docs/static/img/results/) → numbered name for the pre-print
FIG_01   = calibration.pdf
FIG_02   = persistence-diagrams.pdf
FIG_03   = bifurcation.pdf

FIGURES  = 01.pdf 02.pdf 03.pdf

.PHONY: all clean distclean submission sync-figures

all: sync-figures $(MAIN).pdf

$(MAIN).pdf: $(MAIN).tex $(MAIN).bib $(wildcard *.tex) $(FIGURES)
	$(TEX) $(MAIN)
	$(BIB) $(MAIN)
	$(TEX) $(MAIN)
	$(TEX) $(MAIN)

sync-figures:
	@updated=0; \
	pairs="$(FIG_01):01.pdf $(FIG_02):02.pdf $(FIG_03):03.pdf"; \
	for pair in $$pairs; do \
		src=$(SRCIMGS)/$${pair%%:*}; \
		dst=$${pair##*:}; \
		if [ ! -f "$$src" ]; then \
			echo "  missing: $${pair%%:*}"; \
			continue; \
		fi; \
		if [ ! -f "$$dst" ] || ! cmp -s "$$src" "$$dst"; then \
			cp "$$src" "$$dst"; \
			updated=$$((updated + 1)); \
			echo "  updated: $${pair%%:*} → $$dst"; \
		fi; \
	done; \
	echo "Synced $$updated figure(s)"

OUTDIR   = /tmp/topological-archeology
TARFILE  = $(OUTDIR)/topo-archeo-preprint.tar

submission:
	@mkdir -p $(OUTDIR)
	@COPYFILE_DISABLE=1 tar cf $(TARFILE) $(MAIN).tex $(MAIN).bib $(MAIN).pdf $(FIGURES)
	@echo "Created $(TARFILE)"

clean:
	rm -f $(MAIN).aux $(MAIN).bbl $(MAIN).blg $(MAIN).log $(MAIN).out
	rm -f $(MAIN).fdb_latexmk $(MAIN).fls $(MAIN).synctex.gz
	rm -f $(MAIN).toc $(MAIN).lof $(MAIN).lot $(MAIN).run.xml $(MAIN).bcf

distclean: clean
	rm -f $(MAIN).pdf $(FIGURES)
