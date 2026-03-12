import re
import io
import os
import uuid
import time
import asyncio
import concurrent.futures
from typing import Optional

import pandas as pd
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import StreamingResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from validator_core import EmailValidator

# ─────────────────────────────────────────────
# App setup
# ─────────────────────────────────────────────
app = FastAPI(
    title="Email Validator API",
    description="Verify single or bulk email addresses for deliverability.",
    version="2.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

validator = EmailValidator()

# In-memory store for bulk job results
# key: job_id -> {excel_bytes: bytes}
job_results: dict[str, bytes] = {}


# ─────────────────────────────────────────────
# Models
# ─────────────────────────────────────────────
class SingleValidateRequest(BaseModel):
    email: str


class SingleValidateResponse(BaseModel):
    email: str
    classification: str
    status: str
    is_syntax_valid: bool
    is_disposable: bool
    is_role_based: bool
    domain: str
    provider: str
    mx_records: list
    smtp_log: list


# ─────────────────────────────────────────────
# Health check
# ─────────────────────────────────────────────
@app.get("/health", summary="Health check")
def health():
    return {"status": "ok"}


# ─────────────────────────────────────────────
# Single email validation
# ─────────────────────────────────────────────
@app.post("/validate/single", response_model=SingleValidateResponse, summary="Validate a single email address")
def validate_single(body: SingleValidateRequest):
    email = body.email.strip()
    if not email:
        raise HTTPException(status_code=400, detail="Email address is required.")
    result = validator.validate(email)
    return result


# ─────────────────────────────────────────────
# Bulk validation helpers
# ─────────────────────────────────────────────
def process_row(row_index: int, emails: list[str]) -> tuple:
    """Validate all emails in a single row and return combined results."""
    try:
        classes, statuses, domains, providers = [], [], [], []
        if not emails:
            return row_index, "", "", "", ""

        for email in emails:
            res = validator.validate(email)
            cls = res["classification"]
            status = res["status"]
            domain = res.get("domain", "").lower()
            prov = res.get("provider", "Other")
            # Special case: outlook providerProtected → Risky
            if status == "providerProtected" and prov == "outlook":
                cls = "Risky"
            classes.append(cls)
            statuses.append(status)
            domains.append(domain)
            providers.append(prov)

        return (
            row_index,
            ",".join(classes),
            ",".join(statuses),
            ",".join(domains),
            ",".join(providers),
        )
    except Exception as e:
        return row_index, "Error", f"RowError: {str(e)}", "", ""


def get_filtered_df(source_df: pd.DataFrame, email_col: str, filter_fn) -> pd.DataFrame:
    """Return rows filtered by a classification/status predicate."""
    rows = []
    for _, row in source_df.iterrows():
        emails = [e.strip() for e in re.split(r"[,;]", str(row[email_col])) if e.strip()]
        classes = [c.strip() for c in str(row["classification"]).split(",") if c.strip()]
        statuses = [s.strip() for s in str(row["status code"]).split(",") if s.strip()]
        matches = [
            i
            for i in range(len(emails))
            if i < len(classes) and i < len(statuses) and filter_fn(classes[i], statuses[i])
        ]
        if matches:
            nr = row.copy()
            nr[email_col] = ",".join(emails[i] for i in matches)
            nr["classification"] = ",".join(classes[i] for i in matches)
            nr["status code"] = ",".join(statuses[i] for i in matches)
            if "domain" in nr:
                doms = [d.strip() for d in str(nr["domain"]).split(",") if d.strip()]
                nr["domain"] = ",".join(doms[i] for i in matches if i < len(doms))
            if "domainprovider" in nr:
                provs = [p.strip() for p in str(nr["domainprovider"]).split(",") if p.strip()]
                nr["domainprovider"] = ",".join(provs[i] for i in matches if i < len(provs))
            rows.append(nr)
    return pd.DataFrame(rows) if rows else pd.DataFrame(columns=source_df.columns)


def build_excel(df: pd.DataFrame, email_col: str) -> bytes:
    """Build the multi-sheet Excel file and return as bytes."""
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
        df.to_excel(writer, index=False, sheet_name="All_Data")
        get_filtered_df(df, email_col, lambda c, s: c == "delivery").to_excel(
            writer, index=False, sheet_name="Delivery"
        )
        get_filtered_df(df, email_col, lambda c, s: c == "undelivery").to_excel(
            writer, index=False, sheet_name="Undelivery"
        )
        get_filtered_df(
            df, email_col, lambda c, s: c == "Risky" and s == "providerProtected"
        ).to_excel(writer, index=False, sheet_name="Risky_Protected")
        get_filtered_df(
            df, email_col, lambda c, s: c == "Risky" and s == "catchAllCharacterized"
        ).to_excel(writer, index=False, sheet_name="Catch_All")
    return output.getvalue()


# ─────────────────────────────────────────────
# Bulk validation — SSE streaming endpoint
# ─────────────────────────────────────────────
@app.post("/validate/bulk", summary="Bulk validate emails via file upload (SSE stream)")
async def validate_bulk(
    file: UploadFile = File(...),
    email_col: str = Form(...),
    sheet_name: Optional[str] = Form(None),
):
    """
    Upload a CSV or Excel file and stream validation progress using SSE.

    Each SSE event is a JSON object:
    - `{"type": "start",  "total": N}`
    - `{"type": "progress", "completed": N, "total": N, "pct": 0-100}`
    - `{"type": "done", "job_id": "...", "total": N, "deliverable": N, "undeliverable": N, "risky": N}`
    - `{"type": "error", "message": "..."}`

    After receiving `done`, call `GET /result/{job_id}` to download the Excel file.
    """
    filename = file.filename or ""
    contents = await file.read()

    async def event_generator():
        import json

        def sse(data: dict) -> str:
            return f"data: {json.dumps(data)}\n\n"

        try:
            # ── Parse file ───────────────────────────────────────
            if filename.endswith(".csv"):
                df = pd.read_csv(io.BytesIO(contents))
            else:
                xl = pd.ExcelFile(io.BytesIO(contents))
                sname = sheet_name if sheet_name and sheet_name in xl.sheet_names else xl.sheet_names[0]
                df = pd.read_excel(io.BytesIO(contents), sheet_name=sname)

            if email_col not in df.columns:
                yield sse({"type": "error", "message": f"Column '{email_col}' not found in file."})
                return

            total_rows = len(df)
            yield sse({"type": "start", "total": total_rows})

            # ── Build task list ──────────────────────────────────
            results_classification = [None] * total_rows
            results_status = [None] * total_rows
            results_domain = [None] * total_rows
            results_provider = [None] * total_rows

            email_tasks = []
            for i, row in df.iterrows():
                val = str(row[email_col]).strip()
                if not val or val.lower() == "nan":
                    emails = []
                else:
                    emails = [e.strip() for e in re.split(r"[,;]", val) if e.strip()]
                email_tasks.append((i, emails))

            # ── Process in chunks ────────────────────────────────
            completed = 0
            chunk_size = 500
            loop = asyncio.get_event_loop()

            for chunk_start in range(0, len(email_tasks), chunk_size):
                chunk = email_tasks[chunk_start: chunk_start + chunk_size]

                with concurrent.futures.ThreadPoolExecutor(max_workers=15) as executor:
                    futures = {
                        executor.submit(process_row, idx, emails): (idx, emails)
                        for idx, emails in chunk
                    }
                    for future in concurrent.futures.as_completed(futures):
                        try:
                            idx, cls_s, st_s, dom_s, prov_s = future.result()
                            results_classification[idx] = cls_s
                            results_status[idx] = st_s
                            results_domain[idx] = dom_s
                            results_provider[idx] = prov_s
                        except Exception:
                            pass

                        completed += 1
                        # Throttle SSE updates to every 50 rows
                        if completed % 50 == 0 or completed == total_rows:
                            pct = int((completed / total_rows) * 100)
                            yield sse(
                                {
                                    "type": "progress",
                                    "completed": completed,
                                    "total": total_rows,
                                    "pct": pct,
                                }
                            )
                            # Yield control back to event loop
                            await asyncio.sleep(0)

                await asyncio.sleep(0.1)  # Breathe between chunks

            # ── Assemble result DataFrame ────────────────────────
            df["domain"] = results_domain
            df["domainprovider"] = results_provider
            df["classification"] = results_classification
            df["status code"] = results_status

            # ── Build Excel & store ──────────────────────────────
            excel_bytes = await loop.run_in_executor(None, build_excel, df, email_col)
            job_id = str(uuid.uuid4())
            job_results[job_id] = excel_bytes

            # ── Summary counts ───────────────────────────────────
            all_classes = []
            for v in df["classification"].dropna():
                all_classes.extend([c.strip() for c in str(v).split(",")])
            deliverable = all_classes.count("delivery")
            undeliverable = all_classes.count("undelivery")
            risky = len(all_classes) - deliverable - undeliverable

            yield sse(
                {
                    "type": "done",
                    "job_id": job_id,
                    "total": len(all_classes),
                    "deliverable": deliverable,
                    "undeliverable": undeliverable,
                    "risky": risky,
                }
            )

        except Exception as e:
            yield sse({"type": "error", "message": str(e)})

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


# ─────────────────────────────────────────────
# Bulk validation — JSON (non-streaming) endpoint
# ─────────────────────────────────────────────
@app.post("/validate/bulk/sync", summary="Bulk validate emails (synchronous JSON response)")
async def validate_bulk_sync(
    file: UploadFile = File(...),
    email_col: str = Form(...),
    sheet_name: Optional[str] = Form(None),
):
    """
    Upload a CSV or Excel file and receive results synchronously as JSON.
    Returns a job_id you can use with GET /result/{job_id} to download the Excel.
    Also returns row-level results and summary statistics.
    """
    filename = file.filename or ""
    contents = await file.read()

    try:
        if filename.endswith(".csv"):
            df = pd.read_csv(io.BytesIO(contents))
        else:
            xl = pd.ExcelFile(io.BytesIO(contents))
            sname = sheet_name if sheet_name and sheet_name in xl.sheet_names else xl.sheet_names[0]
            df = pd.read_excel(io.BytesIO(contents), sheet_name=sname)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Could not parse file: {e}")

    if email_col not in df.columns:
        raise HTTPException(status_code=400, detail=f"Column '{email_col}' not found in file.")

    total_rows = len(df)
    results_classification = [None] * total_rows
    results_status = [None] * total_rows
    results_domain = [None] * total_rows
    results_provider = [None] * total_rows

    email_tasks = []
    for i, row in df.iterrows():
        val = str(row[email_col]).strip()
        if not val or val.lower() == "nan":
            emails = []
        else:
            emails = [e.strip() for e in re.split(r"[,;]", val) if e.strip()]
        email_tasks.append((i, emails))

    loop = asyncio.get_event_loop()
    chunk_size = 500

    for chunk_start in range(0, len(email_tasks), chunk_size):
        chunk = email_tasks[chunk_start: chunk_start + chunk_size]
        with concurrent.futures.ThreadPoolExecutor(max_workers=15) as executor:
            futures = [executor.submit(process_row, idx, emails) for idx, emails in chunk]
            for future in concurrent.futures.as_completed(futures):
                try:
                    idx, cls_s, st_s, dom_s, prov_s = future.result()
                    results_classification[idx] = cls_s
                    results_status[idx] = st_s
                    results_domain[idx] = dom_s
                    results_provider[idx] = prov_s
                except Exception:
                    pass

    df["domain"] = results_domain
    df["domainprovider"] = results_provider
    df["classification"] = results_classification
    df["status code"] = results_status

    excel_bytes = await loop.run_in_executor(None, build_excel, df, email_col)
    job_id = str(uuid.uuid4())
    job_results[job_id] = excel_bytes

    all_classes = []
    for v in df["classification"].dropna():
        all_classes.extend([c.strip() for c in str(v).split(",")])
    deliverable = all_classes.count("delivery")
    undeliverable = all_classes.count("undelivery")
    risky = len(all_classes) - deliverable - undeliverable

    # Return row-level data as JSON
    rows_out = df.to_dict(orient="records")

    return JSONResponse(
        content={
            "job_id": job_id,
            "summary": {
                "total": len(all_classes),
                "deliverable": deliverable,
                "undeliverable": undeliverable,
                "risky": risky,
            },
            "rows": rows_out,
        }
    )


# ─────────────────────────────────────────────
# Download Excel result
# ─────────────────────────────────────────────
@app.get("/result/{job_id}", summary="Download validated Excel result file")
def download_result(job_id: str):
    """
    Download the Excel result file for a completed bulk validation job.
    The file contains multiple sheets: All_Data, Delivery, Undelivery, Risky_Protected, Catch_All.
    """
    excel_bytes = job_results.get(job_id)
    if excel_bytes is None:
        raise HTTPException(status_code=404, detail="Job not found or already expired.")

    return StreamingResponse(
        io.BytesIO(excel_bytes),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={
            "Content-Disposition": f'attachment; filename="validated_emails_{job_id[:8]}.xlsx"'
        },
    )


# ─────────────────────────────────────────────
# List sheet names in uploaded file
# ─────────────────────────────────────────────
@app.post("/file/sheets", summary="List sheet names in an uploaded Excel file")
async def list_sheets(file: UploadFile = File(...)):
    """
    Upload an Excel file and get back its sheet names.
    Use this to let users pick a sheet before calling /validate/bulk.
    """
    filename = file.filename or ""
    contents = await file.read()

    if filename.endswith(".csv"):
        return {"sheets": ["Sheet1"], "is_csv": True}

    try:
        xl = pd.ExcelFile(io.BytesIO(contents))
        return {"sheets": xl.sheet_names, "is_csv": False}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Could not read Excel file: {e}")


# ─────────────────────────────────────────────
# List columns in uploaded file
# ─────────────────────────────────────────────
@app.post("/file/columns", summary="List column names in an uploaded file")
async def list_columns(
    file: UploadFile = File(...),
    sheet_name: Optional[str] = Form(None),
):
    """
    Upload a CSV or Excel file and get back its column names.
    Use this to let users pick the email column before calling /validate/bulk.
    """
    filename = file.filename or ""
    contents = await file.read()

    try:
        if filename.endswith(".csv"):
            df = pd.read_csv(io.BytesIO(contents), nrows=0)
        else:
            xl = pd.ExcelFile(io.BytesIO(contents))
            sname = sheet_name if sheet_name and sheet_name in xl.sheet_names else xl.sheet_names[0]
            df = pd.read_excel(io.BytesIO(contents), sheet_name=sname, nrows=0)
        return {"columns": df.columns.tolist()}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Could not read file: {e}")


# ─────────────────────────────────────────────
# Entry point
# ─────────────────────────────────────────────
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=7860, reload=False)