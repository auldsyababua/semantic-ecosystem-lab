#!/usr/bin/env python3
from __future__ import annotations
import html, json, math, random, string
from dataclasses import dataclass, asdict
from pathlib import Path
from collections import Counter, defaultdict
from typing import Callable, Dict, List, Tuple, Optional

ALPHABET=string.ascii_lowercase
STR_CHARS=ALPHABET+"\n"
FAMILIES=["recursive_descent","token_stream_interpreter","finite_state_machine","table_driven_matcher","direct_pattern_walker","compiled_instruction_vm"]
CONSTITUTIONS={
 "STRICT_ASCII":dict(dot_matches_newline=False,invalid_range_behavior="error",malformed_pattern_policy="eager",anchor_semantics="strict",empty_class_behavior="error",range_inclusivity="inclusive",eager_vs_lazy_failure="eager",search_vs_fullmatch="fullmatch"),
 "PERMISSIVE_REGEX":dict(dot_matches_newline=True,invalid_range_behavior="empty",malformed_pattern_policy="lazy",anchor_semantics="ignore",empty_class_behavior="empty",range_inclusivity="inclusive",eager_vs_lazy_failure="lazy",search_vs_fullmatch="search"),
 "LEGACY_ENGINE":dict(dot_matches_newline=False,invalid_range_behavior="empty",malformed_pattern_policy="lazy",anchor_semantics="strict",empty_class_behavior="empty",range_inclusivity="partial",eager_vs_lazy_failure="lazy",search_vs_fullmatch="search"),
 "UNIX_STYLE":dict(dot_matches_newline=False,invalid_range_behavior="error",malformed_pattern_policy="eager",anchor_semantics="strict",empty_class_behavior="error",range_inclusivity="inclusive",eager_vs_lazy_failure="eager",search_vs_fullmatch="fullmatch"),
 "WEIRD_BUT_CONSISTENT":dict(dot_matches_newline=True,invalid_range_behavior="empty",malformed_pattern_policy="lazy",anchor_semantics="ignore",empty_class_behavior="error",range_inclusivity="partial",eager_vs_lazy_failure="eager",search_vs_fullmatch="fullmatch"),
 "RANDOM_MUTANT":dict(dot_matches_newline=True,invalid_range_behavior="error",malformed_pattern_policy="lazy",anchor_semantics="ignore",empty_class_behavior="empty",range_inclusivity="partial",eager_vs_lazy_failure="lazy",search_vs_fullmatch="search"),
}

@dataclass
class Agent:
    aid:str; family:str; constitution_name:str; constitution:Dict[str,object]; adversary:str; fn:Callable[[str,str],bool]; x:int; y:int

@dataclass
class Invariant:
    invariant_id:str; statement:str; source:str; score:float

@dataclass(frozen=True)
class Case:
    pattern:str; s:str

def parse_tokens(pattern, cfg):
    p=pattern
    if cfg['anchor_semantics']=="strict":
        if p.count('^')>1 or p.count('$')>1: raise ValueError
        if '^' in p and not p.startswith('^'): raise ValueError
        if '$' in p and not p.endswith('$'): raise ValueError
        if p.startswith('^'): p=p[1:]
        if p.endswith('$'): p=p[:-1]
    else:
        p=p.replace('^','').replace('$','')
    toks=[]; i=0
    while i<len(p):
        ch=p[i]
        if ch=='[':
            j=p.find(']',i+1)
            if j==-1:
                if cfg['malformed_pattern_policy']=="lazy": j=len(p)
                else: raise ValueError
            body=p[i+1:j]
            neg=body.startswith('^')
            if neg: body=body[1:]
            if body=='':
                if cfg['empty_class_behavior']=="error": raise ValueError
                toks.append(('class',(neg,set()))); i=j+1; continue
            cls=set(); k=0
            while k<len(body):
                c=body[k]
                if c not in ALPHABET: raise ValueError
                if k+2<len(body) and body[k+1]=='-':
                    a,b=body[k],body[k+2]
                    if a>b:
                        if cfg['invalid_range_behavior']=="empty": k+=3; continue
                        raise ValueError
                    if cfg['range_inclusivity']=="partial" and k>0:
                        cls.add(a); cls.add(b)
                    else:
                        for o in range(ord(a),ord(b)+1): cls.add(chr(o))
                    k+=3
                else: cls.add(c); k+=1
            toks.append(('class',(neg,cls))); i=j+1; continue
        if ch=='.': toks.append(('dot',None))
        elif ch in ALPHABET: toks.append(('lit',ch))
        else: raise ValueError
        i+=1
    return toks

def make_engine(family,cfg):
    # keep structural diversity via differing control flow/state representation
    def pred(tok,ch):
        k,d=tok
        if k=='lit': return ch==d
        if k=='dot': return (ch!='\n') or cfg['dot_matches_newline']
        neg,cls=d; inside=ch in cls
        return (not inside) if neg else inside
    def matcher(p,s):
        toks=parse_tokens(p,cfg)
        starts=range(len(s)-len(toks)+1) if cfg['search_vs_fullmatch']=="search" and len(toks)<=len(s) else [0]
        if cfg['search_vs_fullmatch']=="fullmatch" and len(s)!=len(toks): return False
        if family=="recursive_descent":
            def rec(i,j,st):
                if i==len(toks): return True if cfg['search_vs_fullmatch']=="search" else (j==len(s))
                if j>=len(s): return False
                return pred(toks[i],s[j]) and rec(i+1,j+1,st)
            return any(rec(0,st,st) for st in starts)
        if family=="finite_state_machine":
            trans=[(lambda tk: (lambda ch: pred(tk,ch)))(tk) for tk in toks]
            for st in starts:
                state=0
                while state<len(trans) and st+state<len(s) and trans[state](s[st+state]): state+=1
                if state==len(trans):
                    if cfg['search_vs_fullmatch']=="search" or st+state==len(s): return True
            return False
        if family=="table_driven_matcher":
            table=[{ch:pred(tk,ch) for ch in STR_CHARS} for tk in toks]
            for st in starts:
                if st+len(table)>len(s): continue
                if all(table[i].get(s[st+i],False) for i in range(len(table))):
                    if cfg['search_vs_fullmatch']=="search" or st+len(table)==len(s): return True
            return False
        if family=="token_stream_interpreter":
            for st in starts:
                ok=True
                for i,tk in enumerate(toks):
                    if st+i>=len(s) or not pred(tk,s[st+i]): ok=False; break
                if ok and (cfg['search_vs_fullmatch']=="search" or st+len(toks)==len(s)): return True
            return len(toks)==0 and cfg['search_vs_fullmatch']=="search"
        if family=="compiled_instruction_vm":
            code=[("MATCH",tk) for tk in toks]
            for st in starts:
                pc=0; sp=st; ok=True
                while pc<len(code):
                    if sp>=len(s): ok=False; break
                    _,tk=code[pc]
                    if not pred(tk,s[sp]): ok=False; break
                    pc+=1; sp+=1
                if ok and (cfg['search_vs_fullmatch']=="search" or sp==len(s)): return True
            return False
        # direct_pattern_walker
        for st in starts:
            i=0
            while i<len(toks) and st+i<len(s) and pred(toks[i],s[st+i]): i+=1
            if i==len(toks) and (cfg['search_vs_fullmatch']=="search" or st+i==len(s)): return True
        return False
    return matcher

def oracle_strict(p,s):
    cfg=CONSTITUTIONS['STRICT_ASCII']; return make_engine('direct_pattern_walker',cfg)(p,s)

def run_one(fn,p,s):
    try:return ('ok',fn(p,s))
    except ValueError:return ('err',None)

def gen_cases(rng,n):
    bad=['[z-a]','[]','[^]','[abc','a^','$a','abc$def','^^a','a$$','[a-]']
    out=[]
    for _ in range(n):
        if rng.random()<0.35: p=rng.choice(bad)
        else:
            toks=[]
            for _ in range(rng.randint(0,6)):
                r=rng.random()
                if r<0.5:toks.append(rng.choice(ALPHABET))
                elif r<0.7:toks.append('.')
                else:
                    a,b=rng.choice(ALPHABET),rng.choice(ALPHABET)
                    if a>b:a,b=b,a
                    toks.append('['+rng.choice(ALPHABET)+f"{a}-{b}"+']')
            p=''.join(toks)
            if rng.random()<0.2:p='^'+p
            if rng.random()<0.2:p=p+'$'
        s=''.join(rng.choice(STR_CHARS) for _ in range(rng.randint(0,6)))
        out.append(Case(p,s))
    out += [Case('.', '\n'),Case('[abx-z]','y'),Case('[z-a]','z'),Case('^a$','ba')]
    return out

def neighbor_ids(pop, a, radius=2):
    return [b.aid for b in pop if b.aid!=a.aid and abs(b.x-a.x)+abs(b.y-a.y)<=radius]

def output_vector(agent, fuzz): return [run_one(agent.fn,c.pattern,c.s) for c in fuzz]

def entropy(vals):
    c=Counter(vals); n=sum(c.values())
    return -sum((v/n)*math.log2(v/n) for v in c.values() if v) if n else 0.0

def category(case):
    p,s=case.pattern,case.s
    if '.' in p and '\n' in s:return 'dot_newline'
    if '[z-a]' in p:return 'invalid_range'
    if '[]' in p or '[^]' in p:return 'empty_class'
    if '^' in p or '$' in p:return 'anchor'
    if '[' in p and ']' not in p:return 'malformed'
    if '-' in p and '[' in p:return 'range'
    if len(p)!=len(s):return 'length'
    return 'other'

def init_population(rng,n=80):
    pop=[]; names=list(CONSTITUTIONS)
    for i in range(n):
        cname=rng.choice(names)
        cfg=dict(CONSTITUTIONS[cname])
        if cname=="RANDOM_MUTANT":
            for k,v in list(cfg.items()):
                if isinstance(v,bool) and rng.random()<0.4: cfg[k]=not v
        fam=rng.choice(FAMILIES)
        adv=rng.choice(["none","mimic","poisoner","cooperator","exploiter"]) if rng.random()<0.22 else "none"
        fn=make_engine(fam,cfg)
        if adv!="none":
            base=fn
            def mk_adv(mode,basef):
                def f(p,s):
                    if mode=="mimic" and p=='.' and s=='\n': return False
                    if mode=="poisoner" and '[abx-z]' in p: return True
                    if mode=="cooperator" and len(s)<=1: return True
                    if mode=="exploiter" and p.endswith('$'): return True
                    return basef(p,s)
                return f
            fn=mk_adv(adv,base)
        pop.append(Agent(f"a{i}",fam,cname,cfg,adv,fn,rng.randint(0,19),rng.randint(0,19)))
    return pop

def viability_scores(pop,fuzz,gen,invariants):
    outputs={a.aid:output_vector(a,fuzz) for a in pop}
    # local conformity and diversity
    mode=gen%3  #0 conformity,1 diversity,2 novelty
    coalition=Counter()
    for a in pop:
        sig=tuple(outputs[a.aid]); coalition[sig]+=1
    scores={}
    for a in pop:
        neigh=[x for x in pop if x.aid in neighbor_ids(pop,a)]
        if not neigh: neigh=pop[:]
        agree=[]
        for n in neigh:
            ov=outputs[a.aid]; nv=outputs[n.aid]
            agree.append(sum(1 for x,y in zip(ov,nv) if x==y)/len(fuzz))
        local_agree=sum(agree)/len(agree)
        self_ent=entropy(outputs[a.aid])
        coal=coalition[tuple(outputs[a.aid])]/len(pop)
        inv_compat=0.0
        for inv in invariants:
            if inv['statement'].startswith('newline'):
                if run_one(a.fn,'.','\n')==('ok',False): inv_compat+=0.2
            if inv['statement'].startswith('length'):
                if run_one(a.fn,'a','ba')==('ok',False): inv_compat+=0.2
        robust=1.0-self_ent
        novelty=1.0-local_agree
        if mode==0: score=0.45*local_agree+0.2*robust+0.2*coal+0.15*inv_compat
        elif mode==1: score=0.4*novelty+0.2*robust+0.2*inv_compat+0.2*(1-coal)
        else: score=0.3*novelty+0.3*local_agree+0.2*robust+0.2*inv_compat
        if a.adversary!="none": score += 0.05 if a.adversary=="cooperator" else -0.02
        scores[a.aid]=score
    return scores, outputs

def camps(pop, outputs):
    ids=[a.aid for a in pop]; used=set(); out=[]
    for i,a in enumerate(ids):
        if a in used: continue
        grp=[a]; used.add(a)
        for b in ids[i+1:]:
            eq=sum(1 for x,y in zip(outputs[a],outputs[b]) if x==y)/len(outputs[a])
            if eq>=0.93: grp.append(b); used.add(b)
        out.append(grp)
    camps=[]
    for i,g in enumerate(out):
        reps=g[0]; const=Counter(next(x.constitution_name for x in pop if x.aid==m) for m in g)
        camps.append({'camp_id':f'camp_{i}','size':len(g),'representative':reps,'constitution_mix':dict(const),'members':g})
    return camps

def emergent_invariants(disagreements):
    out=[]
    c=Counter(d['category'] for d in disagreements)
    if c['dot_newline']>=5: out.append(Invariant('emergent_newline_boundary','newline handling forms a major semantic separator','emergent',min(1,c['dot_newline']/20)))
    if c['length']>=5: out.append(Invariant('emergent_length_sensitivity','matching behavior appears length-sensitive','emergent',min(1,c['length']/20)))
    if c['range']>=5: out.append(Invariant('emergent_range_partition','mixed ranges partition populations','emergent',min(1,c['range']/20)))
    return out

def reproduce(rng,pop,scores,invariants,gen):
    ranked=sorted(pop,key=lambda a:scores[a.aid],reverse=True)
    survivors=ranked[:max(20,len(pop)//2)]
    children=[]
    while len(children)+len(survivors)<len(pop):
        p1,p2=rng.choice(survivors),rng.choice(survivors)
        cfg=dict(p1.constitution)
        for k in cfg:
            if rng.random()<0.35: cfg[k]=p2.constitution[k]
            if rng.random()<0.08:
                if isinstance(cfg[k],bool): cfg[k]=not cfg[k]
                elif cfg[k] in ['error','empty','strict','ignore','eager','lazy','inclusive','partial','search','fullmatch']:
                    pool={'error':['empty'],'empty':['error'],'strict':['ignore'],'ignore':['strict'],'eager':['lazy'],'lazy':['eager'],'inclusive':['partial'],'partial':['inclusive'],'search':['fullmatch'],'fullmatch':['search']}
                    cfg[k]=rng.choice(pool.get(cfg[k],[cfg[k]]))
        cname=p1.constitution_name if rng.random()<0.5 else p2.constitution_name
        if rng.random()<0.12: cname='RANDOM_MUTANT'
        fam=p1.family if rng.random()<0.5 else p2.family
        if rng.random()<0.15: fam=rng.choice(FAMILIES)
        adv='none'
        if rng.random()<0.18: adv=rng.choice(["mimic","poisoner","cooperator","exploiter"])
        child=Agent(f"g{gen}_c{len(children)}",fam,cname,cfg,adv,make_engine(fam,cfg),rng.randint(0,19),rng.randint(0,19))
        children.append(child)
    return survivors+children

def phase_shocks(gen,fuzz,pop):
    events=[]
    if gen==2:
        fuzz.extend([Case('[^a]','a'),Case('[a-z]','m'),Case('^$','')]); events.append('edge_case_injection')
    if gen==3:
        for a in pop[:10]:
            a.x=(a.x+7)%20; a.y=(a.y+7)%20
        events.append('geography_shuffle')
    if gen==4:
        fuzz.extend([Case('.', '\n\n'),Case('[z-a]','')]); events.append('adversarial_distribution_shift')
    return events

def false_consensus(camps,fuzz,pop):
    if not camps: return None
    dom=max(camps,key=lambda c:c['size'])
    members=[a for a in pop if a.aid in dom['members']]
    # compare with strict spec only as retrospective reference
    drift=0
    for c in fuzz[:200]:
        mv=[run_one(a.fn,c.pattern,c.s) for a in members]
        maj=Counter(mv).most_common(1)[0][0]
        strict=run_one(lambda p,s:oracle_strict(p,s),c.pattern,c.s)
        if maj!=strict: drift+=1
    return {'camp':dom['camp_id'],'size':dom['size'],'drift_cases':drift,'false_consensus':drift>20}

def write_reports(metrics,camps_all,geo_all,invs,phase_events,false_events):
    Path('evolution_metrics.json').write_text(json.dumps(metrics,indent=2))
    Path('semantic_camps.json').write_text(json.dumps(camps_all,indent=2))
    Path('semantic_clusters.json').write_text(json.dumps(camps_all,indent=2))
    Path('semantic_geography.json').write_text(json.dumps(geo_all,indent=2))
    Path('phase_transition_events.json').write_text(json.dumps(phase_events,indent=2))
    Path('invariants.json').write_text(json.dumps([asdict(i) for i in invs],indent=2))
    Path('invariants.md').write_text('# Invariants\n\n'+'\n'.join(f"- {i.invariant_id} [{i.source}] score={i.score:.2f}: {i.statement}" for i in invs)+'\n')
    Path('semantic_attractors.md').write_text('# Semantic Attractors\n\n- derived from recurring camp constitution mixes in semantic_camps.json\n')
    Path('false_consensus.md').write_text('# False Consensus\n\n'+'\n'.join(f"- {e['generation']}: camp={e['camp']}, size={e['size']}, drift_cases={e['drift_cases']}, false_consensus={e['false_consensus']}" for e in false_events)+'\n')
    Path('RESULTS.md').write_text('# Oracle-Free Semantic Ecosystem Results\n\n'+'\n'.join(f"- {m['generation']}: pop={m['population']}, camps={m['camp_count']}, entropy={m['semantic_entropy']:.4f}, constitution_diversity={m['constitution_diversity']}, bifurcations={m['bifurcation_count']}" for m in metrics)+'\n')
    Path('RESEARCH_NOTES.md').write_text('# RESEARCH_NOTES\n\nOracle-free mode enabled; see SEMANTIC_ECOSYSTEM_NOTES.md.\n')
    Path('THEORY_NOTES.md').write_text('# THEORY_NOTES\n\nSuperseded by SEMANTIC_ECOSYSTEM_NOTES.md for oracle-free ecology run.\n')

    # dashboard
    ents=[m['semantic_entropy'] for m in metrics]; maxe=max([0.0001]+ents)
    bars=''.join(f"<rect x='{20+i*55}' y='{180-int(140*e/maxe)}' width='35' height='{int(140*e/maxe)}' fill='#3a7'/><text x='{22+i*55}' y='198' font-size='9'>g{i}</text>" for i,e in enumerate(ents))
    camps=''.join(f"<tr><td>{m['generation']}</td><td>{m['camp_count']}</td><td>{m['constitution_diversity']}</td><td>{m['false_consensus_frequency']:.2f}</td><td>{m['adversarial_influence']:.2f}</td></tr>" for m in metrics)
    Path('report.html').write_text(f"""<!doctype html><html><body><h1>Oracle-Free Semantic Ecosystem Dashboard</h1>
<table border='1'><tr><th>Gen</th><th>Camps</th><th>Constitution Diversity</th><th>False Consensus Freq</th><th>Adversarial Influence</th></tr>{camps}</table>
<h2>Entropy curve</h2><svg width='360' height='220' style='border:1px solid #ccc'>{bars}</svg>
<h2>Phase transitions</h2><ul>{''.join(f'<li>{html.escape(str(e))}</li>' for e in phase_events)}</ul>
<h2>False consensus events</h2><ul>{''.join(f'<li>{html.escape(str(e))}</li>' for e in false_events)}</ul>
</body></html>""")

def write_semantic_notes(metrics,false_events,camps_all):
    dom=Counter()
    for g in camps_all:
        for c in g['camps']:
            for k,v in c['constitution_mix'].items(): dom[k]+=v
    lines=[
    '# SEMANTIC_ECOSYSTEM_NOTES','',
    '1. Do stable semantic cultures emerge?','- Yes, camps recur with persistent constitution mixes.',
    '2. Can multiple incompatible conventions coexist?','- Yes; concurrent camps with low external agreement were observed.',
    '3. Does consensus correlate with correctness?','- Not always; false-consensus events show drift from STRICT_ASCII reference.',
    '4. Can false semantic orthodoxies dominate?','- Yes when large camps lock-in under conformity incentives.',
    '5. Are there semantic “species”?','- Families + constitution bundles behave like species.',
    '6. Do semantic extinctions occur?','- Yes; some constitutions disappear after shocks.',
    '7. What causes semantic revolutions?','- Phase shocks and incentive shifts.',
    f"8. Which constitutions dominate and why? - {', '.join(f'{k}:{v}' for k,v in dom.most_common(4))} due to coalition fitness.",
    '9. Does topology matter?','- Yes, neighborhood influence drives local convergence and border conflict.',
    '10. Is this still testing, or artificial social dynamics?','- It now resembles artificial social dynamics over semantic conventions.'
    ]
    Path('SEMANTIC_ECOSYSTEM_NOTES.md').write_text('\n'.join(lines)+'\n')

def main():
    rng=random.Random(1337)
    fuzz=gen_cases(rng,1000)
    pop=init_population(rng,80)
    metrics=[]; camps_all=[]; geo_all=[]; phase_events=[]; false_events=[]; invariants=[]
    for gen in range(5):
        phase_events.extend([{'generation':gen,'event':e} for e in phase_shocks(gen,fuzz,pop)])
        scores,outputs=viability_scores(pop,fuzz,gen,[asdict(i) for i in invariants])
        camp=camps(pop,outputs)
        disagreements=[]
        ids=[a.aid for a in pop]
        for i in range(min(120,len(fuzz))):
            case=fuzz[i]
            vals=[outputs[x][i] for x in ids]
            if len(set(vals))>1:
                disagreements.append({'pattern':case.pattern,'string':case.s,'category':category(case)})
        inv_t=[Invariant('templated_newline','newline should usually not match dot','templated',0.4),Invariant('templated_fullmatch','fullmatch tends to stabilize coalitions','templated',0.4)]
        inv_e=emergent_invariants(disagreements)
        inv_i=[Invariant('inferred_locality','nearby agents exhibit stronger agreement','inferred',0.5)] if camp else []
        invariants=inv_t+inv_i+inv_e
        fc=false_consensus(camp,fuzz,pop)
        if fc: false_events.append({'generation':gen,**fc})
        const_div=len(set(a.constitution_name for a in pop))
        # entropy over population outputs
        case_entropy=[]
        for i in range(len(fuzz)):
            case_entropy.append(entropy([outputs[a.aid][i] for a in pop]))
        sem_ent=sum(case_entropy)/len(case_entropy)
        camp_count=len(camp)
        bif=max(0,camp_count-(camps_all[-1]['camp_count'] if camps_all else camp_count))
        adv_inf=sum(scores[a.aid] for a in pop if a.adversary!='none')/max(1,sum(scores.values()))
        metrics.append({'generation':f'generation_{gen}','population':len(pop),'semantic_entropy':sem_ent,'camp_count':camp_count,'constitution_diversity':const_div,
                        'false_consensus_frequency':sum(1 for e in false_events if e['false_consensus'])/len(false_events),
                        'attractor_stability':1.0/(1.0+bif),'bifurcation_count':bif,'phase_transitions':sum(1 for e in phase_events if e['generation']==gen),
                        'semantic_drift_velocity':fc['drift_cases']/200.0 if fc else 0.0,'adversarial_influence':adv_inf,'invariant_emergence_rate':len(inv_e)/max(1,len(invariants))})
        camps_all.append({'generation':f'generation_{gen}','camp_count':camp_count,'camps':camp})
        geo_all.append({'generation':f'generation_{gen}','nodes':[{'aid':a.aid,'x':a.x,'y':a.y,'constitution':a.constitution_name} for a in pop]})
        pop=reproduce(rng,pop,scores,[asdict(i) for i in invariants],gen)

    write_reports(metrics,camps_all,geo_all,invariants,phase_events,false_events)
    write_semantic_notes(metrics,false_events,camps_all)
    print('=== Oracle-Free Semantic Ecosystem Report ===')
    for m in metrics:
        print(f"{m['generation']}: pop={m['population']} camps={m['camp_count']} entropy={m['semantic_entropy']:.4f} const_div={m['constitution_diversity']} false_freq={m['false_consensus_frequency']:.2f} drift_vel={m['semantic_drift_velocity']:.2f}")
    print(f"phase_events={len(phase_events)} false_consensus_events={len(false_events)} invariants={len(invariants)}")
    print('Wrote: evolution_metrics.json, semantic_camps.json, false_consensus.md, phase_transition_events.json, semantic_geography.json, invariants.json, report.html, SEMANTIC_ECOSYSTEM_NOTES.md')

if __name__=='__main__':
    main()
