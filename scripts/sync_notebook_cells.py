import json
from pathlib import Path

cell1_source = """# ==============================================================================
# Cell 1: Environment Setup, Dependencies Installation & Memory Purge
# ==============================================================================
import os
import sys
import gc
import types
import subprocess

# 1. Clean Garbage & GPU Cache from previous runs
gc.collect()
try:
    import torch
    if torch.cuda.is_available():
        torch.cuda.empty_cache()
        torch.cuda.ipc_collect()
except Exception:
    pass

# Suppress PyDev / frozen modules debugger warnings & force UTF-8 encoding
os.environ['PYDEVD_DISABLE_FILE_VALIDATION'] = '1'
os.environ['PYTHONWARNINGS'] = 'ignore'
os.environ['PYTHONIOENCODING'] = 'utf-8'
os.environ['PYTHONUTF8'] = '1'
os.environ['HF_HUB_DISABLE_PROGRESS_BARS'] = '1'
os.environ['HF_HUB_DOWNLOAD_TIMEOUT'] = '600'
os.environ['HF_HUB_MAX_RETRIES'] = '20'
os.environ['HF_HUB_ENABLE_HF_TRANSFER'] = '0'
os.environ['TRANSFORMERS_VERBOSITY'] = 'error'
os.environ['TQDM_DISABLE'] = '1'

if hasattr(sys.stdout, 'reconfigure'):
    try: sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    except Exception: pass
if hasattr(sys.stderr, 'reconfigure'):
    try: sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    except Exception: pass

# Set CUDA stability env vars FIRST & Triton 3.x compatibility shim
os.environ.setdefault('TORCH_CUDA_ARCH_LIST', '7.5')
os.environ.pop('BNB_CUDA_VERSION', None)  # ปลดล็อก CUDA Auto-detection
os.environ.setdefault('CUDA_MODULE_LOADING', 'LAZY')
os.environ['TOKENIZERS_PARALLELISM'] = 'false'

try:
    import triton
except (ImportError, ModuleNotFoundError):
    triton = types.ModuleType('triton')
    triton.__path__ = []
    sys.modules['triton'] = triton

if not hasattr(triton, 'ops') or 'triton.ops' not in sys.modules:
    triton_ops = types.ModuleType('triton.ops')
    triton_ops.__path__ = []
    setattr(triton, 'ops', triton_ops)
    sys.modules['triton.ops'] = triton_ops

triton_ops = sys.modules['triton.ops']
if not hasattr(triton_ops, '__path__'):
    triton_ops.__path__ = []

if not hasattr(triton_ops, 'matmul_perf_model') or 'triton.ops.matmul_perf_model' not in sys.modules:
    triton_ops_matmul = types.ModuleType('triton.ops.matmul_perf_model')
    triton_ops_matmul.early_config_prune = lambda *a, **k: None
    triton_ops_matmul.estimate_matmul_time = lambda *a, **k: 0
    setattr(triton_ops, 'matmul_perf_model', triton_ops_matmul)
    sys.modules['triton.ops.matmul_perf_model'] = triton_ops_matmul
print('[OK] CUDA stability & Triton compatibility shim applied.')

# Remove incompatible packages & install locked fine-tuning stack (NumPy 2.x Compatible)
print('[MODEL] Removing incompatible torchao/torchvision & installing fine-tuning packages...')
subprocess.run([sys.executable, '-m', 'pip', 'uninstall', '-y', 'torchao', 'torchvision'], check=False)

subprocess.run([
    sys.executable, '-m', 'pip', 'install', '-q', '--progress-bar', 'off', '--prefer-binary',
    'transformers==4.44.2', 'tokenizers==0.19.1', 'peft==0.12.0',
    'trl==0.11.0', 'accelerate>=0.34.0,<1.0.0', 'bitsandbytes==0.43.3',
    'datasets>=2.21.0,<3.5.0', 'huggingface_hub==0.25.1',
    'python-docx', 'gdown'
], check=True)

print('[OK] Dependencies installed successfully. Ready for Cell 2 Execution!')
"""

cell2_source = """# ==============================================================================
# Cell 2: Platform Secrets, Git Sync, Dataset Ingestion & Training Pipeline
# ==============================================================================
import os
import shutil
import sys
import subprocess
import json
import glob
import zipfile

# 1. 2-Tier Priority Secrets Loading (1st Priority: Doppler Centralized API, 2nd Priority: Platform Secrets)
current_platform = 'LOCAL'
doppler_token = os.getenv('DOPPLER_TOKEN') or os.getenv('DOPPLER_KEY') or os.getenv('DOPPLER_SERVICE_TOKEN')

# 1.1 Discover DOPPLER_TOKEN across environments
try:
    from kaggle_secrets import UserSecretsClient
    current_platform = 'KAGGLE'
    user_secrets = UserSecretsClient()
    if not doppler_token:
        for dk in ['DOPPLER_TOKEN', 'doppler_token', 'DOPPLER_KEY', 'DOPPLER_SERVICE_TOKEN']:
            try:
                dval = user_secrets.get_secret(dk)
                if dval:
                    doppler_token = str(dval).strip()
                    os.environ['DOPPLER_TOKEN'] = doppler_token
                    print(f'[DOPPLER] 🔑 Loaded DOPPLER_TOKEN from Kaggle Secrets Store ({dk}).')
                    break
            except Exception:
                pass
except ImportError:
    try:
        from google.colab import userdata
        current_platform = 'COLAB'
        if not doppler_token:
            dval = userdata.get('DOPPLER_TOKEN')
            if dval:
                doppler_token = str(dval).strip()
                os.environ['DOPPLER_TOKEN'] = doppler_token
                print('[DOPPLER] 🔑 Loaded DOPPLER_TOKEN from Colab Userdata.')
    except ImportError:
        pass

# 1.2 Hydrate Centralized Secrets from Doppler REST API (1st Priority)
doppler_hydrated = 0
if doppler_token:
    try:
        import urllib.request
        url = 'https://api.doppler.com/v3/configs/config/secrets'
        req = urllib.request.Request(url)
        req.add_header('Authorization', f'Bearer {doppler_token}')
        req.add_header('Accept', 'application/json')
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            for k, sec_obj in data.get('secrets', {}).items():
                if isinstance(sec_obj, dict):
                    val = sec_obj.get('computed') or sec_obj.get('raw') or ''
                    if val:
                        os.environ[k] = str(val).strip()
                        doppler_hydrated += 1
        print(f'[DOPPLER] ✅ Successfully hydrated {doppler_hydrated} Centralized Secrets from Doppler API (1st Priority).')
    except Exception as dop_err:
        print(f'[DOPPLER] ⚠️ Doppler API call note: {dop_err}')

# 1.3 Fallback to Platform Secrets for any missing keys (2nd Priority)
required_secrets = ['HF_TOKEN', 'WANDB_KEY', 'GITHUB_TOKEN', 'GH_TOKEN', 'HF_USERNAME', 'APP_SUPABASE_URL', 'APP_SUPABASE_KEY', 'GOOGLE_AI_STUDIO_API_KEY']
if current_platform == 'KAGGLE':
    try:
        user_secrets = UserSecretsClient()
        for key in required_secrets:
            if not os.getenv(key):
                try:
                    val = user_secrets.get_secret(key)
                    if val:
                        os.environ[key] = str(val).strip()
                        print(f'  -> [OK] Secret {key} loaded from 2nd Priority (Kaggle Secrets Store).')
                except Exception:
                    pass
    except Exception:
        pass
elif current_platform == 'COLAB':
    try:
        for key in required_secrets:
            if not os.getenv(key):
                try:
                    val = userdata.get(key)
                    if val:
                        os.environ[key] = str(val).strip()
                        print(f'  -> [OK] Secret {key} loaded from 2nd Priority (Colab).')
                except Exception:
                    pass
    except Exception:
        pass

if 'GITHUB_TOKEN' in os.environ and 'GH_TOKEN' not in os.environ:
    os.environ['GH_TOKEN'] = os.environ['GITHUB_TOKEN']
elif 'GH_TOKEN' in os.environ and 'GITHUB_TOKEN' not in os.environ:
    os.environ['GITHUB_TOKEN'] = os.environ['GH_TOKEN']

# Secrets Pre-flight Audit Summary
print('[AUDIT] Pre-flight Secrets Status:')
print(f"  - DOPPLER_TOKEN: {'✅ Configured (1st Priority Active)' if os.getenv('DOPPLER_TOKEN') else 'ℹ️ Not set'}")
print(f"  - HF_TOKEN:      {'✅ Configured' if os.getenv('HF_TOKEN') else '⚠️ Missing (Add to Kaggle Secrets -> HF_TOKEN)'}")
print(f"  - GH_TOKEN:      {'✅ Configured' if (os.getenv('GH_TOKEN') or os.getenv('GITHUB_TOKEN')) else '⚠️ Missing (Add to Kaggle Secrets -> GH_TOKEN)'}")
print(f"  - WANDB_KEY:     {'✅ Configured' if os.getenv('WANDB_KEY') else '⚠️ Missing (Add to Kaggle Secrets -> WANDB_KEY)'}")

# 2. Dynamic Target Pathing & Git Clone/Pull
if current_platform == 'KAGGLE':
    target_dir = '/kaggle/working/HoroConsultant'
elif current_platform == 'COLAB':
    target_dir = '/content/HoroConsultant'
else:
    target_dir = os.path.abspath(os.path.join(os.getcwd(), 'HoroConsultant')) if not os.path.exists('scripts/cloud_train_orchestrator.py') else os.path.abspath(os.getcwd())

if not os.path.exists(target_dir):
    print('[MODEL] Cloning HoroConsultant repository...')
    subprocess.run(['git', 'clone', 'https://github.com/pphothidaen/HoroConsultant.git', target_dir], check=True)
else:
    print('[SYNC] Resetting and pulling latest updates...')
    subprocess.run(['git', '-C', target_dir, 'fetch', 'origin', 'main'], check=True)
    subprocess.run(['git', '-C', target_dir, 'reset', '--hard', 'origin/main'], check=True)

try:
    head_rev = subprocess.check_output(['git', '-C', target_dir, 'rev-parse', '--short', 'HEAD'], text=True).strip()
    head_msg = subprocess.check_output(['git', '-C', target_dir, 'log', '-1', '--pretty=%B'], text=True).strip().splitlines()[0]
    print(f'[GIT] Cloud Environment Active Commit: {head_rev} ({head_msg})')
except Exception:
    pass

os.chdir(target_dir)
if target_dir not in sys.path:
    sys.path.insert(0, target_dir)

import torch
if torch.cuda.is_available():
    cap = torch.cuda.get_device_capability(0)
    dev_name = torch.cuda.get_device_name(0)
    target_sm = f'sm_{cap[0]}{cap[1]}'
    print(f'[CUDA] Detected GPU: {dev_name} ({target_sm})')

# Global PyTorch Embedding Guard to enforce LongTensor scalar types
try:
    import torch.nn as nn
    import torch.nn.functional as F
    _orig_nn_embedding_forward = nn.Embedding.forward
    def _safe_nn_embedding_forward(self, input):
        if isinstance(input, torch.Tensor) and input.dtype not in (torch.long, torch.int, torch.int32, torch.int64):
            input = input.long()
        return _orig_nn_embedding_forward(self, input)
    nn.Embedding.forward = _safe_nn_embedding_forward

    _orig_f_embedding = F.embedding
    def _safe_f_embedding(input, weight, *args, **kwargs):
        if isinstance(input, torch.Tensor) and input.dtype not in (torch.long, torch.int, torch.int32, torch.int64):
            input = input.long()
        return _orig_f_embedding(input, weight, *args, **kwargs)
    F.embedding = _safe_f_embedding
except Exception:
    pass

try:
    import bitsandbytes as bnb
    from pathlib import Path
    bnb_dir = Path(bnb.__file__).parent
    cuda_ver_str = getattr(torch.version, 'cuda', '') or ''
    cuda_clean = cuda_ver_str.replace('.', '')
    if cuda_clean:
        target_so = bnb_dir / f'libbitsandbytes_cuda{cuda_clean}.so'
        if not target_so.exists():
            available = sorted(list(bnb_dir.glob('libbitsandbytes_cuda*.so')), reverse=True)
            if available:
                try: os.symlink(available[0], target_so)
                except Exception: shutil.copy(available[0], target_so)
                print(f'[OK] BNB CUDA Fix: Symlinked {available[0].name} -> {target_so.name}')
    bnb_ver = getattr(bnb, '__version__', 'unknown')
except Exception as bnb_e:
    bnb_ver = f'bypassed ({bnb_e})'

import docx, gdown
import transformers, peft, trl, datasets, accelerate
print(f'[OK] Fail-Fast Import Verified: transformers={transformers.__version__}, peft={peft.__version__}, trl={trl.__version__}, accelerate={accelerate.__version__}, datasets={datasets.__version__}, bitsandbytes={bnb_ver}')

# 4. Google Drive Dataset Ingestion & Deduplication
print('[INFO] กำลังดาวน์โหลด Dataset จาก Google Drive...')
gdrive_url = 'https://drive.google.com/drive/folders/1e8nX-h3cKpcifUv6G2EjuJDey9DBm5b2'
if current_platform == 'KAGGLE':
    gdrive_data_dir = '/kaggle/working/my_dataset'
elif current_platform == 'COLAB':
    gdrive_data_dir = '/content/my_dataset'
else:
    gdrive_data_dir = os.path.join(target_dir, 'my_dataset')

os.makedirs(gdrive_data_dir, exist_ok=True)
try:
    gdown.download_folder(gdrive_url, output=gdrive_data_dir, quiet=False, use_cookies=False)
except Exception as gdown_err:
    print(f'[WARNING] Google Drive download note: {gdown_err}')

local_dataset_target = os.path.join(target_dir, 'project/rag/datasets/train.jsonl')
os.makedirs(os.path.dirname(local_dataset_target), exist_ok=True)

valid_total_lines = 0
seen_data = set()
print('[INFO] กำลังตรวจสอบ รวบรวม และคัดกรองข้อมูลซ้ำจากไฟล์ทั้งหมด...')

if os.path.exists(local_dataset_target):
    try:
        with open(local_dataset_target, 'r', encoding='utf-8') as f_ex:
            for line in f_ex:
                s = line.strip()
                if s: seen_data.add(s)
    except Exception:
        pass

with open(local_dataset_target, 'w', encoding='utf-8') as f_out:
    for item in seen_data:
        f_out.write(item + '\\n')
        valid_total_lines += 1

    if os.path.exists(gdrive_data_dir):
        downloaded_files = glob.glob(os.path.join(gdrive_data_dir, '**/*.*'), recursive=True)
        for fpath in downloaded_files:
            file_ext = fpath.lower()
            valid_file_lines = 0
            duplicate_lines = 0
            
            if file_ext.endswith('.jsonl') or file_ext.endswith('.json') or file_ext.endswith('.docx'):
                print(f'[PROCESS] กำลังประมวลผลไฟล์: {os.path.basename(fpath)}')
                if zipfile.is_zipfile(fpath) or file_ext.endswith('.docx'):
                    try:
                        doc = docx.Document(fpath)
                        for para in doc.paragraphs:
                            text = para.text.strip()
                            if text:
                                text = text.replace('“', '"').replace('”', '"').replace('‘', "'").replace('’', "'")
                                try:
                                    json.loads(text)
                                    if text not in seen_data:
                                        seen_data.add(text)
                                        f_out.write(text + '\\n')
                                        valid_file_lines += 1
                                    else:
                                        duplicate_lines += 1
                                except json.JSONDecodeError: pass
                        print(f'  -> [OK] ได้ข้อมูลใหม่ {valid_file_lines} บรรทัด (ตัดข้อมูลซ้ำออก {duplicate_lines} บรรทัด)')
                    except Exception as e:
                        print(f'  -> [ERROR] สกัดข้อมูลล้มเหลว: {e}')
                else:
                    try:
                        with open(fpath, 'r', encoding='utf-8') as f_in:
                            for line in f_in:
                                text = line.strip()
                                if text:
                                    try:
                                        json.loads(text)
                                        if text not in seen_data:
                                            seen_data.add(text)
                                            f_out.write(text + '\\n')
                                            valid_file_lines += 1
                                        else:
                                            duplicate_lines += 1
                                    except json.JSONDecodeError: pass
                        print(f'  -> [OK] ได้ข้อมูลใหม่ {valid_file_lines} บรรทัด (ตัดข้อมูลซ้ำออก {duplicate_lines} บรรทัด)')
                    except Exception as e:
                        print(f'  -> [ERROR] อ่านไฟล์ล้มเหลว: {e}')
                valid_total_lines += valid_file_lines

    # Ingest Kaggle Mounted Datasets (/kaggle/input/**)
    kaggle_input_dir = '/kaggle/input'
    if os.path.exists(kaggle_input_dir):
        print('[KAGGLE INPUT] ค้นหาและรวบรวมไฟล์จาก Kaggle Input Datasets (bazi-huggingface-curated, horoconsultant-distilled-dataset, horoconsultant-classical-treatises-pdf)...')
        k_files = glob.glob(os.path.join(kaggle_input_dir, '**/*.*'), recursive=True)
        for kpath in k_files:
            kext = kpath.lower()
            if kext.endswith('.jsonl') or kext.endswith('.json'):
                k_valid = 0
                try:
                    with open(kpath, 'r', encoding='utf-8', errors='replace') as k_in:
                        for line in k_in:
                            ktext = line.strip()
                            if ktext:
                                try:
                                    json.loads(ktext)
                                    if ktext not in seen_data:
                                        seen_data.add(ktext)
                                        f_out.write(ktext + '\\n')
                                        k_valid += 1
                                except Exception: pass
                    if k_valid > 0:
                        print(f'  -> [OK] Ingested {k_valid} samples from Kaggle dataset: {os.path.basename(kpath)}')
                        valid_total_lines += k_valid
                except Exception as k_err:
                    print(f'  -> [WARNING] Note reading {kpath}: {k_err}')

    # Hybrid Data Enrichment: If dataset count is low (< 50), ingest curated repository corpus
    internal_sources = [
        os.path.join(target_dir, 'project/data/bazi_hf_curated_corpus.jsonl'),
        os.path.join(target_dir, 'project/rag/datasets/combined_train.jsonl'),
        os.path.join(target_dir, 'project/data/finetune_bazi_qwen25_chatml.jsonl')
    ]
    for isrc in internal_sources:
        if os.path.exists(isrc):
            try:
                added_isrc = 0
                with open(isrc, 'r', encoding='utf-8', errors='replace') as f_isrc:
                    for line in f_isrc:
                        text = line.strip()
                        if text:
                            try:
                                json.loads(text)
                                if text not in seen_data:
                                    seen_data.add(text)
                                    f_out.write(text + '\\n')
                                    added_isrc += 1
                            except json.JSONDecodeError: pass
                if added_isrc > 0:
                    print(f'  -> [OK] Ingested {added_isrc} records from internal {os.path.basename(isrc)}')
                    valid_total_lines += added_isrc
            except Exception as isrc_err:
                print(f'  -> [WARNING] Note reading {isrc}: {isrc_err}')

print(f'[OK] รวบรวม Dataset สำเร็จ! มีข้อมูลที่ไม่ซ้ำกันพร้อมเทรนรวมทั้งสิ้น {valid_total_lines} บรรทัด')

# 5. Run Cloud Training Orchestrator with Execution Logging
print('[START] Launching Cloud Training Orchestrator สำหรับการเทรนต่อเนื่อง...')
if current_platform == 'KAGGLE':
    log_path = '/kaggle/working/train_execution.log'
elif current_platform == 'COLAB':
    log_path = '/content/train_execution.log'
else:
    log_path = os.path.join(target_dir, 'train_execution.log')

train_env = os.environ.copy()
train_env['PYTHONIOENCODING'] = 'utf-8'
train_env['PYTHONUTF8'] = '1'

dataset_cmd_path = None

train_cmd = [
    sys.executable,
    'scripts/cloud_train_orchestrator.py',
    '--platform', current_platform,
    '--base-model', 'pphothidaen/qwen2.5-7b-bazi-instruct-4bit',
    '--hf-repo', 'pphothidaen/qwen2.5-7b-bazi-instruct-4bit',
    '--dataset-path', local_dataset_target,
    '--epochs', '3',
]

if 'HITL_EXPORT_PATH' in os.environ:
    train_cmd.extend(['--dataset-path', os.environ['HITL_EXPORT_PATH']])
elif dataset_cmd_path:
    train_cmd.extend(['--dataset-path', dataset_cmd_path])

proc = subprocess.Popen(
    train_cmd,
    stdout=subprocess.PIPE,
    stderr=subprocess.STDOUT,
    text=True,
    errors='replace',
    env=train_env
)

with open(log_path, 'w', encoding='utf-8', errors='replace') as log_f:
    for line in iter(proc.stdout.readline, ''):
        safe_line = line.encode('utf-8', errors='replace').decode('utf-8', errors='replace')
        sys.stdout.write(safe_line)
        sys.stdout.flush()
        log_f.write(safe_line)

proc.wait()

if proc.returncode != 0:
    log_tail = ''
    if os.path.exists(log_path):
        try:
            with open(log_path, 'r', encoding='utf-8') as f:
                log_tail = ''.join(f.readlines()[-30:])
        except Exception:
            pass
    raise RuntimeError(f'[ERROR] Training orchestrator failed (exit code {proc.returncode}).\\n--- Tail of train_execution.log ---\\n{log_tail}')

print('[OK] Training pipeline completed successfully! โมเดลถูกอัปโหลดขึ้น Hugging Face เรียบร้อยแล้ว!')
"""

def to_notebook_lines(code_str: str):
    return [line + '\n' for line in code_str.splitlines()]

def main():
    # 1. Strict syntax check of Python code
    compile(cell1_source, '<cell_1>', 'exec')
    compile(cell2_source, '<cell_2>', 'exec')
    print('[OK] Python syntax validation compiled successfully for both cells!')

    c1_lines = to_notebook_lines(cell1_source)
    c2_lines = to_notebook_lines(cell2_source)

    targets = [
        Path('horoconsultant-finetune-pipeline.ipynb'),
        Path('project/kaggle_kernel/notebook.ipynb')
    ]

    for p in targets:
        if not p.exists():
            continue
        with open(p, 'r', encoding='utf-8') as f:
            nb = json.load(f)

        nb['cells'] = [
            {
                'cell_type': 'code',
                'execution_count': None,
                'metadata': {},
                'outputs': [],
                'source': c1_lines
            },
            {
                'cell_type': 'code',
                'execution_count': None,
                'metadata': {},
                'outputs': [],
                'source': c2_lines
            }
        ]

        with open(p, 'w', encoding='utf-8') as f:
            json.dump(nb, f, indent=2, ensure_ascii=False)
            f.write('\n')
        print(f'[OK] Synchronized and validated {p}')

if __name__ == '__main__':
    main()
