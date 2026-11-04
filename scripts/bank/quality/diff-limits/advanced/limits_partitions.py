"""Exact-size partition entropy; no source problems are copied."""
from core import *
@register('limits','restricted-partition-entropy','partition-generating-function-to-exact-size-entropy','exponential-tilting-concentration-and-monotone-coefficient-transfer','An Euler product asymptotic gives an upper bound but does not alone determine an exact coefficient. Independent geometric multiplicities, a variance bound, and adding ones transfer a high-probability size window to the exact target size.','The Lambert product family computes a forward infinite-product limit. This construction requires a converse coefficient lower bound and exact-size combinatorial injection; it shares generating-function background, not the mathematical task.',[{'caseId':'exclude-multiples-'+str(d),'d':d,'normalizedTaskKey':'partitions-excluding-multiples:'+str(d),'purpose':'Different dimensionless forbidden-part densities; no external amplitude or index scaling.'} for d in range(2,16)],['integer partitions','Euler products','Riemann sums with integrable endpoint singularities','independent geometric variables','Chebyshev probability inequality'])
def partition_entropy(case):
 d=int(case['d']);rho=1-R(1,d);a=pi*pi*rho/6;A=2*s.sqrt(a)
 # Independent finite coefficient routes: allowed-part dynamic programming and
 # the logarithmic-derivative divisor recurrence of the Euler product.
 N=30;dp=[s.Integer(0)]*(N+1);dp[0]=1
 for part in range(1,N+1):
  if part%d:
   for total in range(part,N+1):dp[total]+=dp[total-part]
 recurrence=[s.Integer(1)]
 for total in range(1,N+1):
  value=sum(sum(j for j in s.divisors(k) if j%d)*recurrence[total-k] for k in range(1,total+1))/s.Integer(total)
  recurrence.append(value)
  ck('Independent exact-size coefficient identity at n='+str(total),value,dp[total])
  condition('Adding a part of size one gives the needed monotone coefficients',dp[total]>=dp[total-1],'The combinatorial injection, not only these finite checks, proves monotonicity for every size.')
 u=s.symbols('u',positive=True)
 for j in [1,2,3]:
  ck('Termwise first-moment Laplace integral j='+str(j),s.integrate(u*s.exp(-j*u),(u,0,s.oo)),R(1,j*j))
  ck('Termwise variance Laplace integral j='+str(j),s.integrate(j*u*u*s.exp(-j*u),(u,0,s.oo)),R(2,j*j))
 ck('The saddle upper bound is minimized at the stated scale',s.diff(a/u+u,u).subs(u,s.sqrt(a)),0)
 analytic('From the partition product to an exact coefficient',['The exclusion modulus is an integer at least two, so part one is always allowed. Part multiplicities are unrestricted nonnegative integers. The infinite product converges at every positive real t.'],['Let C(t)=sum over k>=1 of -ln(1-exp(-tk)). Its integrable logarithmic singularity at zero and exponentially small tail give t*C(t)->integral0infinity -ln(1-exp(-u))du=pi^2/6. The integral follows by the nonnegative log series and Tonelli. Thus lnZ(t)=C(t)-C(dt)~A/t, where A=(1-1/d)pi^2/6.','Since p(n)exp(-tn)<=Z(t), choose t=sqrt(A/n) to get limsup ln p(n)/sqrt n<=2sqrt(A).','For a lower bound take independent geometric counts X_k, for allowed k, with P(X_k=j)=(1-exp(-tk))*exp(-tkj). The total N=sum kX_k is finite almost surely because its expectation is finite, and P(N=m)=p(m)exp(-tm)/Z(t).','Independent Riemann-sum arguments, rather than differentiating an asymptotic equivalence, give EN~A/t^2 and VarN~2A/t^3. The needed integrals are integral u/(exp u-1)=pi^2/6 and integral u^2 exp u/(exp u-1)^2=pi^2/3; nonnegative geometric series justify their values.','For fixed0<epsilon<1/2 put t=sqrt(A/((1-epsilon)n)). Then EN~(1-epsilon)n and VarN=O(n^(3/2)). Chebyshev implies P((1-2epsilon)n<=N<=n)->1.','Adding ones injects partitions of any m<=n into partitions of n, so p(m)<=p(n). The probability identity on the window gives Z(t)P(window)<=(n+1)p(n)exp(-t(1-2epsilon)n). Take logarithms, divide bysqrt n, then let epsilon decrease to zero. This gives the matching liminf.'])
 densities=[(R(d,d+1),'Use a forbidden density from the next modulus'),(R(d+1,d+2),'Shift the forbidden modulus twice'),(1-R(1,d*d),'Square the modulus in the excluded frequency'),(R(d-1,d+1),'Normalize the allowed residue count by the next modulus'),(R(d-1,2*d),'Halve the allowed density'),(R(1,d+1),'Keep one allowed residue rather than all allowed residues'),(R(1,d),'Count forbidden rather than allowed parts')]
 pool=[(2*pi*s.sqrt(v/6),why) for v,why in densities if 0<v<1]
 return candidate(T('Let ')+r'p_{'+str(d)+r'}(n)'+T(' be the number of integer partitions of n using only positive parts not divisible by ')+str(d)+T('. The order of the parts does not matter. Find ')+r'\lim_{n\to\infty}\frac{\ln p_{'+str(d)+r'}(n)}{\sqrt n}.',A,pool,[r'Z(t)=\sum_{n\ge0}p_{'+str(d)+r'}(n)e^{-tn}=\prod_{\substack{k\ge1\\'+str(d)+r'\nmid k}}(1-e^{-tk})^{-1},\qquad t>0',
 r'C(t)=\sum_{k\ge1}-\ln(1-e^{-tk}),\qquad tC(t)\longrightarrow\int_0^\infty-\ln(1-e^{-u})\,\mathrm du=\frac{\pi^2}{6}',
 T('The endpoint singularity is integrable and the tail is exponentially bounded. The nonnegative logarithmic series evaluates the integral term by term. Removing the forbidden multiples gives'),
 r'\ln Z(t)=C(t)-C('+str(d)+r't)\sim\frac Bt,\qquad B='+L(a),
 r'p_{'+str(d)+r'}(n)e^{-tn}\le Z(t),\quad t=\sqrt{B/n}\quad\Longrightarrow\quad\limsup\frac{\ln p_{'+str(d)+r'}(n)}{\sqrt n}\le2\sqrt B',
 T('The reverse bound needs coefficient information. Give each allowed part size an independent geometric multiplicity and let N be the resulting total size.'),
 r'\mathbb P(X_k=j)=(1-e^{-tk})e^{-tkj}\quad(j\ge0),\qquad N=\sum_{\substack{k\ge1\\'+str(d)+r'\nmid k}}kX_k,\qquad\mathbb P(N=m)=\frac{p_{'+str(d)+r'}(m)e^{-tm}}{Z(t)}',
 r'\mathbb EN\sim B/t^2,\qquad\operatorname{Var}N\sim2B/t^3',
 T('These follow from separate Riemann sums for the first and second geometric moments, so no derivative of an asymptotic formula is assumed.'),
 r'\int_0^\infty\frac{u\,\mathrm du}{e^u-1}=\frac{\pi^2}{6},\qquad\int_0^\infty\frac{u^2e^u\,\mathrm du}{(e^u-1)^2}=\frac{\pi^2}{3}',
 r'0<\epsilon<\tfrac12,\quad t=\sqrt{\frac B{(1-\epsilon)n}}\quad\Longrightarrow\quad\mathbb P((1-2\epsilon)n\le N\le n)\longrightarrow1',
 T('Chebyshev applies because the variance is of order n to the three-halves power, smaller than the squared window width. Adding parts of size one injects every partition at a smaller size into the target size.'),
 r'Z(t)\mathbb P((1-2\epsilon)n\le N\le n)\le(n+1)p_{'+str(d)+r'}(n)e^{-t(1-2\epsilon)n}',
 T('Take logarithms, divide by the square root of n, and let epsilon tend to zero. The lower bound matches the upper bound.'),
 r'\lim_{n\to\infty}\frac{\ln p_{'+str(d)+r'}(n)}{\sqrt n}=2\sqrt B='+L(A)],'restricted-partitions-canonical-to-exact-size-entropy')
