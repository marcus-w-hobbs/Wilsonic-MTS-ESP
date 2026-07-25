# Standalone unit tests: compile REAL Source/*.cpp files against the stub
# JuceHeader.h (no JUCE framework needed). Run by CI (.github/workflows/
# plugin.yml) and locally via `make -C tests run`.
#
# Some Source files quote-include "WilsonicAppSkin.h" (JUCE-heavy). Quoted
# includes search the includer's directory first, so those files are copied
# verbatim into build/ where the stub WilsonicAppSkin.h (-I.) wins instead.
# The `cmp` proves each copy is byte-identical to the repo source.

CXX = g++
SRC = ../Source
CXXFLAGS = -std=c++17 -I. -I$(SRC) -DJucePlugin_IsSynth=1 -Wall -Wextra
TARGETS = test_wilsonicmath test_tuning
RESEARCH_CLI = research_cli

CORE_SRCS = \
	paint_stubs.cpp \
	build/Microtone_verbatim.cpp \
	build/BrunTuning_verbatim.cpp \
	build/BrunGral_verbatim.cpp \
	$(SRC)/Fraction.cpp \
	$(SRC)/WilsonicMath.cpp \
	$(SRC)/MicrotoneArray.cpp \
	$(SRC)/TuningImp.cpp \
	$(SRC)/TuningTableImp.cpp \
	$(SRC)/PythagoreanMeans.cpp \
	$(SRC)/BrunMicrotone.cpp \
	$(SRC)/Brun.cpp \
	$(SRC)/ScalaFile.cpp \
	$(SRC)/ScalaFileScl.cpp \
	$(SRC)/ScalaFileKbm.cpp \
	$(SRC)/ScalaFileDegree.cpp

all: $(TARGETS)

test_wilsonicmath: test_wilsonicmath.cpp $(SRC)/WilsonicMath.cpp
	$(CXX) $(CXXFLAGS) $^ -o $@

build/Microtone_verbatim.cpp: $(SRC)/Microtone.cpp
	mkdir -p build
	cp $< $@
	cmp $< $@

build/BrunTuning_verbatim.cpp: $(SRC)/Brun+Tuning.cpp
	mkdir -p build
	cp $< $@
	cmp $< $@

build/BrunGral_verbatim.cpp: $(SRC)/Brun+Gral.cpp
	mkdir -p build
	cp $< $@
	cmp $< $@

test_tuning: test_tuning.cpp $(CORE_SRCS)
	$(CXX) $(CXXFLAGS) $^ -o $@

# Headless research tool (built on demand, not part of `run`): emits real
# scale generation + analyzer counts as JSON for experiments/triads/.
$(RESEARCH_CLI): research_cli.cpp $(CORE_SRCS)
	$(CXX) $(CXXFLAGS) $^ -o $@

run: $(TARGETS)
	./test_wilsonicmath
	./test_tuning

clean:
	rm -rf $(TARGETS) $(RESEARCH_CLI) build
