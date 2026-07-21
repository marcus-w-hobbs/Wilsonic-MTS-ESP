# cpp_receipts: compiles the plugin's REAL Microtone/Fraction/WilsonicMath
# against stub headers (same technique as tests/Makefile) and runs the
# characterization cases. Zero plugin files modified.
#
# Microtone.cpp is copied verbatim into build/ before compiling so that its
# quoted #include "WilsonicAppSkin.h" resolves to the local stub instead of
# the JUCE-heavy real header (quoted includes search the includer's own
# directory first). The `cmp` in the build rule is the receipt that the
# compiled file is byte-identical to the repo's Source/Microtone.cpp.

CXX = g++
SRC = ../../../Source
CXXFLAGS = -std=c++17 -I. -I$(SRC) -Wall -Wextra
TARGET = receipts

all: $(TARGET)

build/Microtone_verbatim.cpp: $(SRC)/Microtone.cpp
	mkdir -p build
	cp $(SRC)/Microtone.cpp $@
	cmp $(SRC)/Microtone.cpp $@

$(TARGET): receipts_main.cpp build/Microtone_verbatim.cpp $(SRC)/Fraction.cpp $(SRC)/WilsonicMath.cpp
	$(CXX) $(CXXFLAGS) $^ -o $@

run: $(TARGET)
	./$(TARGET)

clean:
	rm -rf $(TARGET) build
