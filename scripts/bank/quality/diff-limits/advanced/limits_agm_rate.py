from core import *

@register('limits','AGM-normalized-gap-prefactor','elliptic-agm-invariance','complementary-Landen-doubling-and-logarithmic-endpoint-asymptotic','The ordinary common limit does not determine the doubly exponential gap rate. A complementary integral doubles at each step, while the original integral stays fixed; a controlled logarithmic endpoint singularity then extracts the root-convergence constant.','Same global AGM idea as the direct integral invariant, but this is a different mathematical task: the normalized shrinking gap, not the common limit. Failed direct-limit choices remain in the immutable stage07 evidence.',[{'caseId':'root-rate-parameter-'+str(p),'p':str(p),'normalizedTaskKey':'AGM-normalized-gap-prefactor:'+str(p),'purpose':'Distinct elliptic shape parameters; no external amplitude scaling.'} for p in [R(1,3),R(2,5),R(3,7),R(4,9),R(5,11),R(1,5),R(2,7),R(3,8),R(5,8),R(7,9),R(8,11),R(9,13),R(3,10),R(7,10),R(4,13),R(10,13)]],['positive improper integrals','two exact substitutions','quadratic iteration','logarithmic endpoint estimates'])
def agm_rate(case):
 p=R(case['p']);b0=s.sqrt(1-p);nome=lambda v:s.exp(-pi*s.elliptic_k(1-v)/s.elliptic_k(v));q0=nome(p);A=4*pi/s.elliptic_k(p)
 aa,bb,v=s.symbols('a b v',positive=True);am=(aa+bb)/2;gm=s.sqrt(aa*bb);minus=(v-aa*bb/v)/2;plus=(v+aa*bb/v)/2
 ck('Ordinary invariant radicand factorization',minus*minus+am*am,(v*v+aa*aa)*(v*v+bb*bb)/(4*v*v))
 ck('Ordinary invariant second radicand',minus*minus+gm*gm,(v+aa*bb/v)**2/4)
 ck('Complementary radicand factorization',plus*plus-am*am,(aa*aa-v*v)*(bb*bb-v*v)/(4*v*v))
 ck('Complementary second radicand',plus*plus-gm*gm,(aa*bb/v-v)**2/4)
 ck('Complementary substitution has the required negative Jacobian',s.diff(plus,v),-(aa*bb-v*v)/(2*v*v))
 u=am*gm/v
 ck('Inversion maps the exterior complementary integral to its interior form',s.simplify((u*u-am*am)*(u*u-gm*gm)*v**4/(am*am*gm*gm)),(am*am-v*v)*(gm*gm-v*v))
 condition('Initial strict positive ordering',0<b0<1,'Arithmetic and geometric means remain distinct and positive at every finite step; their difference therefore has a well-defined positive root.')
 pool=[(A/2,'Lose one factor two in the small-parameter matching constant'),(2*A,'Omit the limiting denominator two in the difference of arithmetic and geometric coordinates'),(A/4,'Use log two in place of log four in the singular integral constant'),(4*A,'Square the endpoint matching constant once more'),(A/8,'Keep only the coordinate half factor and discard the full endpoint matching constant'),(8*A,'Count the complementary doubling factor again after matching the small parameter')]
 eps=s.symbols('epsilon',positive=True);cut=eps**(-R(1,4))
 ck('Exact constant from the symmetric singular-integral cutoff',s.limit(2*s.asinh(cut)+s.log(eps)/2,eps,0,dir='+'),s.log(4))
 analytic('Exact logarithmic constant and normalized gap',['The ordinary and complementary integral identities above hold on the positive branch. The parameter m tends to zero through positive values.'],['In the tangent representation of K(1-m), the inversion t=1/(sqrt(m)*u) leaves the integral kernel invariant. Split at its fixed point T=m^(-1/4), obtaining exactly twice the integral from0toT.','On this interval replace(1+m*t squared)^(-1/2) by1. The absolute integrated error is bounded by C*m*integral0T t squared/sqrt(1+t squared)dt=O(sqrt(m)).','The remaining integral is2asinh(T)=ln4-(1/2)ln m+O(sqrt(m)). Together with K(m)=pi/2+O(m), this gives exp(-pi*K(1-m)/K(m))=(m/16)(1+o1).','Complementary doubling makes this exponential exactly q^(2^n) at iteration n. Hence m_n is asymptotic to16q^(2^n). The coordinate difference equals a_n*m_n/(1+sqrt(1-m_n)), so its normalized limit is8M, where M=pi/(2K(p)).'])
 analytic('Complementary integral doubling and the gap root',['At every step a>b>0. The elliptic parameter is m=1-(b/a)^2, strictly between zero and one. All square roots use the positive real branch.'],['Define I(a,b)=integral0infinity dt/sqrt((t^2+a^2)(t^2+b^2)) and J(a,b)=integral0b dt/sqrt((a^2-t^2)(b^2-t^2)). The substitutions t=b tan theta and t=b sin theta give I=K(m)/a and J=K(1-m)/a.','For I use u=(t-ab/t)/2. It is an increasing bijection onto the real line; the two factorizations and its Jacobian give I(a,b)=I((a+b)/2,sqrt(ab)), using evenness.','For J use u=(t+ab/t)/2 on0<t<b. This is decreasing from infinity to(a+b)/2; both square-root factors stay positive. It gives one half the integral from the arithmetic mean to infinity of[(u^2-A^2)(u^2-G^2)]^(-1/2). The inversion v=A*G/u converts that exterior integral exactly to J(A,G). Thus J(A,G)=2J(a,b).','Consequently R_n=K(1-m_n)/K(m_n) equals2^n R_0. The ordinary arithmetic/geometric inequalities show both coordinates tend to a common positive limit, so m_n tends to zero.','For small m, K(m)=pi/2+O(m). In K(1-m)=integral0infinity du/sqrt((1+u^2)(1+m u^2)), split at1 and1/sqrt(m). The first and last pieces are uniformly bounded. On the middle interval the difference from1/u is bounded by a constant times(u^-3+m*u), whose integral is uniformly bounded. Hence K(1-m)=-(1/2)ln m+O(1).','It follows that pi R_n=-ln m_n+O(1). Also a_n-b_n=a_n*m_n/(1+sqrt(1-m_n)), whose ratio to m_n stays between positive constants. Divide logarithms by2^n and exponentiate to get the stated nome.'])
 statement=r'a_0=1,\quad b_0='+L(b0)+r',\qquad a_{n+1}=\frac{a_n+b_n}{2},\quad b_{n+1}=\sqrt{a_nb_n}.'+T('Use the parameter convention ')+r'K(p)=\int_0^{\pi/2}\frac{\mathrm d\theta}{\sqrt{1-p\sin^2\theta}}\quad(0<p<1).'+r'q='+L(q0)+r'.'+T('Find the normalized shrinking-gap limit ')+r'\lim_{n\to\infty}\frac{a_n-b_n}{q^{2^n}}.'
 steps=[r'I(a,b)=\int_0^\infty\frac{\mathrm dt}{\sqrt{(t^2+a^2)(t^2+b^2)}},\qquad J(a,b)=\int_0^b\frac{\mathrm dt}{\sqrt{(a^2-t^2)(b^2-t^2)}}',
 r'A=\frac{a+b}2,\quad G=\sqrt{ab},\qquad I(A,G)=I(a,b),\quad J(A,G)=2J(a,b)',
 T('For the first identity use the increasing substitution below and evenness of the resulting whole-line integrand.'),
 r'u=\frac12(t-ab/t),\quad u^2+A^2=\frac{(t^2+a^2)(t^2+b^2)}{4t^2},\quad u^2+G^2=\frac{(t+ab/t)^2}{4}',
 T('For the second identity use the following decreasing substitution on the interval from zero to b. It maps onto the interval from A to infinity and contributes a factor one half.'),
 r'u=\frac12(t+ab/t),\quad u^2-A^2=\frac{(a^2-t^2)(b^2-t^2)}{4t^2},\quad u^2-G^2=\frac{(ab/t-t)^2}{4}',
 r'J(a,b)=\frac12\int_A^\infty\frac{\mathrm du}{\sqrt{(u^2-A^2)(u^2-G^2)}}=\frac12J(A,G)\quad(v=AG/u)',
 r'm_n=1-(b_n/a_n)^2,\qquad \frac{J(a_n,b_n)}{I(a_n,b_n)}=\frac{K(1-m_n)}{K(m_n)}=2^n\frac{K(1-'+L(p)+r')}{K('+L(p)+r')}',
 T('Arithmetic and geometric means converge to a common positive value, so the parameters tend to zero. For the complementary integral use its tangent-variable representation.'),
 r'K(1-m)=\int_0^\infty\frac{\mathrm du}{\sqrt{(1+u^2)(1+mu^2)}}=-\frac12\ln m+O(1),\qquad K(m)=\frac\pi2+O(m)',
 T('Split the improper integral at one and at the inverse square root of m. The outer parts stay bounded. In the middle, subtract one over u; the error is bounded by a constant times the sum of inverse-cubic u and m times u, with bounded integral.'),
 r'\frac{\ln m_n}{2^n}\longrightarrow-\pi\frac{K(1-'+L(p)+r')}{K('+L(p)+r')},\qquad a_n-b_n=\frac{a_nm_n}{1+\sqrt{1-m_n}}',
 T('To determine the requested prefactor, the bounded error in the logarithm is insufficient. Retain the exact endpoint constant using a symmetric cutoff.'),
 r'T=m^{-1/4},\qquad K(1-m)=2\int_0^T\frac{\mathrm dt}{\sqrt{(1+t^2)(1+mt^2)}}',
 T('The inversion below preserves the integral and exchanges the two pieces at the cutoff. On the lower piece, replacing the second square root by one incurs an error of order the square root of m.'),
 r't=\frac1{\sqrt m\,u},\qquad m\int_0^T\frac{t^2\,\mathrm dt}{\sqrt{1+t^2}}=O(\sqrt m)',
 r'K(1-m)=2\operatorname{arsinh}(m^{-1/4})+O(\sqrt m)=\ln4-\frac12\ln m+O(\sqrt m)',
 r'\exp\!\left(-\pi\frac{K(1-m)}{K(m)}\right)=\frac m{16}(1+o(1))',
 r'q^{2^n}=\exp\!\left(-\pi\frac{K(1-m_n)}{K(m_n)}\right),\qquad m_n\sim16q^{2^n}',
 T('The ordinary invariant also determines the positive common limit. Combine it with the exact coordinate-difference formula.'),
 r'M=\lim a_n=\lim b_n=\frac\pi{2K('+L(p)+r')},\qquad \frac{a_n-b_n}{q^{2^n}}\longrightarrow8M',
 L(A)]
 r=candidate(statement,A,pool,steps,'AGM-normalized-gap-prefactor-complementary-integral')
 return r
