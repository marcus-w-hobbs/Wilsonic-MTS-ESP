from fractions import Fraction as F
from math import gcd
# 1. Farey order N on [1,2]: consecutive terms are superparticular (epimoric) and bc-ad=1
def farey(N):
    s=sorted({F(n,d) for d in range(1,N+1) for n in range(d,2*d+1)})
    return s
for N in (3,4,5,6):
    s=farey(N); ok=all((b.numerator*a.denominator - a.numerator*b.denominator)==1 and (b/a).numerator-(b/a).denominator==1 for a,b in zip(s,s[1:]))
    print("F%d on [1,2]:"%N, [str(x) for x in s], "all steps epimoric & det=1:", ok)
# 2. mediant = denominator-weighted arithmetic mean = numerator-weighted harmonic mean
a,c=F(5,4),F(4,3); m=F(a.numerator+c.numerator,a.denominator+c.denominator)
am=(a.denominator*a+c.denominator*c)/(a.denominator+c.denominator)
hm=(a.numerator+c.numerator)/(a.numerator/a+c.numerator/c)
print("mediant",m,"den-weighted AM",am,"num-weighted HM",hm)
# 3. Archytas enharmonic as mediant cascade from 1/1,4/3
seq=[F(1),F(4,3)]; print("epimore",seq[1]/seq[0])
seq.insert(1,F(5,4)); print([str(x) for x in seq],[str(seq[i+1]/seq[i]) for i in range(2)])
seq.insert(2,F(9,7)); print([str(x) for x in seq],[str(seq[i+1]/seq[i]) for i in range(3)])
# 4. lambdoma row/column: mediant along row = AM (proportional), along column = HM (subcontrary)
print("row 4/4,5/4,6/4 AM:",(F(4,4)+F(6,4))/2, " column 6/4,6/5,6/6 HM:", 2*F(6,4)*F(6,6)/(F(6,4)+F(6,6)))
# 5. 5-limit superparticulars (Stormer): finite list
sp=[]
for n in range(1,100000):
    x=n+1; y=n
    def smooth(k):
        for p in (2,3,5):
            while k%p==0: k//=p
        return k==1
    if smooth(n) and smooth(n+1): sp.append(f"{n+1}/{n}")
print("5-limit superparticulars:",sp)
# 6. difference tone of p:q dyad vs periodicity pitch
for p,q in ((3,2),(5,4),(5,3),(7,4),(9,8),(10,9)):
    print(f"{p}/{q}: difference tone = {p-q} x fundamental; equals periodicity pitch: {p-q==1}")
# 7. epimore between sqrt2 convergents 17/12 and 24/17
print("24/17 / 17/12 =", F(24,17)/F(17,12))
