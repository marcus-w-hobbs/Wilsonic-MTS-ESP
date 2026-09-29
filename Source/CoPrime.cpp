/* ==============================================================================
 
 CoPrime.cpp
 Created: 23 Apr 2023 12:39:35pm
 Author:  Marcus W. Hobbs
 
 ==============================================================================
 */

#include "CoPrime.h"
#include "Rhombus.h"
#include "AppTuningModel.h"
#include "WilsonicProcessor.h"
#include "WilsonicProcessorConstants.h"

#pragma mark - GCD

unsigned long CoPrime::GCD(unsigned long a, unsigned long b) {
    auto const retVal = gcd(a, b);
    
    return retVal;
}

#pragma mark - static members

const StringArray CoPrime::__displayModeNames {
    "Subharmonic",
    "Triangle",
    "Harmonic"
};

#pragma mark - lifecycle

CoPrime::CoPrime() {
    //
    setCanNPOOverride(false); // would break keyboard if true
    setNPOOverrideEnable(false);
    setCanSort(false);
    setSort(false);
    setOctaveReduce(false);
    setOctaveRepeat(true);
    setNoteNumberMiddleC(60);
    setCanUniquify(false);
    setUniquify(false);
    setCanScala(false);
    
    //
    _s = 1;
    _t = 1;
    _a = 0;
    _b = 1;
    _c = 1;
    _d = 0;
    _numX = 9;
    _numY = 9;
    _displayMode = DisplayMode::Triangle;
    
    // 2d array
    _cpgArray = vector<vector<CoPrimeMicrotone_p>>(static_cast<unsigned long>(getMaxX()),
                                                   vector<CoPrimeMicrotone_p>(static_cast<unsigned long>(getMaxY()),
                                                                              make_shared<CoPrimeMicrotone>(1, 1, Microtone::Space::Linear, TuningConstants::defaultOctave)));
    
    //
    _updateCPG();
}

#pragma mark - public methods

void CoPrime::setDisplayMode(CoPrime::DisplayMode new_mode) {
    if (_displayMode != new_mode) {
        _displayMode = new_mode;
        _updateCPG();
    }
}

const int CoPrime::getDisplayMode() {
    return static_cast<const int>(_displayMode);
}

CoPrimeMicrotone_p CoPrime::getMicrotoneAtXY(unsigned long x, unsigned long y) {
    jassert(x <= getMaxX());
    jassert(y <= getMaxY());
    auto cpgmt = _cpgArray[x][y];
    
    return cpgmt;
}

unsigned long CoPrime::getA() const {
    return _a;
}

unsigned long CoPrime::getB() const {
    return _b;
}

unsigned long CoPrime::getC() const {
    return _c;
}

unsigned long CoPrime::getD() const {
    return _d;
}

unsigned long CoPrime::getS() const {
    return _s;
}

unsigned long CoPrime::getT() const {
    return _t;
}

unsigned long CoPrime::getX() const {
    return _numX;
}

unsigned long CoPrime::getY() const {
    return _numY;
}

void CoPrime::setA(unsigned long value) {
    const ScopedLock sl(_lock);
    _a = jlimit(static_cast<unsigned long>(getMinA()), static_cast<unsigned long>(getMaxA()), value);
    _updateCPG();
}

void CoPrime::setB(unsigned long value) {
    const ScopedLock sl(_lock);
    _b = jlimit(static_cast<unsigned long>(getMinB()), static_cast<unsigned long>(getMaxB()), value);
    _updateCPG();
}

void CoPrime::setC(unsigned long value) {
    const ScopedLock sl(_lock);
    _c = jlimit(static_cast<unsigned long>(getMinC()), static_cast<unsigned long>(getMaxC()), value);
    _updateCPG();
}

void CoPrime::setD(unsigned long value) {
    const ScopedLock sl(_lock);
    _d = jlimit(static_cast<unsigned long>(getMinD()), static_cast<unsigned long>(getMaxD()), value);
    _updateCPG();
}

void CoPrime::setS(unsigned long value) {
    const ScopedLock sl(_lock);
    _s = jlimit(static_cast<unsigned long>(getMinS()), static_cast<unsigned long>(getMaxS()), value);
    _updateCPG();
}

void CoPrime::setT(unsigned long value) {
    const ScopedLock sl(_lock);
    _t = jlimit(static_cast<unsigned long>(getMinT()), static_cast<unsigned long>(getMaxT()), value);
    _updateCPG();
}

void CoPrime::setX(unsigned long value) {
    const ScopedLock sl(_lock);
    _numX = jlimit(static_cast<unsigned long>(getMinX()), static_cast<unsigned long>(getMaxX()), value);
    _updateCPG();
}

void CoPrime::setY(unsigned long value) {
    const ScopedLock sl(_lock);
    _numY = jlimit(static_cast<unsigned long>(getMinY()), static_cast<unsigned long>(getMaxY()), value);
    _updateCPG();
}

#pragma mark - _udpateCPG

void CoPrime::_updateCPG() {
    const ScopedLock sl(_lock);
    
    // UPDATE
    // don't call _cpgArray.clear().  It removes the inner array.
    for (auto i = 0UL; i < static_cast<unsigned long>(getMaxX()); i++) {
        for (auto j = 0UL; j < static_cast<unsigned long>(getMaxY()); j++) {
            _cpgArray[i][j] = nullptr;
        }
    }
    
    MicrotoneArray microtoneArray;
    auto noteNumber = 0UL;
    for (auto y = 0UL; y < _numY; y++) {
        for (auto x = 0UL; x < _numX; x++) {
            unsigned long xx = x;
            unsigned long yy = y;
            if (_displayMode == DisplayMode::Harmonic || _displayMode == DisplayMode::Triangle) {
                yy = _numY - y - 1;
            } else { // subharmonic
                xx = y;
                yy = _numX - x - 1;
            }
            
            // I fact-checked this with Erv's diagrams:
            unsigned long numerator = _s + yy * _a + xx * _c;
            unsigned long denominator = _t + yy * _b + xx * _d;
            string desc = ""; // will be overwritten by designated initializer as num/den
            CoPrimeMicrotone_p m = make_shared<CoPrimeMicrotone>(numerator, denominator, Microtone::Space::Linear);
            m->setX(x); // must use x, not xx
            m->setY(y); // must use y, not yy
            m->setNoteNumber(noteNumber);
            if(getOctaveReduce()) {
                m->octaveReduce();
            }
            _cpgArray[x][y] = m;
            microtoneArray.addMicrotone(m);
            //DBG ("_updateCPG: (" + String(m->getX()) + ", " + String(m->getY())+"): " + String(m->getNumerator()) + "/" + String(m->getDenominator()) + ":" + m->getShortDescriptionText() + " " + m->getShortDescriptionText2() + " " + m->getShortDescriptionText3());
            noteNumber++;
        }
    }
    
    // DESC
    string type = "";
    switch (_displayMode) {
        case DisplayMode::Subharmonic:
            type = "Subharmonic";
            break;
        case DisplayMode::Triangle:
            type = "Diamond";
            break;
        case DisplayMode::Harmonic:
            type = "Harmonic";
            break;
        default:
            jassertfalse;
            break;
    }
    setTuningDescription("(" + to_string(_a) + "/" + to_string(_b) + ")x(" + to_string(_c) + "/" + to_string(_d) + ")+(" + to_string(_s) + "," + to_string(_t) + ") " + type);
    
    // UPDATE
    setMicrotoneArray(microtoneArray); // calls _update(), which calls completion block
}

#pragma mark - drawing

bool CoPrime::canPaintTuning() {
    return true;
}

void CoPrime::paint(WilsonicProcessor& processor, Graphics& g, Rectangle<int> bounds) {
    const ScopedLock sl(_lock);
    
    // Draw non-coprime microtones first, so that the thicker coprime is on top
    for (auto x = 0UL; x < _numX; x++) {
        for (auto y = 0UL; y < _numY; y++) {
            CoPrimeMicrotone_p microtone = getMicrotoneAtXY(x, y);
            if (!microtone->isCoPrime()) {
                _commonDrawingForRect(processor, g, bounds, microtone, 0.f);
            }
        }
    }
    
    // draw thicker co-prime microtones
    for (auto x = 0UL; x < _numX; x++) {
        for (auto y = 0UL; y < _numY; y++) {
            CoPrimeMicrotone_p microtone = getMicrotoneAtXY(x, y);
            if (microtone->isCoPrime()) {
                _commonDrawingForRect(processor, g, bounds, microtone, 0.f);
            }
        }
    }
        
#if JucePlugin_IsSynth
    // optimization
    auto vs = processor.getVoiceStates();
    if (vs.noVoicesPlaying()) {
        return;
    }
    
    // call common drawing for x,y of playing non-coprime microtone
    for (unsigned long i = 0; i < WilsonicProcessorConstants::numVoices; i++) {
        // keyboard note states
        auto v = vs.voiceState[i];
        auto nnv = v.nn;
        auto vmag = v.rms;
        
        // only render if the velocity is above tolerance
        if (vmag > 0) {
            // get the microtone of the app tuning (implies the global, i.e., keyboard's tuning)
            auto mtv = processor.getAppTuningModel()->getTuning()->microtoneAtNoteNumber(nnv);
            if (CoPrimeMicrotone_p mtc = dynamic_pointer_cast<CoPrimeMicrotone>(mtv)) {
                if(mtc->getFilterNote())
                    continue;
                _commonDrawingForRect(processor, g, bounds, mtc, 12.f * vmag);
            } else {
                DBG("Can't cast to CoPrimeMicrotone");
            }
        }
    }
#elif JucePlugin_IsMidiEffect
    for (unsigned long i = 0; i < WilsonicProcessorConstants::numMidiNotes; i++) {
        float const rms = processor.getKeyboardRMSForNN(i);
        if (rms > 0.f) {
            auto mtv = processor.getAppTuningModel()->getTuning()->microtoneAtNoteNumber(i);
            if (CoPrimeMicrotone_p mtc = dynamic_pointer_cast<CoPrimeMicrotone>(mtv)) {
                if(mtc->getFilterNote())
                    continue;
                _commonDrawingForRect(processor, g, bounds, mtc, 12.f * rms);
            } else {
                DBG("Can't cast to CoPrimeMicrotone");
            }
        }
    }
#else
    jassertfalse;
#endif
}

void CoPrime::_commonDrawingForRect(WilsonicProcessor& processor,
                                    Graphics& g,
                                    const Rectangle<int>& bounds,
                                    CoPrimeMicrotone_p microtone,
                                    float velocityMag)
{
    // TUNING SPACE: x,y are 0-based indices
    unsigned long x = microtone->getX();
    unsigned long y = microtone->getY();
    float x0 = static_cast<float>(x    ) / static_cast<float>(_numX);
    float x1 = static_cast<float>(x + 1) / static_cast<float>(_numX);
    float y0 = static_cast<float>(y    ) / static_cast<float>(_numY);
    float y1 = static_cast<float>(y + 1) / static_cast<float>(_numY);
    
    // RHOMBUS, tuning space
    Rhombus rhombusTuning = Rhombus::make(x0, y0, x1, y1);
    AffineTransform tuningSpaceToDeviceSpaceTransform = tuningSpaceToDeviceSpaceForSize(bounds);
    
    // RHOMBUS, device space
    Rhombus rhombusDevice = rhombusTuning.transformedBy(tuningSpaceToDeviceSpaceTransform);
    bool containsRhombus = Rhombus::rectContainsRhombus(bounds, rhombusDevice);
    microtone->setIsClipped(!containsRhombus);
    auto const nnOutOfRange =  microtone->getNoteNumber() + getNoteNumberMiddleC() > (WilsonicProcessorConstants::numMidiNotes - 1);
    if(containsRhombus) {
        // FILL Rhombus based on CoPrime and isPlaying
        float const p01 = microtone->getPitchValue01();
        auto ca = 0.f;
        if (!microtone->isCoPrime()) { // <<===== differentiator
            ca = -3.f;
        }
        if (velocityMag > 0.f) {
            ca += velocityMag;
        }
        auto fillColor = processor.getAppTuningModel()->colorForPitch01(p01, 1.f, ca);
        if(nnOutOfRange) {
            fillColor = Colours::dimgrey;
        }
        g.setColour(fillColor);
        rhombusDevice.fillRhombus(g);
        
        // STROKE Rhombus
        auto color = microtone->isCoPrime() ? Colours::white : Colours::grey; // <<== differentiator
        if(nnOutOfRange) {
            color = Colours::grey;
        }
        g.setColour(color);
        auto const lineThickness = microtone->isCoPrime() ? 2.f : 1.f;
        rhombusDevice.strokeRhombus(g, lineThickness);
        
        // LABEL
        g.setColour(Colours::black);
        string labelStr = to_string(microtone->getNumerator()) + "/" + to_string(microtone->getDenominator());
        auto fontHeight = 1.5f * 14.f;
        g.setFont(Font(FontOptions(fontHeight)));
        auto tr0 = Rectangle<int>(0, 0, 80, 50).withCentre(rhombusDevice.getMidpoint().roundToInt());
        g.drawText(labelStr, tr0, Justification::centred);
    }
}

#pragma mark - Mouse

// return starts at middleC
int CoPrime::cpgnnForDeviceSpace(Point<int> xy, Rectangle<int>viewSize) {
    auto xyf = Point<float>(static_cast<float>(xy.x), static_cast<float>(xy.y));
    auto xfm = deviceSpaceToTuningSpaceForSize(viewSize);
    xfm.transformPoint(xyf.x, xyf.y);
    auto const midpointFactorX = 1.f;
#if JUCE_IOS || JUCE_ANDROID
    auto const midpointFactorY = 1.f + (0.25f * 1.f / _numY);
#else
    auto const midpointFactorY = 1.f;
#endif
    auto x01 = midpointFactorX * xyf.x;
    auto y01 = midpointFactorY * xyf.y;
    x01 = jlimit(0.f, 0.999f, x01);
    y01 = jlimit(0.f, 0.999f, y01);
    auto x = static_cast<unsigned long>(x01 * _numX); // 0-based index
    x = jlimit(0UL, static_cast<unsigned long>(CoPrime::getMaxX()-1), x); // 0-based index
    auto y = static_cast<unsigned long>(y01 * _numY); // 0-based index
    y = jlimit(0UL, static_cast<unsigned long>(CoPrime::getMaxY()-1), y); // 0-based index
    CoPrimeMicrotone_p microtone = getMicrotoneAtXY(x, y);
    if (microtone != nullptr) {
        auto const nn = static_cast<int>(microtone->getNoteNumber() + getNoteNumberMiddleC());
        
        //DBG ("CoPrime::nnForDeviceSpace: Point xy:("+String(xy.x)+","+String(xy.y)+"), viewSize:("+String(viewSize.getWidth())+","+String(viewSize.getHeight())+", xfmdpoint:("+String(xyf.x)+","+String(xyf.y)+"), final xy:("+String(x)+","+String(y)+"), final nn:"+String(nn));
        return nn;
    } else {
        //DBG ("CoPrime::nnForDeviceSpace: Point xy:("+String(xy.x)+","+String(xy.y)+"), viewSize:("+String(viewSize.getWidth())+","+String(viewSize.getHeight())+", xfmdpoint:("+String(xyf.x)+","+String(xyf.y)+"), final xy:("+String(x)+","+String(y)+"), final nn:-1");
        return static_cast<int>(-1);
    }
    
    jassertfalse;
    return static_cast<int>(-1);
}

#pragma mark - Transforms

AffineTransform CoPrime::tuningSpaceToDeviceSpaceForSize(const Rectangle<int>& viewSize) {
    float const width = viewSize.getWidth();
    float const height = viewSize.getHeight();
    auto trs = AffineTransform();
    switch (_displayMode) {
        case DisplayMode::Subharmonic:
        case DisplayMode::Harmonic:
        {
            float const s = 0.95f;
            trs = trs.translated(-0.5f, -0.5f);
            trs = trs.scaled(s * width, -s * height);
            trs = trs.translated(0.5f * width + 0.5f, 0.5f * height + 0.5f);
        }
            break;
        case DisplayMode::Triangle:
        {
            float const s = 0.618f;
            trs = trs.translated(-0.5f, -0.5f);
            trs = trs.scaled(-1.f, 1.f);
            trs = trs.rotated(degreesToRadians(225.f));
            float const tweak = 1.7f;
            trs = trs.scaled(s * width, tweak * s * height);
            trs = trs.translated(0.5f * width + 0.5f, tweak * 0.5f * height + 0.5f);
        }
            break;
        default:
            DBG("ERROR: CoPrimeGridDisplayModeUndefined");
            jassertfalse;
            break;
    }
    
    return trs;
}

AffineTransform CoPrime::deviceSpaceToTuningSpaceForSize(const Rectangle<int>& viewSize) {
    AffineTransform ts = tuningSpaceToDeviceSpaceForSize(viewSize);
    AffineTransform retVal = ts.inverted();
    
    return retVal;
}

#pragma mark - Scala

String CoPrime::defaultScalaName() {
    return "CoPrime";
}

String CoPrime::scalaComments() {
    return "Generated by CoPrime class";
}
