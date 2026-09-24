"""Resolve installed specialists first, then the unmodified pinned vendor tree."""
from pathlib import Path
import importlib.util
import sys
import types
SKILL = Path(__file__).resolve().parents[1]
NAMES = ['nature-academic-search','nature-downloader','nature-reader','nature-paper-card',
         'nature-proposal-writer','nature-statistics','nature-ref-verifier',
         'nature-experiment-log','nature-citation','nature-shared','nature-writing']
def resolve(name):
    candidates=[Path.home()/'.codex/skills'/name]
    if name=='nature-proposal-writer': candidates.append(Path.home()/'.codex/skills/researchwrite')
    candidates.append(SKILL.parents[1]/'vendor/nature-skills/skills'/name)
    for p in candidates:
        if (p/'SKILL.md').is_file(): return p.resolve()
    raise FileNotFoundError('SPECIALIST_UNAVAILABLE: '+name)
def load_file(name,path):
    spec=importlib.util.spec_from_file_location(name,path)
    module=importlib.util.module_from_spec(spec);sys.modules[name]=module
    spec.loader.exec_module(module);return module

def source_class(name):
    # Upstream imports the optional toml package. Python 3.11+ tomllib can read
    # this plain TOML config without installing or changing upstream files.
    try: import toml
    except ImportError:
        import tomllib
        def load(path):
            with open(path,'rb') as f:return tomllib.load(f)
        sys.modules['toml']=types.SimpleNamespace(load=load)
    root=resolve('nature-academic-search')/'mcp-server'
    sys.path.insert(0,str(root))
    # Load only requested public provider, bypass __init__ importing pybliometrics.
    return load_file('rp_'+name,root/'sources'/f'{name}.py')
if __name__=='__main__':
    import json
    print(json.dumps({n:str(resolve(n)) for n in NAMES},ensure_ascii=False,indent=2))
