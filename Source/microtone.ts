//
// Translated from C++ Microtone.h/Microtone.cpp into TypeScript.
//
// NOTE:
// - This file inlines certain dependencies (Fraction, TuningConstants, etc.).
// - JUCE-specific classes like Path or Point<float> are replaced with simple stubs or basic equivalents.
// - Some C++-style assertions (jassert) are replaced with a helper assert() function.
// - The TuningConstants come from TuningConstants.h, but are placed here inlined.
// - The WilsonicMath / WilsonicAppSkin floatDescription are partially emulated.
// - If you need a real path rendering library, replace the Path type with something else.
// - The code attempts to preserve the original structure and logic from C++.
//

// Basic assertion helper to emulate jassert in C++.
function assert(condition: boolean, message?: string): asserts condition {
    if (!condition) {
        throw new Error(message || "Assertion failed");
    }
}

// Minimal stub for "Point" from JUCE. 
// (In C++, it's juce::Point<float>. We'll just store x,y in TS.)
export interface Point {
    x: number;
    y: number;
}

// Minimal stub for "Path" from JUCE. 
// (In real code, replace with an actual path-drawing representation.)
export type Path = any;  // Placeholder

// Inlined TuningConstants from "TuningConstants.h"
const TuningConstants = {
    minPeriod: 1.0,       // MUST NEVER CHANGE
    defaultPeriod: 2.0,   // MUST NEVER CHANGE
    maxPeriod: 20.0,      // Can be changed to your liking
    defaultFrequencyA69: 440.0,
    defaultNoteNumberA69: 69,
    middleCFrequency: 261.6255653006,
    middleCNoteNumber: 60
};

// Emulated float-to-string function to mimic "WilsonicAppSkin::floatDescription" usage.
// This tries to preserve certain trailing-zero removal.
function floatDescription(value: number, precision: number): string {
    // toFixed returns a string with the specified precision, but not necessarily
    // removing trailing zeros. We'll manually strip them.
    let s = value.toFixed(precision);

    // Remove trailing zeros
    s = s.replace(/(\.\d*?[1-9])0+$/, "$1"); // trailing zeros
    // Remove trailing dot if it becomes something like "3."
    s = s.replace(/\.$/, "");

    return s;
}

// Minimal math helper to emulate parts of "WilsonicMath" usage
namespace WilsonicMath {
    // We replicate the concept of an epsilon for float equality checks
    export enum Epsilon {
        UI,
        CALC
    }

    export function getEpsilon(type: Epsilon): number {
        switch (type) {
            case Epsilon.UI: return 1e-4;
            case Epsilon.CALC: return Number.EPSILON;
            default: return Number.EPSILON;
        }
    }

    export function floatsAreNotEqual(a: number, b: number, epsilonType = Epsilon.CALC): boolean {
        const epsilon = getEpsilon(epsilonType);
        return Math.abs(a - b) > epsilon;
    }

    export function floatsAreEqual(a: number, b: number, epsilonType = Epsilon.CALC): boolean {
        const epsilon = getEpsilon(epsilonType);
        return Math.abs(a - b) <= epsilon;
    }
}

// Minimal "Fraction" class to replicate "Fraction.h"/"Fraction.cpp" behavior used by Microtone.
class Fraction {
    private _num: number;
    private _den: number;

    constructor(numerator?: number, denominator?: number, shouldReduce = true) {
        // default constructor
        if (numerator === undefined) {
            this._num = 0;
            this._den = 1;
            return;
        }
        this._num = numerator;
        this._den = (denominator === undefined || denominator === 0) ? 1 : denominator;
        // possible reduce
        if (shouldReduce) {
            this.reduce();
        }
    }

    public numerator(): number {
        return this._num;
    }

    public denominator(): number {
        return this._den;
    }

    public floatValue(): number {
        return this._num / this._den;
    }

    private reduce(): void {
        if (this._den === 0) {
            // In C++ code, we had an assertion. We'll just do an assertion here.
            assert(false, "Fraction denominator is 0");
        }
        const g = Fraction.greatestCommonFactor(Math.abs(this._num), Math.abs(this._den));
        if (g !== 0) {
            this._num = this._num / g;
            this._den = this._den / g;
        }
        // handle negative denominator
        if (this._den < 0) {
            this._den = -this._den;
            this._num = -this._num;
        }
    }

    // Equivalent to the static method in C++ "greatestCommonFactor"
    static greatestCommonFactor(m: number, n: number): number {
        if (m === 0 || n === 0) {
            return m || n; // handle gcd(0,x)
        }
        while (n !== 0) {
            const temp = n;
            n = m % n;
            m = temp;
        }
        return m;
    }

    // Operators as static methods

    static add(a: Fraction, b: Fraction): Fraction {
        if (a._den === b._den) {
            return new Fraction(a._num + b._num, a._den);
        } else {
            return new Fraction(a._num * b._den + b._num * a._den, a._den * b._den);
        }
    }

    static sub(a: Fraction, b: Fraction): Fraction {
        if (a._den === b._den) {
            // Original code asserts (a._num >= b._num) but let's skip that
            return new Fraction(a._num - b._num, a._den);
        } else {
            return new Fraction(a._num * b._den - b._num * a._den, a._den * b._den);
        }
    }

    static mul(a: Fraction, b: Fraction): Fraction {
        return new Fraction(a._num * b._num, a._den * b._den);
    }

    static div(a: Fraction, b: Fraction): Fraction {
        return new Fraction(a._num * b._den, a._den * b._num);
    }
}

// Type alias to match the style from C++
// In C++: using Microtone_p = shared_ptr<Microtone>;
// In TS, we just store references, so:
export type Microtone_p = Microtone;

/**
 * Space enum to mimic Microtone::Space in C++.
 */
export enum Space {
    Undefined = 0,
    LogPeriod,
    Linear
}

/**
 * Transpiled Microtone class from Microtone.h and Microtone.cpp.
 */
export class Microtone {
    private _shortDescriptionText: string = "";
    private _shortDescriptionText2: string = "";
    private _shortDescriptionText3: string = "";

    private _space: Space = Space.Linear;
    private _isRational: boolean = false;
    private _doFilter: boolean = false; // for "MTS Filter Note"
    // When rational, we store it in _microtoneRational; else we store in _microtoneNumber
    private _microtoneRational: Fraction = new Fraction(1, 1);
    private _microtoneNumber: number = 1.0;
    private _period: number = TuningConstants.defaultPeriod;
    private _midiNoteNumber: number = 60;
    private _midiRegister: number = 0;

    private _gralErvPoint: Point = { x: 0, y: 0 };
    private _gralErvPointFinal: Point = { x: 0, y: 0 };
    private _gralErvOctaveVector: Point = { x: 1, y: 1 };

    private _gralHexPoint: Point = { x: 0, y: 0 };
    private _gralHexPointFinal: Point = { x: 0, y: 0 };
    private _gralHexOctaveVector: Point = { x: 0, y: 0 };

    private _touchPointPath: Path = null;  // in C++, it's a juce::Path
    private _shouldRender: boolean = true;

    // Constructors
    constructor();
    constructor(num: number, den: number);
    constructor(num: number, den: number, shortDescriptionText: string, space: Space);
    constructor(num: number, den: number, shortDescriptionText: string, space: Space, period: number, should_reduce?: boolean);
    constructor(f: number);
    constructor(f: number, shortDescriptionText: string);
    constructor(f: number, shortDescriptionText: string, space: Space);
    constructor(f: number, shortDescriptionText: string, space: Space, period: number);
    constructor(...args: any[]) {
        // Overload resolution logic
        if (args.length === 0) {
            // Microtone()
            this.initRational(1, 1, "", Space.Linear, TuningConstants.defaultPeriod, true);
        } else if (args.length === 2 && typeof args[0] === "number" && typeof args[1] === "number") {
            // Microtone(unsigned long num, unsigned long den)
            const [num, den] = args;
            this.initRational(num, den, "", Space.Linear, TuningConstants.defaultPeriod, true);
        } else if (
            args.length === 4 ||
            args.length === 5 ||
            (args.length === 6 && typeof args[0] === "number" && typeof args[1] === "number")
        ) {
            // Possibly: Microtone(num, den, shortDescriptionText, space) 
            // or Microtone(num, den, shortDescriptionText, space, period, should_reduce)
            const [num, den, shortDescription, space, period, should_reduce] = args;
            this.initRational(
                num,
                den,
                shortDescription ?? "",
                space ?? Space.Linear,
                period !== undefined ? period : TuningConstants.defaultPeriod,
                should_reduce !== undefined ? should_reduce : true
            );
        } else if (args.length === 1 && typeof args[0] === "number") {
            // Microtone(float f)
            const f = args[0];
            this.initFloat(f, "", Space.Linear, TuningConstants.defaultPeriod);
        } else if (args.length === 2 && typeof args[0] === "number" && typeof args[1] === "string") {
            // Microtone(float f, string shortDesc)
            const [f, desc] = args;
            this.initFloat(f, desc, Space.Linear, TuningConstants.defaultPeriod);
        } else if (args.length === 3 && typeof args[0] === "number" && typeof args[1] === "string" && typeof args[2] === "number") {
            // Microtone(float f, string shortDesc, Space space)
            const [f, desc, space] = args;
            this.initFloat(f, desc, space, TuningConstants.defaultPeriod);
        } else if (args.length === 4 && typeof args[0] === "number" && typeof args[1] === "string" && typeof args[2] === "number" && typeof args[3] === "number") {
            // Microtone(float f, string shortDesc, Space space, float period)
            const [f, desc, space, period] = args;
            this.initFloat(f, desc, space, period);
        }
    }

    private initRational(num: number, den: number, shortDescriptionText: string, space: Space, period: number, should_reduce: boolean) {
        this._isRational = true;
        this._space = space;
        this._period = period;
        this._microtoneRational = new Fraction(num, den, should_reduce);

        if (!shortDescriptionText || shortDescriptionText.length === 0) {
            if (den === 1) {
                this._shortDescriptionText = `${num}`;
            } else {
                this._shortDescriptionText = `${num}/${den}`;
            }
        } else {
            this._shortDescriptionText = shortDescriptionText;
        }
    }

    private initFloat(f: number, shortDescription: string, space: Space, period: number) {
        assert(!Number.isNaN(f), "f is NaN");
        // For "space == LogPeriod", we allow f >= 0; for "space == Linear", we want f>0. 
        // We'll skip some strict checks for brevity, or do:
        if (space === Space.Linear) {
            assert(f > 0, "Float constructor: f <= 0 for linear space");
        }
        assert(period >= TuningConstants.minPeriod && period <= TuningConstants.maxPeriod, "Period out of valid range");

        this._isRational = false;
        this._space = space;
        this._microtoneNumber = f;
        this._period = period;

        if (!shortDescription || shortDescription.length === 0) {
            this._shortDescriptionText = `${f}`;
        } else {
            this._shortDescriptionText = shortDescription;
        }
    }

    // Clone
    public clone(): Microtone {
        const m = new Microtone();
        m._space = this._space;
        m._isRational = this._isRational;
        m._microtoneRational = new Fraction(this._microtoneRational.numerator(), this._microtoneRational.denominator(), true);
        m._microtoneNumber = this._microtoneNumber;
        m._period = this._period;
        m._gralErvPoint = { x: this._gralErvPoint.x, y: this._gralErvPoint.y };
        m._gralErvPointFinal = { x: this._gralErvPointFinal.x, y: this._gralErvPointFinal.y };
        m._gralErvOctaveVector = { x: this._gralErvOctaveVector.x, y: this._gralErvOctaveVector.y };
        m._gralHexPoint = { x: this._gralHexPoint.x, y: this._gralHexPoint.y };
        m._gralHexPointFinal = { x: this._gralHexPointFinal.x, y: this._gralHexPointFinal.y };
        m._gralHexOctaveVector = { x: this._gralHexOctaveVector.x, y: this._gralHexOctaveVector.y };
        m._touchPointPath = this._touchPointPath;
        m._midiNoteNumber = this._midiNoteNumber;
        m._midiRegister = this._midiRegister;
        m._shortDescriptionText = this._shortDescriptionText;
        m._shortDescriptionText2 = this._shortDescriptionText2;
        m._shortDescriptionText3 = this._shortDescriptionText3;
        m._doFilter = this._doFilter;
        m._shouldRender = this._shouldRender;
        return m;
    }

    // Getters / Setters
    public getSpace(): Space {
        return this._space;
    }

    public isRational(): boolean {
        return this._isRational;
    }

    public getShortDescriptionText(): string {
        return this._shortDescriptionText;
    }

    public setShortDescriptionText(desc: string): void {
        this._shortDescriptionText = desc;
    }

    public getShortDescriptionText2(): string {
        return this._shortDescriptionText2;
    }

    public setShortDescriptionText2(desc: string): void {
        this._shortDescriptionText2 = desc;
    }

    public getShortDescriptionText3(): string {
        return this._shortDescriptionText3;
    }

    public setShortDescriptionText3(desc: string): void {
        this._shortDescriptionText3 = desc;
    }

    public getDebugDescription(): string {
        return `${this._shortDescriptionText}${this._shortDescriptionText2}${this._shortDescriptionText3}(${this.getFrequencyValueDescription()})`;
    }

    public getNumerator(): number {
        if (this._isRational) {
            return this._microtoneRational.numerator();
        } else {
            return Math.floor(this._microtoneNumber); // In original code, we cast float->ulong
        }
    }

    public getDenominator(): number {
        if (this._isRational) {
            return this._microtoneRational.denominator();
        } else {
            return 1;
        }
    }

    // getPitchValue01 => returns float from 0..1
    public getPitchValue01(): number {
        const f = this._isRational
            ? this._microtoneRational.floatValue()
            : this._microtoneNumber;

        switch (this._space) {
            case Space.Linear: {
                assert(f > 0, "PitchValue in linear space must be > 0");
                assert(this._period >= TuningConstants.minPeriod);

                if (WilsonicMath.floatsAreEqual(this._period, TuningConstants.minPeriod)) {
                    // minPeriod == 1 => log2( f ), but if period=1, log2(f) doesn't make sense for f=1?
                    // The original code does: return log2f(f). We'll mimic that.
                    return Math.log2(f);
                } else {
                    let retVal = Math.log(f) / Math.log(this._period);

                    // separate integer part from fraction
                    const intPart = Math.trunc(retVal);
                    retVal = retVal - intPart;

                    if (retVal < 0) {
                        retVal = 1 + retVal;
                    }
                    // fmod 1
                    retVal = retVal % 1;

                    assert(!Number.isNaN(retVal), "NaN pitchValue");
                    assert(Number.isFinite(retVal), "Infinite pitchValue");
                    return retVal;
                }
            }
            case Space.LogPeriod: {
                // just return f
                return f;
            }
            default:
                assert(false, "Space undefined");
                return 0;
        }
    }

    public setPitchValue01(p: number): void {
        // microtone must not be rational
        assert(!this._isRational, "Cannot call setPitchValue01 on a rational Microtone");
        if (p < 0 || p > 1) {
            assert(false, "pitch out of range 0..1");
        }

        switch (this._space) {
            case Space.Linear:
                this._microtoneNumber = Math.pow(this._period, p);
                break;
            case Space.LogPeriod:
                this._microtoneNumber = p;
                break;
            default:
                assert(false, "Space undefined in setPitchValue01");
        }
    }

    public getFrequencyValue(): number {
        const f = this._isRational
            ? this._microtoneRational.floatValue()
            : this._microtoneNumber;

        switch (this._space) {
            case Space.Linear:
                return f;
            case Space.LogPeriod:
                return Math.pow(this._period, f);
            default:
                assert(false, "Undefined space in getFrequencyValue");
                return 0;
        }
    }

    public setFrequencyValue(f: number): void {
        assert(!this._isRational, "Cannot call setFrequencyValue on a rational Microtone");
        assert(f > 0, "Frequency must be > 0");

        switch (this._space) {
            case Space.Linear:
                this._microtoneNumber = f;
                break;
            case Space.LogPeriod:
                // logBase(b, x) = log(x)/log(b)
                this._microtoneNumber = Math.log2(f) / Math.log2(this._period);
                break;
            default:
                assert(false, "Undefined space in setFrequencyValue");
        }
    }

    public getFrequencyValueDescription(): string {
        const f = this.getFrequencyValue();
        return Microtone.getFrequencyValueDescription(f);
    }

    public getPitchValueDescription(): string {
        const p = this.getPitchValue01();
        // In original code: floatDescription(p, 6)
        return floatDescription(p, 6);
    }

    public getCentsValueDescription(): string {
        // 1200 cents per "octave" from 0..1 in pitchValue
        const p = 1200.0 * this.getPitchValue01();
        return floatDescription(p, 2);
    }

    public static getFrequencyValueDescription(f: number): string {
        return floatDescription(f, 3);
    }

    public getGralErvPoint(): Point {
        return this._gralErvPoint;
    }

    public setGralErvPoint(p: Point): void {
        this._gralErvPoint = p;
    }

    public getGralErvPointFinal(): Point {
        return this._gralErvPointFinal;
    }

    public setGralErvPointFinal(p: Point): void {
        this._gralErvPointFinal = p;
    }

    public getGralErvOctaveVector(): Point {
        return this._gralErvOctaveVector;
    }

    public setGralErvOctaveVector(p: Point): void {
        this._gralErvOctaveVector = p;
    }

    public getGralHexPoint(): Point {
        return this._gralHexPoint;
    }

    public setGralHexPoint(p: Point): void {
        this._gralHexPoint = p;
    }

    public getGralHexPointFinal(): Point {
        return this._gralHexPointFinal;
    }

    public setGralHexPointFinal(p: Point): void {
        this._gralHexPointFinal = p;
    }

    public getHexOctaveVector(): Point {
        return this._gralHexOctaveVector;
    }

    public setHexOctaveVector(p: Point): void {
        this._gralHexOctaveVector = p;
    }

    public getTouchPointPath(): Path {
        return this._touchPointPath;
    }

    public setTouchPointPath(t: Path): void {
        this._touchPointPath = t;
    }

    public setFilterNote(doFilter: boolean): void {
        this._doFilter = doFilter;
    }

    public getFilterNote(): boolean {
        return this._doFilter;
    }

    public setShouldRender(shouldRender: boolean): void {
        this._shouldRender = shouldRender;
    }

    public getShouldRender(): boolean {
        return this._shouldRender;
    }

    public updateShortDescriptionText(): void {
        if (this._isRational) {
            const n = this.getNumerator();
            const d = this.getDenominator();
            if (d === 1) {
                this._shortDescriptionText = `${n}`;
            } else {
                this._shortDescriptionText = `${n}/${d}`;
            }
        } else {
            this._shortDescriptionText = Microtone.getFrequencyValueDescription(this.getFrequencyValue());
        }
    }

    public octaveReduce(): void {
        this.octaveReduceWithPeriod(this._period);
    }

    public octaveReduceWithPeriod(period: number): void {
        // replace current period if different
        if (WilsonicMath.floatsAreNotEqual(period, this._period)) {
            assert(period >= TuningConstants.minPeriod && period <= TuningConstants.maxPeriod, "Invalid period");
            this._period = period;
        }

        // If rational but period is non-integer, convert to float
        if (this._isRational) {
            const r = period % 1.0;
            if (r !== 0.0) {
                // convert
                this._microtoneNumber = this._microtoneRational.floatValue();
                this._isRational = false;
            }
        }

        if (this._isRational) {
            // if period = minPeriod => set fraction to that
            if (WilsonicMath.floatsAreEqual(this._period, TuningConstants.minPeriod)) {
                this._microtoneRational = new Fraction(Math.floor(this._period), 1);
                return;
            }

            const val = this._microtoneRational.floatValue();
            assert(!Number.isNaN(val), "NaN rational val");
            assert(Number.isFinite(val), "Inf rational val");

            // period is integer so we can treat it as fraction
            // This code in C++ is somewhat complex. We'll replicate the logic:
            const periodFrac = new Fraction(Math.floor(this._period), 1);

            if (this._space === Space.Linear) {
                assert(val > 0, "Rational must be > 0 for linear space");
                // repeatedly divide or multiply by period to get in [1, period)
                while (this._microtoneRational.floatValue() >= this._period) {
                    this._microtoneRational = Fraction.div(this._microtoneRational, periodFrac);
                }
                while (this._microtoneRational.floatValue() < 1.0) {
                    this._microtoneRational = Fraction.mul(this._microtoneRational, periodFrac);
                }
                // must be in [1, period)
            } else if (this._space === Space.LogPeriod) {
                let m = val;
                while (m < 1.0) {
                    m += 1.0;
                }
                while (m >= 1.0) {
                    m -= 1.0;
                }
                // we don't actually store m in the fraction though. 
                // The C++ logic for rational + LogPeriod is a bit contradictory.
                // We'll just store it in _microtoneNumber and mark non-rational:
                this._microtoneRational = new Fraction(1, 1);
                this._microtoneNumber = m;
                this._isRational = false;
            } else {
                assert(false, "Undefined space in rational octaveReduce");
            }
        } else {
            // float
            if (WilsonicMath.floatsAreEqual(this._period, TuningConstants.minPeriod)) {
                this._microtoneNumber = this._period;
                return;
            }
            assert(!Number.isNaN(this._microtoneNumber) && Number.isFinite(this._microtoneNumber), "Invalid microtoneNumber");

            if (this._space === Space.Linear) {
                while (this._microtoneNumber < 1.0) {
                    this._microtoneNumber *= this._period;
                }
                while (this._microtoneNumber >= this._period) {
                    this._microtoneNumber /= this._period;
                }
            } else if (this._space === Space.LogPeriod) {
                while (this._microtoneNumber < 0.0) {
                    this._microtoneNumber += 1.0;
                }
                this._microtoneNumber = this._microtoneNumber % 1.0;
            } else {
                assert(false, "Undefined space in float octaveReduce");
            }
        }
    }

    // checks if freqValue is power-of-2
    public frequencyValueIsPowerOf2(): boolean {
        assert(this._space === Space.Linear || this._space === Space.LogPeriod, "Space must be linear or logPeriod");
        let p = this.getFrequencyValue();
        assert(p > 0, "Frequency must be > 0");
        assert(!Number.isNaN(p) && Number.isFinite(p), "Invalid freq");
        p = Math.log2(p);
        p = p % 1.0;
        return p === 0.0 || p === 1.0;
    }

    public setMidiNoteNumber(nn: number): void {
        this._midiNoteNumber = nn;
    }

    public getMidiNoteNumber(): number {
        return this._midiNoteNumber;
    }

    public setMidiRegister(registerNumber: number): void {
        this._midiRegister = registerNumber;
    }

    public getMidiRegister(): number {
        return this._midiRegister;
    }

    // Operator-like methods
    // multiply
    public multiply(multipland: Microtone): Microtone {
        if (this._isRational && multipland._isRational) {
            const result = Fraction.mul(
                this._microtoneRational,
                new Fraction(multipland.getNumerator(), multipland.getDenominator(), true)
            );
            return new Microtone(result.numerator(), result.denominator(), "", this._space, this._period, true);
        } else {
            const result = this.getFrequencyValue() * multipland.getFrequencyValue();
            return new Microtone(result);
        }
    }

    // divide
    public divide(divisor: Microtone): Microtone {
        if (this._isRational && divisor._isRational) {
            const result = Fraction.div(
                this._microtoneRational,
                new Fraction(divisor.getNumerator(), divisor.getDenominator(), true)
            );
            return new Microtone(result.numerator(), result.denominator(), "", this._space, this._period, true);
        } else {
            const result = this.getFrequencyValue() / divisor.getFrequencyValue();
            return new Microtone(result);
        }
    }

    // add
    public add(rightHand: Microtone): Microtone {
        if (this._isRational && rightHand._isRational) {
            const result = Fraction.add(
                this._microtoneRational,
                new Fraction(rightHand.getNumerator(), rightHand.getDenominator(), true)
            );
            return new Microtone(result.numerator(), result.denominator(), "", this._space, this._period, true);
        } else {
            const result = this.getFrequencyValue() + rightHand.getFrequencyValue();
            return new Microtone(result);
        }
    }

    // subtract
    public subtract(term: Microtone): Microtone {
        if (this._isRational && term._isRational) {
            const result = Fraction.sub(
                this._microtoneRational,
                new Fraction(term.getNumerator(), term.getDenominator(), true)
            );
            return new Microtone(result.numerator(), result.denominator(), "", this._space, this._period, true);
        } else {
            const result = this.getFrequencyValue() - term.getFrequencyValue();
            return new Microtone(result);
        }
    }

    // freshmanSum
    public static freshmanSum(left: Microtone, right: Microtone): Microtone {
        assert(left.isRational() && right.isRational(), "freshmanSum requires rational Microtones");
        const numerator = left.getNumerator() + right.getNumerator();
        const denominator = left.getDenominator() + right.getDenominator();
        return new Microtone(numerator, denominator);
    }
}
