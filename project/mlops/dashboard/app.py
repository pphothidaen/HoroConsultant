"""
project/mlops/dashboard/app.py
==============================
Streamlit MLOps Monitoring Dashboard & Interactive Operations Console.
Visualizes dataset growth, domain distribution, Kaggle GPU training metrics,
and allows on-demand triggers.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT_DIR))

try:
    import pandas as pd
    import streamlit as st
    STREAMLIT_AVAILABLE = True
except ImportError:
    STREAMLIT_AVAILABLE = False


def main():
    if not STREAMLIT_AVAILABLE:
        print("[ERROR] Streamlit is not installed. Please run: pip install streamlit pandas")
        return

    st.set_page_config(
        page_title="HoroConsultant MLOps Console",
        page_icon="🔮",
        layout="wide"
    )

    st.title("🔮 HoroConsultant: Autonomous Distillation & Fine-Tuning Console")
    st.caption("Grounded Knowledge Mining from Google NotebookLM via Hermes Agent -> Kaggle GPU Fine-Tuning Hub")

    from project.mlops.distillation.curator import DatasetCurator
    from project.mlops.distillation.hermes_miner import MINING_ONTOLOGY, HermesKnowledgeMiner
    from project.mlops.notifications.webhook_notifier import WebhookNotifier
    from project.mlops.training.finetune_orchestrator import FineTuneOrchestrator

    # Sidebar Operations
    st.sidebar.header("🕹️ Pipeline Operations")
    selected_domain = st.sidebar.selectbox("Target Domain", ["all"] + list(MINING_ONTOLOGY.keys()))
    selected_format = st.sidebar.selectbox("Dataset Format", ["chatml", "alpaca", "raw"])
    dry_run_mode = st.sidebar.checkbox("Dry-Run Simulation", value=True)

    if st.sidebar.button("🚀 Trigger Knowledge Mining"):
        with st.spinner(f"Mining domain '{selected_domain}' via Hermes Agent..."):
            miner = HermesKnowledgeMiner()
            curator = DatasetCurator(output_dir=ROOT_DIR / "project" / "data")
            notifier = WebhookNotifier()

            if selected_domain == "all":
                res = miner.mine_all_domains()
                samples = [s for sub in res.values() for s in sub]
            else:
                samples = miner.mine_domain(domain=selected_domain)

            stats = curator.curate_and_export(
                samples=samples,
                dataset_name=f"bazi_distill_{selected_domain}",
                target_format=selected_format
            )
            notifier.notify_distillation_complete(stats)
            st.sidebar.success(f"Mined {stats['final_unique_count']} unique samples!")

    if st.sidebar.button("⚡ Dispatch Kaggle Fine-Tuning"):
        with st.spinner("Dispatching kernel to Kaggle Nvidia T4 GPU..."):
            orchestrator = FineTuneOrchestrator()
            res = orchestrator.trigger_kaggle_training(dry_run=dry_run_mode)
            st.sidebar.info(f"Status: {res.get('status')}")

    # Main Metrics Grid
    col1, col2, col3, col4 = st.columns(4)
    
    data_dir = ROOT_DIR / "project" / "data"
    dataset_files = list(data_dir.glob("*.jsonl")) if data_dir.exists() else []
    total_samples = 0
    for f in dataset_files:
        try:
            total_samples += sum(1 for _ in open(f, encoding="utf-8"))
        except Exception:
            pass

    col1.metric("Target Base Model", "Qwen 2.5 7B BaZi 4-bit")
    col2.metric("Curated Datasets", len(dataset_files))
    col3.metric("Total Training Samples", total_samples)
    col4.metric("Active Domains", len(MINING_ONTOLOGY))

    st.markdown("---")

    # Layout: Datasets Table & Sample Inspector
    tab1, tab2, tab3 = st.tabs(["📊 Curated Datasets", "🔍 Sample Inspector", "⚙️ Kaggle & MLOps Infrastructure"])

    with tab1:
        st.subheader("Generated JSONL Datasets")
        if dataset_files:
            table_data = []
            for f in dataset_files:
                count = sum(1 for _ in open(f, encoding="utf-8"))
                table_data.append({
                    "Filename": f.name,
                    "Size (KB)": round(f.stat().st_size / 1024, 2),
                    "Sample Count": count,
                    "Last Modified": f.stat().st_mtime
                })
            st.dataframe(pd.DataFrame(table_data), use_container_width=True)
        else:
            st.info("No curated datasets found yet. Click 'Trigger Knowledge Mining' in the sidebar.")

    with tab2:
        st.subheader("Interactive Dataset Sample Inspector")
        if dataset_files:
            selected_file = st.selectbox("Select Dataset File", [f.name for f in dataset_files])
            file_path = data_dir / selected_file
            records = [json.loads(line) for line in open(file_path, encoding="utf-8")]
            if records:
                sample_idx = st.slider("Sample Index", 0, len(records) - 1, 0)
                st.json(records[sample_idx])
        else:
            st.info("Please generate a dataset to inspect samples.")

    with tab3:
        st.subheader("MLOps Infrastructure Topology")
        st.markdown(
            """
            * **Knowledge Vault:** Google NotebookLM (Canonical Texts & Treatises)
            * **Extraction Engine:** Hermes Agent with MCP Protocol & Browser Automation
            * **Validation Gate:** Quality Curator with Deterministic PyO3 / Python Consistency Checks
            * **Fine-Tuning Cluster:** Kaggle GPU (Nvidia Tesla T4 - 16GB VRAM)
            * **Hub Target:** `pphothidaen/qwen2.5-7b-bazi-instruct-4bit` on Hugging Face
            * **Notification Channels:** Telegram Bot API / Discord Webhooks
            """
        )


if __name__ == "__main__":
    main()
