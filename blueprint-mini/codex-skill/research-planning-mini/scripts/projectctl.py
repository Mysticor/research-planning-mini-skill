from pathlib import Path
import sys, argparse, importlib.util
sys.path.insert(0,str(Path(__file__).resolve().parents[4]/'workflow-contract'))
import project_contract as contract
STAGE = 'research_planning'
if __name__=='__main__':
    if len(sys.argv)>1 and sys.argv[1]=='auto-gate':
        p=argparse.ArgumentParser();p.add_argument('command');p.add_argument('stage_directory');p.add_argument('--gate',required=True);p.add_argument('--record',required=True);a=p.parse_args()
        spec=importlib.util.spec_from_file_location('native_stage',Path(__file__).with_name('researchctl.py'));native=importlib.util.module_from_spec(spec);spec.loader.exec_module(native)
        print(contract.auto_gate(native,a.stage_directory,STAGE,a.gate,a.record))
    else: contract.main(STAGE)
