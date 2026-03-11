import re
import streamlit as st
import pandas as pd
from validator_core import EmailValidator
import io
import time
import concurrent.futures

st.set_page_config(page_title="Email Validator", page_icon="✉️", layout="wide")

st.markdown("""
<style>

* { box-sizing: border-box; }

html, body, [data-testid="stAppViewContainer"], .main, .stApp {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "Helvetica Neue", Arial, sans-serif !important;
    background-color: #f5f6ff !important;
    color: #1e1b4b !important;
}

.main .block-container {
    max-width: 1020px !important;
    padding: 0 2rem 4rem !important;
    margin: 0 auto;
}

#MainMenu, footer, header, [data-testid="stToolbar"] { display: none !important; }

/* ════════════════════════════
   TOP BANNER
════════════════════════════ */
.top-banner {
    background: linear-gradient(135deg, #4f46e5 0%, #7c3aed 55%, #a855f7 100%);
    margin: 0 -2rem 2.5rem;
    padding: 2.2rem 2.5rem 2rem;
    position: relative;
    overflow: hidden;
}
.top-banner::before {
    content: '';
    position: absolute;
    top: -50px; right: -30px;
    width: 220px; height: 220px;
    background: rgba(255,255,255,0.07);
    border-radius: 50%;
}
.top-banner::after {
    content: '';
    position: absolute;
    bottom: -70px; left: 35%;
    width: 300px; height: 300px;
    background: rgba(255,255,255,0.04);
    border-radius: 50%;
}
.banner-badge {
    display: inline-flex;
    align-items: center;
    gap: 0.4rem;
    background: rgba(255,255,255,0.18);
    border: 1px solid rgba(255,255,255,0.3);
    border-radius: 20px;
    padding: 0.28rem 0.85rem;
    font-size: 0.72rem;
    font-weight: 700;
    color: #ffffff !important;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    margin-bottom: 0.9rem;
    width: fit-content;
}
.banner-title {
    font-size: 2rem;
    font-weight: 800;
    color: #ffffff !important;
    letter-spacing: -0.03em;
    margin-bottom: 0.4rem;
    line-height: 1.1;
}
.banner-subtitle {
    font-size: 0.9rem;
    color: rgba(255,255,255,0.82) !important;
    font-weight: 400;
}

/* ════════════════════════════
   TABS
════════════════════════════ */
[data-baseweb="tab-list"] {
    background: transparent !important;
    border-bottom: 2px solid #e0e7ff !important;
    gap: 0 !important;
    margin-bottom: 2rem;
}
[data-baseweb="tab"] {
    font-size: 0.85rem !important;
    font-weight: 600 !important;
    color: #9ca3af !important;
    background: transparent !important;
    border: none !important;
    border-bottom: 2px solid transparent !important;
    padding: 0.85rem 1.5rem !important;
    margin-bottom: -2px !important;
}
[aria-selected="true"][data-baseweb="tab"] {
    color: #4f46e5 !important;
    border-bottom: 2px solid #4f46e5 !important;
}
[data-baseweb="tab-highlight"],
[data-baseweb="tab-border"] { display: none !important; }

/* ════════════════════════════
   FORM LABELS
════════════════════════════ */
[data-testid="stTextInput"] label,
[data-testid="stTextInput"] label p,
[data-testid="stSelectbox"] label,
[data-testid="stSelectbox"] label p,
[data-testid="stFileUploader"] label,
[data-testid="stFileUploader"] label p {
    font-size: 0.72rem !important;
    font-weight: 700 !important;
    color: #4f46e5 !important;
    text-transform: uppercase !important;
    letter-spacing: 0.09em !important;
}

/* ════════════════════════════
   TEXT INPUT
════════════════════════════ */
[data-testid="stTextInput"] input {
    background-color: #ffffff !important;
    border: 2px solid #e0e7ff !important;
    border-radius: 8px !important;
    color: #1e1b4b !important;
    font-size: 0.92rem !important;
    font-weight: 500 !important;
    padding: 0.72rem 1rem !important;
    box-shadow: 0 1px 4px rgba(99,102,241,0.08) !important;
}
[data-testid="stTextInput"] input:focus {
    border-color: #6366f1 !important;
    box-shadow: 0 0 0 3px rgba(99,102,241,0.15) !important;
}
[data-testid="stTextInput"] input::placeholder { color: #c7d2fe !important; }

/* ════════════════════════════
   SELECTBOX
════════════════════════════ */
[data-testid="stSelectbox"] > div > div {
    background-color: #ffffff !important;
    border: 2px solid #e0e7ff !important;
    border-radius: 8px !important;
    color: #1e1b4b !important;
    font-size: 0.92rem !important;
    font-weight: 500 !important;
    box-shadow: 0 1px 4px rgba(99,102,241,0.08) !important;
}
[data-testid="stSelectbox"] [data-baseweb="select"] span,
[data-testid="stSelectbox"] [data-baseweb="select"] div {
    color: #1e1b4b !important;
    background-color: transparent !important;
}

/* Dropdown popover */
[data-baseweb="popover"],
[data-baseweb="popover"] > div,
[role="listbox"],
[role="listbox"] > div,
ul[data-baseweb="menu"],
ul[data-baseweb="menu"] li {
    background-color: #ffffff !important;
    border: 1.5px solid #e0e7ff !important;
    border-radius: 8px !important;
    box-shadow: 0 8px 24px rgba(99,102,241,0.15) !important;
}
[role="option"],
li[role="option"],
[data-baseweb="menu-item"],
[data-baseweb="menu"] li {
    background-color: #ffffff !important;
    color: #1e1b4b !important;
    font-size: 0.88rem !important;
    font-weight: 500 !important;
    padding: 0.55rem 1rem !important;
}
[role="option"]:hover,
li[role="option"]:hover,
[data-baseweb="menu-item"]:hover {
    background-color: #eef2ff !important;
    color: #4f46e5 !important;
}
[aria-selected="true"][role="option"],
[data-highlighted][role="option"] {
    background-color: #e0e7ff !important;
    color: #4f46e5 !important;
    font-weight: 600 !important;
}

/* ════════════════════════════
   FILE UPLOADER
════════════════════════════ */
[data-testid="stFileUploader"] {
    background: #ffffff !important;
    border: 2px dashed #a5b4fc !important;
    border-radius: 12px !important;
    padding: 0 !important;
    overflow: hidden !important;
}
[data-testid="stFileUploaderDropzone"] {
    background: linear-gradient(135deg, #eef2ff 0%, #f5f3ff 100%) !important;
    border: none !important;
    border-radius: 10px !important;
    padding: 1.75rem 1.5rem !important;
    text-align: center !important;
}
[data-testid="stFileUploaderDropzoneInstructions"] > div > span {
    font-size: 1rem !important;
    font-weight: 700 !important;
    color: #4f46e5 !important;
}
[data-testid="stFileUploaderDropzoneInstructions"] > div > small {
    font-size: 0.78rem !important;
    color: #818cf8 !important;
    font-weight: 500 !important;
}
[data-testid="stFileUploaderDropzone"] button {
    background: linear-gradient(135deg, #4f46e5, #7c3aed) !important;
    color: #ffffff !important;
    -webkit-text-fill-color: #ffffff !important;
    border: none !important;
    border-radius: 8px !important;
    font-size: 0.82rem !important;
    font-weight: 700 !important;
    padding: 0.55rem 1.4rem !important;
    box-shadow: 0 4px 12px rgba(99,102,241,0.35) !important;
    width: auto !important;
}
[data-testid="stFileUploaderDropzone"] button:hover {
    background: linear-gradient(135deg, #4338ca, #6d28d9) !important;
}
[data-testid="stFileUploaderFile"] {
    background: #eef2ff !important;
    border: 1.5px solid #c7d2fe !important;
    border-radius: 8px !important;
    padding: 0.5rem 0.9rem !important;
    margin: 0.5rem !important;
}
[data-testid="stFileUploaderFileName"] {
    font-size: 0.85rem !important;
    font-weight: 600 !important;
    color: #4f46e5 !important;
}
[data-testid="stFileUploaderFileSize"] {
    font-size: 0.75rem !important;
    color: #818cf8 !important;
}

/* ════════════════════════════
   BUTTONS — compact, white text
════════════════════════════ */
[data-testid="stButton"] > button {
    background: linear-gradient(135deg, #4f46e5, #7c3aed) !important;
    color: #ffffff !important;
    -webkit-text-fill-color: #ffffff !important;
    border: none !important;
    border-radius: 8px !important;
    font-size: 0.88rem !important;
    font-weight: 700 !important;
    letter-spacing: 0.02em !important;
    /* Key fix: auto width, consistent padding, no stretching */
    display: inline-flex !important;
    align-items: center !important;
    justify-content: center !important;
    width: auto !important;
    min-width: 140px !important;
    max-width: 220px !important;
    padding: 0.65rem 1.6rem !important;
    height: 2.75rem !important;
    box-shadow: 0 4px 14px rgba(99,102,241,0.35) !important;
    white-space: nowrap !important;
}
[data-testid="stButton"] > button:hover {
    background: linear-gradient(135deg, #4338ca, #6d28d9) !important;
    color: #ffffff !important;
    -webkit-text-fill-color: #ffffff !important;
}
/* Inner text nodes */
[data-testid="stButton"] > button p,
[data-testid="stButton"] > button span,
[data-testid="stButton"] > button div {
    color: #ffffff !important;
    -webkit-text-fill-color: #ffffff !important;
    font-weight: 700 !important;
}

/* ════════════════════════════
   DOWNLOAD BUTTONS — compact, white text
════════════════════════════ */
[data-testid="stDownloadButton"] > button {
    background: linear-gradient(135deg, #059669, #0d9488) !important;
    color: #ffffff !important;
    -webkit-text-fill-color: #ffffff !important;
    border: none !important;
    border-radius: 8px !important;
    font-size: 0.88rem !important;
    font-weight: 700 !important;
    display: inline-flex !important;
    align-items: center !important;
    justify-content: center !important;
    width: auto !important;
    min-width: 180px !important;
    max-width: 280px !important;
    padding: 0.65rem 1.6rem !important;
    height: 2.75rem !important;
    box-shadow: 0 4px 14px rgba(5,150,105,0.3) !important;
    white-space: nowrap !important;
}
[data-testid="stDownloadButton"] > button:hover {
    background: linear-gradient(135deg, #047857, #0f766e) !important;
    color: #ffffff !important;
    -webkit-text-fill-color: #ffffff !important;
}
[data-testid="stDownloadButton"] > button p,
[data-testid="stDownloadButton"] > button span,
[data-testid="stDownloadButton"] > button div {
    color: #ffffff !important;
    -webkit-text-fill-color: #ffffff !important;
    font-weight: 700 !important;
}

/* ════════════════════════════
   PROGRESS BAR
════════════════════════════ */
[data-testid="stProgressBar"] > div {
    background-color: #e0e7ff !important;
    border-radius: 6px !important;
    height: 10px !important;
}
[data-testid="stProgressBar"] > div > div {
    background: linear-gradient(90deg, #4f46e5, #7c3aed, #a855f7) !important;
    border-radius: 6px !important;
    height: 10px !important;
}

/* ════════════════════════════
   PROGRESS TEXT
════════════════════════════ */
.progress-text {
    font-size: 1.05rem !important;
    font-weight: 700 !important;
    color: #4f46e5 !important;
    margin-top: 0.5rem;
    letter-spacing: 0.01em;
}

/* ════════════════════════════
   RESULT CARD
════════════════════════════ */
.result-card {
    background: #ffffff;
    border: 2px solid #e0e7ff;
    border-radius: 12px;
    padding: 1.6rem 1.8rem;
    margin-top: 1.25rem;
    box-shadow: 0 4px 20px rgba(99,102,241,0.09);
}
.result-card.delivery   { border-left: 6px solid #10b981; }
.result-card.undelivery { border-left: 6px solid #ef4444; }
.result-card.risky      { border-left: 6px solid #f59e0b; }

.result-grid {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 1.25rem;
    margin-bottom: 1.25rem;
}
.r-label {
    font-size: 0.68rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.1em;
    color: #6366f1;
    margin-bottom: 0.35rem;
}
.r-value {
    font-size: 1rem;
    font-weight: 700;
    color: #1e1b4b;
}
.card-divider { border: none; border-top: 2px solid #e0e7ff; margin: 0 0 1rem; }

.badge-row { display: flex; gap: 0.5rem; flex-wrap: wrap; }
.badge {
    display: inline-flex;
    align-items: center;
    gap: 0.3rem;
    border-radius: 6px;
    font-size: 0.75rem;
    font-weight: 700;
    padding: 0.32rem 0.7rem;
    border: 1.5px solid;
}
.badge.ok   { color: #059669; border-color: #a7f3d0; background: #ecfdf5; }
.badge.warn { color: #d97706; border-color: #fcd34d; background: #fffbeb; }
.badge.bad  { color: #dc2626; border-color: #fca5a5; background: #fef2f2; }

/* ════════════════════════════
   METRIC CARDS
════════════════════════════ */
[data-testid="stMetric"] {
    background: #ffffff !important;
    border: 2px solid #e0e7ff !important;
    border-radius: 10px !important;
    padding: 1.1rem 1.3rem !important;
    box-shadow: 0 2px 10px rgba(99,102,241,0.08) !important;
}
[data-testid="stMetricLabel"] p {
    font-size: 0.72rem !important;
    font-weight: 700 !important;
    text-transform: uppercase !important;
    letter-spacing: 0.08em !important;
    color: #6366f1 !important;
}
[data-testid="stMetricValue"] {
    font-size: 1.6rem !important;
    font-weight: 800 !important;
    color: #1e1b4b !important;
}
[data-testid="column"]:nth-child(1) [data-testid="stMetric"] { border-top: 4px solid #6366f1 !important; }
[data-testid="column"]:nth-child(2) [data-testid="stMetric"] { border-top: 4px solid #10b981 !important; }
[data-testid="column"]:nth-child(3) [data-testid="stMetric"] { border-top: 4px solid #ef4444 !important; }
[data-testid="column"]:nth-child(4) [data-testid="stMetric"] { border-top: 4px solid #f59e0b !important; }

/* ════════════════════════════
   ALERTS
════════════════════════════ */
[data-testid="stAlert"] {
    border-radius: 8px !important;
    font-size: 0.88rem !important;
    font-weight: 600 !important;
}

/* ════════════════════════════
   DATAFRAME
════════════════════════════ */
[data-testid="stDataFrame"] {
    border: 2px solid #e0e7ff !important;
    border-radius: 10px !important;
    overflow: hidden !important;
    box-shadow: 0 2px 10px rgba(99,102,241,0.07) !important;
}

/* ════════════════════════════
   FOOTER
════════════════════════════ */
.app-footer {
    margin-top: 3rem;
    padding-top: 1.25rem;
    border-top: 2px solid #c7d2fe;
    font-size: 0.82rem;
    color: #4f46e5 !important;
    text-align: center;
    font-weight: 700;
    letter-spacing: 0.06em;
    text-transform: uppercase;
}
</style>
""", unsafe_allow_html=True)

# ── Banner ───────────────────────────────────────────────────────────────────
st.markdown("""
<div class="top-banner">
    <div class="banner-badge">✉ Email Intelligence</div>
    <div class="banner-title">Email Validator</div>
    <div class="banner-subtitle">Verify single or bulk email addresses for deliverability in seconds</div>
</div>
""", unsafe_allow_html=True)

validator = EmailValidator()

tab1, tab2 = st.tabs(["Single Validation", "Bulk Validation"])

# ═══════════════════════════
# TAB 1 — Single
# ═══════════════════════════
with tab1:
    # Email input full width, button in a tight column beside it
    col_input, col_btn = st.columns([5, 1], vertical_alignment="bottom")
    with col_input:
        email_input = st.text_input("Email Address", placeholder="you@example.com")
    with col_btn:
        verify_btn = st.button("Verify Email", key="single_verify")

    if verify_btn:
        if email_input.strip():
            with st.spinner("Checking…"):
                result = validator.validate(email_input.strip())

            cls        = result["classification"].lower()
            status     = result["status"]
            card_class = cls if cls in ("delivery", "undelivery") else "risky"

            s_badge = '<span class="badge ok">✓ Syntax Valid</span>'   if result["is_syntax_valid"] else '<span class="badge bad">✗ Syntax Invalid</span>'
            d_badge = '<span class="badge warn">⚠ Disposable</span>'   if result["is_disposable"]   else '<span class="badge ok">✓ Not Disposable</span>'
            r_badge = '<span class="badge warn">⚠ Role-Based</span>'   if result["is_role_based"]   else '<span class="badge ok">✓ Not Role-Based</span>'

            st.markdown(f"""
            <div class="result-card {card_class}">
                <div class="result-grid">
                    <div>
                        <div class="r-label">Classification</div>
                        <div class="r-value">{result['classification']}</div>
                    </div>
                    <div>
                        <div class="r-label">Status Code</div>
                        <div class="r-value">{status}</div>
                    </div>
                    <div>
                        <div class="r-label">Domain</div>
                        <div class="r-value">{result.get('domain', '—')}</div>
                    </div>
                    <div>
                        <div class="r-label">Provider</div>
                        <div class="r-value">{result.get('provider', '—')}</div>
                    </div>
                </div>
                <hr class="card-divider">
                <div class="badge-row">{s_badge}{d_badge}{r_badge}</div>
            </div>
            """, unsafe_allow_html=True)

            if status == "providerProtected":
                st.info("Provider Protected — Port 25 is likely blocked. The address probably exists but cannot be fully confirmed.")
        else:
            st.error("Please enter an email address.")

# ═══════════════════════════
# TAB 2 — Bulk
# ═══════════════════════════
with tab2:
    uploaded_file = st.file_uploader("Upload CSV or Excel File", type=["csv", "xlsx", "xls"])

    if "processed_df" not in st.session_state:
        st.session_state.processed_df = None

    if uploaded_file:
        try:
            if uploaded_file.name.endswith(".csv"):
                df = pd.read_csv(uploaded_file)
                st.success(f"Loaded {len(df):,} rows from CSV.")
            else:
                xl = pd.ExcelFile(uploaded_file)
                sheet_names = xl.sheet_names
                if len(sheet_names) > 1:
                    selected_sheet = st.selectbox("Select Sheet", options=sheet_names)
                    df = pd.read_excel(uploaded_file, sheet_name=selected_sheet)
                else:
                    df = pd.read_excel(uploaded_file)
                    selected_sheet = sheet_names[0] if sheet_names else "Sheet1"
                st.success(f"Loaded {len(df):,} rows from Excel.")

            email_col = st.selectbox("Email Column", options=df.columns.tolist())

            # --- State Initialization ---
            sheet_name = selected_sheet if 'selected_sheet' in locals() else "default"
            file_id = f"{uploaded_file.name}_{uploaded_file.size}_{sheet_name}"
            
            if ("results_data" not in st.session_state or 
                st.session_state.get("last_file_id") != file_id or 
                st.session_state.get("last_email_col") != email_col):
                
                st.session_state.results_data = {
                    "classification": [None] * len(df),
                    "status": [None] * len(df),
                    "domain": [None] * len(df),
                    "provider": [None] * len(df)
                }
                st.session_state.last_file_id = file_id
                st.session_state.last_email_col = email_col
                st.session_state.processed_df = None

            # Button row: Run and Reset
            btn_col1, btn_col2, _ = st.columns([2, 1.5, 3.5])
            with btn_col1:
                run_btn = st.button("▶  Run Validation", key="bulk_verify")
            with btn_col2:
                if st.button("🔄 Reset Progress", key="reset_progress"):
                    st.session_state.results_data = {
                        "classification": [None] * len(df),
                        "status": [None] * len(df),
                        "domain": [None] * len(df),
                        "provider": [None] * len(df)
                    }
                    st.session_state.processed_df = None
                    st.rerun()

            if run_btn:
                email_tasks = []
                for i, row in df.iterrows():
                    # Check if already processed and NOT an error that should be retried
                    current_status = st.session_state.results_data["status"][i]
                    if st.session_state.results_data["classification"][i] is not None:
                        # Retry for DNS errors and various SMTP connection issues
                        if current_status not in ["DnsError", "smtpError", "smtpConnectionTimeout"]:
                            continue
                        
                    val = str(row[email_col]).strip()
                    # Handle empty, NaN, or placeholder 'nan'
                    if not val or val.lower() == "nan":
                        emails = []
                    else:
                        emails = [e.strip() for e in re.split(r'[,;]', val) if e.strip()]
                    email_tasks.append((i, emails))

                total_to_process = len(email_tasks)
                total_rows = len(df)
                already_done = total_rows - total_to_process

                if total_to_process == 0:
                    st.info("All addresses in this file have already been validated.")
                else:
                    if already_done > 0:
                        st.info(f"Resuming validation: {already_done:,} rows already completed, {total_to_process:,} remaining.")

                    st.markdown(
                        f'<p style="font-size:0.92rem;font-weight:600;color:#6366f1;margin-bottom:0.5rem;">'
                        f'Processing {total_to_process:,} rows…</p>',
                        unsafe_allow_html=True
                    )

                results_classification = st.session_state.results_data["classification"]
                results_status         = st.session_state.results_data["status"]
                results_domain         = st.session_state.results_data["domain"]
                results_provider       = st.session_state.results_data["provider"]

                def process_row(row_index, emails, original_row):
                    try:
                        classes, statuses, domains, providers = [], [], [], []
                        if not emails:
                            return row_index, "", "", "", ""
                            
                        for email in emails:
                            res    = validator.validate(email)
                            cls    = res["classification"]
                            status = res["status"]
                            domain = res.get("domain", "").lower()
                            prov   = res.get("provider", "Other")
                            if status == "providerProtected" and prov == "outlook":
                                cls = "Risky"
                            classes.append(cls); statuses.append(status)
                            domains.append(domain); providers.append(prov)
                        return row_index, ",".join(classes), ",".join(statuses), ",".join(domains), ",".join(providers)
                    except Exception as e:
                        # Fallback for unexpected row-level errors
                        return row_index, "Error", f"RowError: {str(e)}", "", ""

                start_time = time.time()
                completed = already_done
                chunk_size = 500
                progress_bar = st.progress(completed / total_rows if total_rows > 0 else 0)
                progress_text = st.empty()
                progress_text.markdown(f'<p class="progress-text">Progress: {int((completed/total_rows)*100)}% ({completed:,}/{total_rows:,})</p>', unsafe_allow_html=True)
                
                # Split tasks into chunks to manage memory and responsiveness
                for i in range(0, len(email_tasks), chunk_size):
                    chunk = email_tasks[i:i + chunk_size]
                    # Reduced workers to 15 for better network/CPU stability
                    with concurrent.futures.ThreadPoolExecutor(max_workers=15) as ex:
                        futures = [ex.submit(process_row, idx, emails, df.iloc[idx]) for idx, emails in chunk]
                        for future in concurrent.futures.as_completed(futures):
                            try:
                                idx, cls_s, st_s, dom_s, prov_s = future.result()
                                results_classification[idx] = cls_s
                                results_status[idx]         = st_s
                                results_domain[idx]         = dom_s
                                results_provider[idx]       = prov_s
                                # Perspective state update
                                st.session_state.results_data["classification"][idx] = cls_s
                                st.session_state.results_data["status"][idx] = st_s
                                st.session_state.results_data["domain"][idx] = dom_s
                                st.session_state.results_data["provider"][idx] = prov_s
                            except Exception:
                                pass # Individual task failure handled inside process_row
                                
                            completed += 1
                            # Throttle UI updates to every 50 rows (or at the end) to stabilize WebSocket connection
                            if completed % 50 == 0 or completed == total_rows:
                                pct = completed / total_rows
                                progress_bar.progress(pct)
                                progress_text.markdown(
                                    f'<p class="progress-text">{int(pct*100)}% &nbsp;—&nbsp; {completed:,} / {total_rows:,} rows</p>',
                                    unsafe_allow_html=True
                                )
                    # Small break between chunks to allow UI to breathe
                    time.sleep(0.1)

                df["domain"]         = st.session_state.results_data["domain"]
                df["domainprovider"] = st.session_state.results_data["provider"]
                df["classification"] = st.session_state.results_data["classification"]
                df["status code"]    = st.session_state.results_data["status"]
                
                progress_text.empty()
                st.success(f"Done — {total_rows:,} rows validated in {int(time.time() - start_time)}s.")
                st.session_state.processed_df = df

            if st.session_state.processed_df is not None:
                df = st.session_state.processed_df
            elif "results_data" in st.session_state and any(x is not None for x in st.session_state.results_data["classification"]):
                # Construct DF from partial results in state
                df = df.copy() # Avoid modifying original in case of partial refresh
                df["domain"]         = st.session_state.results_data["domain"]
                df["domainprovider"] = st.session_state.results_data["provider"]
                df["classification"] = st.session_state.results_data["classification"]
                df["status code"]    = st.session_state.results_data["status"]
                # Filter out rows that are not processed yet if showing partial results
                df = df.dropna(subset=["classification"])
            else:
                df = None

            if df is not None:

                all_classes = []
                for v in df["classification"].dropna():
                    all_classes.extend([c.strip() for c in str(v).split(",")])
                total         = len(all_classes)
                deliverable   = all_classes.count("delivery")
                undeliverable = all_classes.count("undelivery")
                risky         = total - deliverable - undeliverable

                st.markdown("<div style='margin-top:1.5rem'></div>", unsafe_allow_html=True)
                m1, m2, m3, m4 = st.columns(4)
                m1.metric("Total Addresses", f"{total:,}")
                m2.metric("Deliverable",     f"{deliverable:,}")
                m3.metric("Undeliverable",   f"{undeliverable:,}")
                m4.metric("Risky / Review",  f"{risky:,}")

                st.markdown("<div style='margin-top:1.25rem'></div>", unsafe_allow_html=True)
                st.dataframe(df, use_container_width=True, height=300)

                def get_filtered_df(source_df, col, filter_fn):
                    rows = []
                    for _, row in source_df.iterrows():
                        emails   = [e.strip() for e in re.split(r'[,;]', str(row[col])) if e.strip()]
                        # Explicitly strip whitespace from each class and status
                        classes  = [c.strip() for c in str(row["classification"]).split(",") if c.strip()]
                        statuses = [s.strip() for s in str(row["status code"]).split(",") if s.strip()]
                        
                        matches  = [i for i in range(len(emails)) if i < len(classes) and i < len(statuses) and filter_fn(classes[i], statuses[i])]
                        if matches:
                            nr = row.copy()
                            nr[col]              = ",".join(emails[i]  for i in matches)
                            nr["classification"] = ",".join(classes[i] for i in matches)
                            nr["status code"]    = ",".join(statuses[i] for i in matches)
                            if "domain" in nr:
                                doms = [d.strip() for d in str(nr["domain"]).split(",") if d.strip()]
                                nr["domain"] = ",".join(doms[i] for i in matches if i < len(doms))
                            if "domainprovider" in nr:
                                provs = [p.strip() for p in str(nr["domainprovider"]).split(",") if p.strip()]
                                nr["domainprovider"] = ",".join(provs[i] for i in matches if i < len(provs))
                            rows.append(nr)
                    return pd.DataFrame(rows) if rows else pd.DataFrame(columns=source_df.columns)

                output = io.BytesIO()
                with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
                    df.to_excel(writer, index=False, sheet_name="All_Data")
                    get_filtered_df(df, email_col, lambda c, s: c == "delivery").to_excel(writer, index=False, sheet_name="Delivery")
                    get_filtered_df(df, email_col, lambda c, s: c == "undelivery").to_excel(writer, index=False, sheet_name="Undelivery")
                    get_filtered_df(df, email_col, lambda c, s: c == "Risky" and s == "providerProtected").to_excel(writer, index=False, sheet_name="Risky_Protected")
                    get_filtered_df(df, email_col, lambda c, s: c == "Risky" and s == "catchAllCharacterized").to_excel(writer, index=False, sheet_name="Catch_All")

                # Download buttons in narrow columns
                st.markdown("<div style='margin-top:1.5rem'><b>Export Settings</b></div>", unsafe_allow_html=True)
                
                # Column selection for Clean Export
                available_cols = df.columns.tolist()
                default_cols = [c for c in available_cols if c not in ["domain", "domainprovider", "classification", "status code"]]
                selected_cols = st.multiselect(
                    "Select columns to include in Clean Export",
                    options=available_cols,
                    default=default_cols,
                    key="clean_export_cols"
                )

                dl1, dl2, _ = st.columns([2, 2, 3])
                with dl1:
                    # Regenerate 'output' to ensure it uses the latest 'df' if needed, 
                    # but usually it's already generated above. 
                    # Re-generating to be safe and consistent with potential changes.
                    all_data_output = io.BytesIO()
                    with pd.ExcelWriter(all_data_output, engine="xlsxwriter") as writer:
                        df.to_excel(writer, index=False, sheet_name="All_Data")
                        get_filtered_df(df, email_col, lambda c, s: c == "delivery").to_excel(writer, index=False, sheet_name="Delivery")
                        get_filtered_df(df, email_col, lambda c, s: c == "undelivery").to_excel(writer, index=False, sheet_name="Undelivery")
                        get_filtered_df(df, email_col, lambda c, s: c == "Risky" and s == "providerProtected").to_excel(writer, index=False, sheet_name="Risky_Protected")
                        get_filtered_df(df, email_col, lambda c, s: c == "Risky" and s in ["smtpError","dnsError","smtpConnectionTimeout"]).to_excel(writer, index=False, sheet_name="Retrying_Mails")
                        get_filtered_df(df, email_col, lambda c, s: c == "Risky" and s == "catchAllCharacterized").to_excel(writer, index=False, sheet_name="Catch_All")

                    st.download_button(
                        label="⬇  Export All Results",
                        data=all_data_output.getvalue(),
                        file_name="validated_emails.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        key="export_all_btn"
                    )
                with dl2:
                    # Helper to get cleaned DF (only selected columns)
                    def get_custom_clean_sheets(source_df, email_col, cols):
                        delivery = get_filtered_df(source_df, email_col, lambda c, s: c == "delivery")
                        risky_p  = get_filtered_df(source_df, email_col, lambda c, s: c == "Risky" and s == "providerProtected")
                        catch_all = get_filtered_df(source_df, email_col, lambda c, s: c == "Risky" and s == "catchAllCharacterized")
                        
                        def filter_cols(target_df):
                            if not target_df.empty:
                                return target_df[[c for c in cols if c in target_df.columns]]
                            return pd.DataFrame(columns=cols)

                        return filter_cols(delivery), filter_cols(risky_p), filter_cols(catch_all)

                    d_clean, r_clean, c_clean = get_custom_clean_sheets(df, email_col, selected_cols)
                    
                    output_clean = io.BytesIO()
                    with pd.ExcelWriter(output_clean, engine="xlsxwriter") as writer:
                        # Even if empty, create the sheets if possible or handle gracefully
                        if not d_clean.empty: d_clean.to_excel(writer, index=False, sheet_name="Delivery")
                        else: pd.DataFrame(columns=selected_cols).to_excel(writer, index=False, sheet_name="Delivery")
                        
                        if not r_clean.empty: r_clean.to_excel(writer, index=False, sheet_name="Risky_Protected")
                        else: pd.DataFrame(columns=selected_cols).to_excel(writer, index=False, sheet_name="Risky_Protected")
                        
                        if not c_clean.empty: c_clean.to_excel(writer, index=False, sheet_name="Catch_All")
                        else: pd.DataFrame(columns=selected_cols).to_excel(writer, index=False, sheet_name="Catch_All")
                    
                    st.download_button(
                        label="⬇  Clean Export",
                        data=output_clean.getvalue(),
                        file_name="clean_validated_emails.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        key="export_clean_custom"
                    )

        except Exception as e:
            st.error(f"Error processing file: {e}")

st.markdown(
    '<div class="app-footer">Arrow Thought &nbsp;·&nbsp; Vellore &nbsp;·&nbsp; Software Team</div>',
    unsafe_allow_html=True
)