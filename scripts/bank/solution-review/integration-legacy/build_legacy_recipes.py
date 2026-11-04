import os
"""Create compact, parameterized explanatory recipes for all legacy families."""
from pathlib import Path
import sys,json
import sympy as s
ROOT=Path(os.environ.get('BANK_AUDIT_REPO',Path(__file__).resolve().parents[4]))
OUT=Path(__file__).parent
sys.path.insert(0,str(ROOT/'scripts/bank'))
from families import FAMILIES,x,y,n
from pipeline import display,operate

def L(z):return s.latex(z).replace(r'\log',r'\ln').replace(r'\operatorname{atan}',r'\arctan')
def T(z):return r'\text{'+z+'}'
def D(z,order=1):return r'\frac{d'+('^{'+str(order)+'}' if order>1 else '')+r'}{dx'+('^{'+str(order)+'}' if order>1 else '')+'}'+r'\left('+L(z)+r'\right)'
R=s.Rational
P={
'polynomial-area':[T('Integrate each monomial on the displayed interval using its power antiderivative.')],
'exponential-area':[r'\frac{d}{dx}\frac{e^{kx}}k=e^{kx}\quad(k=1,2,3)',T('Evaluate each antiderivative at one and zero.')],
'trig-area':[r'(-\cos x)^{\prime}=\sin x,\quad(\sin x)^{\prime}=\cos x,\quad(-\tfrac12\cos(2x))^{\prime}=\sin(2x)',T('Evaluate these primitives at the displayed endpoints.')],
'polynomial-exponential':[r'F_0(x)=e^x,\quad F_j(x)=x^je^x-jF_{j-1}(x)\quad(j=1,2,3)',r'F_j^{\prime}(x)=x^je^x',T('Repeated integration by parts gives the following definite contributions.')],
'quadratic-substitution':[r't=1+x^2,\quad dt=2x\,dx,\quad x:0\to1\ \Longrightarrow\ t:1\to2',r'\int_1^2\frac{dt}{t}=\ln2,\quad\int_1^2\frac{2\,dt}{t^2}=1,\quad\int_1^2\frac{3\,dt}{t^3}=\frac98'],
'rational-decomposition':[T('Split each rational function into its two simple fractions before integrating.')],
'log-moments':[r'F_j(x)=x^{j+1}\left(\frac{\ln x}{j+1}-\frac1{(j+1)^2}\right)\quad(j=0,1,2)',r'F_j^{\prime}(x)=x^j\ln x,\quad\lim_{x\downarrow0}F_j(x)=0',r'\int_0^1x^j\ln x\,dx=F_j(1)-\lim_{x\downarrow0}F_j(x)=-\frac1{(j+1)^2}'],
 'trig-products':[r'J_j:=\int_0^{\pi/2}\sin^{2j}x\,dx,\quad J_0=\frac\pi2',T('Integration by parts gives ')+r'J_j=\frac{2j-1}{2j}J_{j-1}\quad(j\ge1)',r'\int_0^{\pi/2}\sin^{2j}x\cos^2x\,dx=J_j-J_{j+1}\quad(j=1,2,3)'],
'improper-rational':[r't=\frac{x}{1+x},\quad dx=\frac{dt}{(1-t)^2},\quad x:0\to\infty\ \Longrightarrow\ t:0\to1',r'\frac{x^j}{(1+x)^{j+2}}dx=t^jdt\quad(j=0,1,2)',r'\int_0^1t^jdt=\frac1{j+1}'],
'polynomial-slope':[T('Differentiate each monomial, then substitute the displayed point.')],
'trig-slope':[T('Differentiate the trigonometric terms, retaining the inner frequency factor.')],
'exp-log-slope':[T('Differentiate each term on its positive real domain, then evaluate at one.')],
'product-rule':[T('Apply the product rule to each product before evaluation.')],
'quotient-rule':[T('Differentiate numerator and denominator with the quotient rule; all displayed denominators are nonzero at the evaluation point.')],
'nested-chain':[T('Differentiate the outer function and multiply by the derivative of the inner square.')],
'fourth-derivative':[T('Differentiate each product four times before substituting zero; this retains all product-rule terms.')],
'log-differentiation':[r'\frac d{dx}v(x)^{w(x)}=v(x)^{w(x)}\left(w^{\prime}(x)\ln v(x)+w(x)\frac{v^{\prime}(x)}{v(x)}\right)\quad(v(x)>0)',r'(v,w)=(x,x),\ (x,x^2),\ (1+x,x)',T('All three bases are positive near the evaluation point.')],
'parametric-curvature':[T('Apply the product and chain rules three times, then substitute the displayed point.')],
'polynomial-continuity':[T('All components are polynomials and continuous at one, so direct substitution is valid.')],
'removable-factor':[r'\frac{x^j-1}{x-1}=\sum_{r=0}^{j-1}x^r\quad(x\ne1,\ j=2,3,4)',T('The polynomial expressions extend continuously to one.')],
'standard-trig-limits':[r'\frac{\sin(jx)}x=j\frac{\sin(jx)}{jx}\longrightarrow j\quad(j=1,2,3)',T('The factor with argument and denominator equal tends to one.')],
'exponential-cancellation':[r'e^{jx}=1+jx+O(x^2)\quad(x\to0,\ j=1,2,3)',r'\frac{e^{jx}-1}{x}=j+O(x)\longrightarrow j'],
'rational-at-infinity':[T('Divide each numerator and denominator by its highest power of the variable.'),r'\frac{x^2+1}{2x^2+3}=\frac{1+x^{-2}}{2+3x^{-2}}',r'\frac{x^3-1}{3x^3+x}=\frac{1-x^{-3}}{3+x^{-2}},\quad\frac{x^4+x}{4x^4+1}=\frac{1+x^{-3}}{4+x^{-4}}'],
'logarithmic-cancellation':[r'\ln(1+jx)=jx+O(x^2)\quad(x\to0,\ j=1,2,3)',r'\frac{\ln(1+jx)}x=j+O(x)\longrightarrow j',T('The logarithms are real in a neighborhood of zero.')],
 'third-order-exponential':[r'e^{jx}=1+jx+\frac{j^2x^2}2+\frac{j^3x^3}6+O(x^4)\quad(j=1,2,3)',r'\frac{e^{jx}-1-jx-j^2x^2/2}{x^3}=\frac{j^3}6+O(x)'],
 'trig-cancellation':[r'\sin x=x-\frac{x^3}6+O(x^5),\quad\cos x=1-\frac{x^2}2+O(x^4),\quad\tan x=x+\frac{x^3}3+O(x^5)',r'x-\sin x=\frac{x^3}6+O(x^5),\quad\tan x-x=\frac{x^3}3+O(x^5)',r'\sin x-x\cos x=\frac{x^3}3+O(x^5)'],
'radical-cancellation':[r'(1+x)^r=1+rx+\frac{r(r-1)}2x^2+O(x^3)\quad\left(r=\frac12,\frac13,\frac14\right)',T('Subtract the displayed constant and linear terms, then divide by the square of the variable.')],
'geometric-series':[r'\sum_{n=0}^Nr^n=\frac{1-r^{N+1}}{1-r}\longrightarrow\frac1{1-r}\quad(|r|<1)',r'r=\frac12,\ \frac13,\ \frac14'],
'even-geometric-series':[r'(1/j)^{2n}=(1/j^2)^n\quad(j=2,3,4)',r'\sum_{n=0}^\infty r^n=\frac1{1-r}\quad(|r|<1),\qquad r=\frac14,\ \frac19,\ \frac1{16}'],
 'telescoping-series':[r'\frac1{(n+j)(n+j+1)}=\frac1{n+j}-\frac1{n+j+1}\quad(j=1,2,3)',r'\sum_{n=0}^N\frac1{(n+j)(n+j+1)}=\frac1j-\frac1{N+j+1}\longrightarrow\frac1j'],
 'weighted-geometric':[r'G(r):=\sum_{n=0}^\infty r^n=\frac1{1-r}\quad(|r|<1)',T('Differentiate inside the convergence disk and multiply by the ratio.'),r'\sum_{n=0}^\infty nr^n=rG^{\prime}(r)=\frac r{(1-r)^2}',r'r=\frac12,\ \frac13,\ \frac14'],
 'quadratic-geometric':[r'G(r):=\sum_{n=0}^\infty r^n=\frac1{1-r}\quad(|r|<1)',r'\sum_{n=0}^\infty n^2r^n=r\frac d{dr}\left(rG^{\prime}(r)\right)=\frac{r(1+r)}{(1-r)^3}',r'r=\frac12,\ \frac13,\ \frac14',T('Both differentiations are valid inside the convergence disk.')],
 'exponential-series':[r'e^t=\sum_{n=0}^\infty\frac{t^n}{n!}\quad(t\in\mathbb R)',r't=1,\ 2,\ 3',T('The exponential power series converges absolutely at all three values.')],
 'alternating-log-series':[r'\ln(1+t)=\sum_{n=1}^\infty\frac{(-1)^{n+1}t^n}{n}\quad(-1<t\le1)',r't=1,\ \frac12,\ \frac13',T('The endpoint converges by the alternating-series test; the other two series converge absolutely.')],
 'cubic-telescoping':[r'\frac1{(n+j)(n+j+1)(n+j+2)}=\frac12\left(\frac1{(n+j)(n+j+1)}-\frac1{(n+j+1)(n+j+2)}\right)',r'j=1,2,3',T('Sum the finite differences before taking the limit.'),r'\sum_{n=0}^\infty\frac1{(n+j)(n+j+1)(n+j+2)}=\frac1{2j(j+1)}'],
 'zeta-even':[r'\zeta(s):=\sum_{n=1}^\infty n^{-s}\quad(s>1)',r'\zeta(2)=\frac{\pi^2}{6},\quad\zeta(4)=\frac{\pi^4}{90},\quad\zeta(6)=\frac{\pi^6}{945}',T('Apply these classical even-zeta evaluations to the three powers; all component series converge absolutely.')],
 'partial-x':[T('Hold the second variable fixed while differentiating in the first.')],
 'partial-y':[T('Hold the first variable fixed while differentiating in the second.')],
 'mixed-partials':[T('Differentiate once in each variable before substituting the point.')],
 'high-mixed-partials':[T('Differentiate twice in each variable before substituting the origin.')],
 'laplacian':[r'\Delta h:=\frac{\partial^2h}{\partial x^2}+\frac{\partial^2h}{\partial y^2}',T('Add the pure second derivatives; mixed derivatives are not part of this operator.')],
 'laplacian-products':[r'\Delta h:=\frac{\partial^2h}{\partial x^2}+\frac{\partial^2h}{\partial y^2}',T('Differentiate the composite terms before substituting the point.')],
 'rectangle-area':[T('Integrate first in the second variable and use its displayed bounds, then integrate in the first.')],
 'triangle-integral':[T('The inner upper bound depends on the first variable; substitute it before the outer integration.')],
 'curved-domain-integral':[T('The curved inner upper bound must be substituted before the outer integration.')],
 'transformed-beta-log':[r't=\frac{x}{1+x},\quad dx=\frac{dt}{(1-t)^2},\quad x:0\to\infty\ \Longrightarrow\ t:0\to1',r'\frac{x^{p-1}}{(1+x)^{p+q}}\left(-\ln\frac{x}{1+x}\right)^m dx=t^{p-1}(1-t)^{q-1}(-\ln t)^m dt',r'(p,q,m)=(2,3,2),\ (3,4,3),\ (4,3,4)',r'\int_0^1t^{p-1}(1-t)^{q-1}(-\ln t)^m dt=m!\sum_{j=0}^{q-1}\frac{(-1)^j\binom{q-1}j}{(p+j)^{m+1}}',T('Expand the finite binomial; the log moments follow by differentiating the convergent power integral.')],
 'concealed-reflection':[r'h_{p,q}(x)=x^p(1+x)^q,\quad w_m(x)=[x(1-x)]^m',r'(p,q,m)=(2,2,1),\ (3,2,2),\ (2,3,3)',r'\frac{h_{p,q}(x)}{h_{p,q}(x)+h_{p,q}(1-x)}+\frac{h_{p,q}(1-x)}{h_{p,q}(x)+h_{p,q}(1-x)}=1',T('Reflect each integral around one half; its weight is unchanged.'),r'\int_0^1w_m(x)\frac{h_{p,q}(x)}{h_{p,q}(x)+h_{p,q}(1-x)}dx=\frac12\int_0^1w_m(x)dx=\frac{(m!)^2}{2(2m+1)!}'],
 'frullani-cancellation':[r'(p,q,m)=(1,2,2),\ (2,3,3),\ (3,4,4)',r'x^{p-1}(1-x^q)^m=\sum_{j=0}^m(-1)^j\binom mj x^{p+qj-1}',r'\sum_{j=0}^m(-1)^j\binom mj=0',r'\int_0^1\frac{x^{u-1}-x^{v-1}}{-\ln x}\,dx=\ln\frac vu\quad(u,v>0)',T('Group the powers into convergent differences before integrating; individual logarithmic terms need not converge.'),r'\int_0^1\frac{x^{p-1}(1-x^q)^m}{-\ln x}\,dx=-\sum_{j=0}^m(-1)^j\binom mj\ln(p+qj)'],
 'removable-exponential-derivative':[r'e^{mx}(e^x-1)^4=\sum_{j=0}^4(-1)^{4-j}\binom4j e^{(m+j)x}\quad(m=1,2,3)',T('The numerator has a fourth-order zero, so division yields an analytic extension.'),T('The sixth derivative of the quotient is six factorial times its sixth Taylor coefficient.'),r'\left.\frac{d^6}{dx^6}\frac{e^{mx}(e^x-1)^4}{x^4}\right|_{x=0}=\frac{6!}{10!}\sum_{j=0}^4(-1)^{4-j}\binom4j(m+j)^{10}'],
 'implicit-inverse-series':[r'\phi_{p,q}(z)=\frac{(1+z)^p}{(1-z)^q},\quad(p,q)=(2,2),(3,2),(2,3)',T('These are the three analytic branches defined in the question, in order.'),r'u=x\phi_{p,q}(u),\quad u(0)=0\quad\Longrightarrow\quad u^{(6)}(0)=5![z^5]\phi_{p,q}(z)^6',T('The bracket denotes the coefficient of the indicated power.'),r'u^{(6)}(0)=5!\sum_{j=0}^5\binom{6p}j\binom{6q+4-j}{5-j}',T('The implicit-function derivative is nonzero at the origin, so Lagrange inversion applies.')],
 'roots-of-unity-product':[r'\prod_{j=1}^{m-1}\left(1-2x\cos\frac{2\pi j}{m}+x^2\right)=(1+x+\cdots+x^{m-1})^2',r'(m,d)=(4,1),(5,2),(6,3)',T('These parameter pairs describe the three products and their exponential multipliers.'),r'[x^j](1+x+\cdots+x^{m-1})^2=\min(j+1,m,2m-1-j)\quad(0\le j\le2m-2)',T('The bracket denotes a polynomial coefficient.'),r'\left.\frac{d^6}{dx^6}\left(e^{dx}(1+x+\cdots+x^{m-1})^2\right)\right|_{x=0}=6!\sum_{j=0}^6\frac{\min(j+1,m,2m-1-j)d^{6-j}}{(6-j)!}'],
 'finite-difference-log-limit':[r'(b,c)=(6,2),(7,3),(8,4)',T('These are the power and logarithm exponents in the three components.'),r'\partial_b^c(1+jx)^b=(1+jx)^b\ln^c(1+jx)',r'\sum_{j=0}^5(-1)^{5-j}\binom5j j^r=0\quad(0\le r<5),\qquad\sum_{j=0}^5(-1)^{5-j}\binom5j j^5=5!',r'\lim_{x\to0}\frac{\sum_{j=0}^5(-1)^{5-j}\binom5j(1+jx)^b\ln^c(1+jx)}{x^5}=\frac{d^c}{db^c}\bigl[b(b-1)(b-2)(b-3)(b-4)\bigr]',T('Analyticity near zero justifies extracting the fifth Taylor coefficient and differentiating it in the exponent.')],
 'riemann-product-limit':[r'f_1(t)=\frac{t^2(1-t)^2}{1+t},\quad f_2(t)=\frac{t^3(1-t)^2}{2+t},\quad f_3(t)=\frac{t^2(1-t)^3}{3+t}',r'u_j=\frac{f_i(j/N)}{N^2}\quad(1\le j\le N,\ i=1,2,3)',r'0\le u_j\le N^{-2},\quad\sum_{j=1}^N u_j^2\le N^{-3}',r'\ln\prod_{j=1}^N(1+u_j)=\sum_{j=1}^Nu_j+O(N^{-3})',r'N\left(\prod_{j=1}^N(1+u_j)-1\right)\longrightarrow\int_0^1f_i(t)dt',r'J_m(c):=\int_0^1\frac{t^m}{t+c}\,dt,\quad J_0(c)=\ln\frac{c+1}{c}',r'J_m(c)=\frac1m-cJ_{m-1}(c)\quad(m\ge1)',T('Expand the finite powers in the three weights and use this recurrence at the displayed denominators.')],
 'second-order-riemann-limit':[r'f_1(t)=t^2(t+1)^2,\quad f_2(t)=t^3(t+2)^2,\quad f_3(t)=t^2(t+3)^3',r'\frac1N\sum_{j=1}^N f_i(j/N)=\int_0^1f_i(t)dt+\frac{f_i(1)-f_i(0)}{2N}+\frac{f_i^{\prime}(1)-f_i^{\prime}(0)}{12N^2}+O(N^{-4})',r'f_i(0)=f_i^{\prime}(0)=0\quad(i=1,2,3)',T('After the two subtractions and multiplication by the square of the sample size, only the derivative endpoint term survives.'),r'\frac{f_1^{\prime}(1)}{12}=1,\quad\frac{f_2^{\prime}(1)}{12}=\frac{11}4,\quad\frac{f_3^{\prime}(1)}{12}=\frac{44}3'],
 'stirling-beta-series':[r'(p,q,m)=(1,5,2),(2,6,3),(3,7,4)',T('These are respectively the first denominator shift, the number of subsequent shifts, and the numerator exponent.'),r'\frac1{(n+p)\cdots(n+p+q)}=\frac1{q!}\int_0^1t^{n+p-1}(1-t)^qdt',r'\sum_{n=0}^\infty n^m t^n=\sum_{j=0}^m S(m,j)j!\frac{t^j}{(1-t)^{j+1}}\quad(0<t<1)',r'S(0,0)=1,\quad S(m,0)=0\ (m>0),\quad S(m,j)=jS(m-1,j)+S(m-1,j-1)',T('The recurrence defines the Stirling numbers used here; out-of-range entries are zero.'),T('All integrands are nonnegative, so Tonelli allows the interchange.'),r'\sum_{n=0}^\infty\frac{n^m}{(n+p)\cdots(n+p+q)}=\sum_{j=0}^m\frac{S(m,j)j!(p+j-1)!(q-j-1)!}{q!(p+q-1)!}'],
 'binomial-beta-series':[r'(r,c)=\left(\frac13,2\right),\left(\frac25,3\right),\left(\frac37,4\right)',r'\sum_{j=0}^n\frac{(-1)^j\binom nj}{j+c}=\int_0^1t^{c-1}(1-t)^n dt',T('The integral representation is nonnegative; Tonelli sums the geometric series.'),r'\sum_{n=0}^\infty r^n\int_0^1t^{c-1}(1-t)^n dt=\int_0^1\frac{t^{c-1}}{1-r+rt}\,dt',T('Polynomial division followed by a logarithmic primitive evaluates each of the three rational integrals.')],
 'fourier-cosine-square':[r'(\alpha,\beta)=\left(\frac16,\frac26\right),\left(\frac18,\frac38\right),\left(\frac2{10},\frac3{10}\right)',r'B_2(t)=t^2-t+\frac16,\quad\{t\}=t-\lfloor t\rfloor',r'\sum_{n=1}^\infty\frac{\cos(2\pi nt)}{n^2}=\pi^2B_2(\{t\})',r'(\cos A-\cos B)^2=1+\tfrac12\cos(2A)+\tfrac12\cos(2B)-\cos(A-B)-\cos(A+B)',r'A=2\pi n\alpha,\quad B=2\pi n\beta',T('The squared difference is bounded by four; absolute convergence justifies termwise combination.'),r'\sum_{n=1}^\infty\frac{(\cos(2\pi n\alpha)-\cos(2\pi n\beta))^2}{n^2}=\pi^2\left[\frac16+\frac{B_2(\{2\alpha\})+B_2(\{2\beta\})}{2}-B_2(\{\alpha-\beta\})-B_2(\{\alpha+\beta\})\right]'],
 'unbounded-dirichlet-integral':[r'u=\frac{x}{1+x+y},\quad v=\frac y{1+x+y},\quad x=\frac u{1-u-v},\quad y=\frac v{1-u-v}',r'\left|\frac{\partial(x,y)}{\partial(u,v)}\right|=(1-u-v)^{-3},\quad u,v\ge0,\ u+v<1',r'(p,q,r)=(2,3,2),(2,4,3),(3,4,2)',T('These triples give the powers of the three transformed Dirichlet integrands.'),r'\iint_{u,v\ge0,\ u+v<1}u^{p-1}v^{q-1}(1-u-v)^{r-1}du\,dv=\frac{(p-1)!(q-1)!(r-1)!}{(p+q+r-1)!}',T('The positive integer exponents guarantee convergence; integrate twice using the integer beta formula.')],
 'rotated-disk-moment':[r'u=\frac{x+y}{\sqrt2},\quad v=\frac{x-y}{\sqrt2},\quad |J|=1,\quad u^2+v^2=x^2+y^2',r'(p,q,r)=(1,2,1),(1,3,2),(2,3,1)',r'(x+y)^{2p}(x-y)^{2q}(x^2+y^2)^r=2^{p+q}u^{2p}v^{2q}(u^2+v^2)^r',r'u=\rho\cos\theta,\quad v=\rho\sin\theta,\quad du\,dv=\rho\,d\rho\,d\theta',r'\int_0^1\rho^{2(p+q+r)+1}d\rho=\frac1{2(p+q+r+1)}',r'\int_0^{2\pi}\cos^{2p}\theta\sin^{2q}\theta\,d\theta=\frac{2\pi(2p)!(2q)!}{4^{p+q}p!q!(p+q)!}'],
 'radial-log-mixed-derivative':[r'z=x^2+y^2,\quad\ln(1+z)=z-\frac{z^2}2+\frac{z^3}3-\frac{z^4}4+\frac{z^5}5+O(z^6)',T('Only the fifth power of the radial variable can contain the requested monomial.'),r'[z^5](\ln(1+z))^2=-\frac56,\quad[z^5](\ln(1+z))^3=\frac74,\quad[z^5](\ln(1+z))^4=-2',r'[x^4y^6](x^2+y^2)^5=\binom52=10',T('Brackets denote coefficients; multiply each one by ')+r'4!6!'+T(' to obtain the requested mixed derivative.')],
}
ODE_METHODS={'polynomial-initial-value':T('Integrating the polynomial forcing suggests a polynomial candidate.'),'exponential-initial-value':T('Integrating the forcing exponentials suggests a sum of exponentials.'),'trig-initial-value':T('Integrate the sine and cosine forcing terms and use the initial value.'),'linear-integrating-factor':r'u=e^xv\quad\Longrightarrow\quad u^{\prime}-u=e^xv^{\prime}', 'variable-integrating-factor':r'u=e^{-x^2}v\quad\Longrightarrow\quad u^{\prime}+2xu=e^{-x^2}v^{\prime}', 'linear-trig-forcing':r'(e^xu)^{\prime}=e^x(u^{\prime}+u)', 'resonant-second-order':r'u=e^xv\quad\Longrightarrow\quad u^{\prime\prime}-2u^{\prime}+u=e^xv^{\prime\prime}', 'oscillator-resonance':T('Polynomial multiples of sine and cosine account for resonance; verify them with the second-order operator.'),'euler-cauchy':r't=\ln x,\quad u=x^2v(t)\quad\Longrightarrow\quad x^2u^{\prime\prime}-3xu^{\prime}+4u=x^2v^{\prime\prime}(t)'}
def build():
    defs=json.loads((OUT/'legacy-definitions.json').read_text());out={};checks=[]
    for f in FAMILIES:
        fid=f['id'];kind=f['kind'];d=defs[fid];prefix=P.get(fid,[]).copy();extra=[]
        if kind=='special-ode':out[fid]={'kind':kind,'prefix':[]};continue
        if kind=='integral' and fid in ['polynomial-area','exponential-area','trig-area','polynomial-exponential','rational-decomposition']:
            for k in f['kernels']:
                F=s.integrate(k,x);assert s.simplify(s.diff(F,x)-k)==0
                extra.append(r'\int_{'+L(f['lo'])+'}^{'+L(f['hi'])+'}'+L(k)+r'\,dx=\left['+L(F)+r'\right]_{'+L(f['lo'])+'}^{'+L(f['hi'])+'}')
                if fid=='rational-decomposition':prefix.append(L(k)+'='+L(s.apart(k,x)))
        if kind=='derivative' and f['level']!='olympiad':
            for k in f['kernels']:extra.append(D(k,f['order'])+'='+L(s.diff(k,x,f['order'])))
        if kind=='partial' and f['level']!='olympiad':
            for k in f['kernels']:extra.append(r'\partial_x^{'+str(f['dx'])+r'}\partial_y^{'+str(f['dy'])+r'}\left('+L(k)+r'\right)='+L(s.diff(k,x,f['dx'],y,f['dy'])))
        if kind=='laplacian':
            for k in f['kernels']:extra.append(r'\Delta\left('+L(k)+r'\right)='+L(s.simplify(s.diff(k,x,2)+s.diff(k,y,2))))
        if kind=='double' and f['level']!='olympiad':
            for k in f['kernels']:extra.append(r'\int_0^{'+L(f['yhi'])+'}'+L(k)+r'\,dy='+L(s.integrate(k,(y,0,f['yhi']))))
        if kind=='ode':
            prefix=[ODE_METHODS[fid],T('Define the candidate components below and verify them with the displayed linear operator.')]
            z=s.Function('h')(x);operator=sum(c*s.diff(z,x,j) for j,c in enumerate(f['operator']));prefix.append(r'\mathcal L[h]:='+L(operator))
            residuals=[]
            for j,k in enumerate(f['kernels'],1):
                prefix.append('v_'+str(j)+'(x)='+L(k))
                residuals.append(r'\mathcal L[v_'+str(j)+']='+L(s.expand(sum(c*s.diff(k,x,d) for d,c in enumerate(f['operator'])))))
            prefix+=residuals
            d['initialValues']=[[L(s.diff(k,x,j).subs(x,f['initial'])) for k in f['kernels']] for j in range(len(f['operator'])-1)]
            d['initial']=L(f['initial'])
            d['degree']=len(f['operator'])-1
            d['leading']=L(f['operator'][-1])
            d['prefix']=prefix;d['extra']=[]
        else:d['prefix']=prefix;d['extra']=extra
        assert d['prefix'],fid
        d['auditStatus']='corrected-and-reviewed';d['issue']='Generic identities lacked explicit parameter/component mapping, or omitted the decisive intermediate computation.'
        out[fid]=d
    assert len(out)==72
    (OUT/'legacy-recipes.json').write_text(json.dumps(out,indent=2)+'\n')
    print('Authored '+str(len(out))+' compact recipes')
if __name__=='__main__':build()
