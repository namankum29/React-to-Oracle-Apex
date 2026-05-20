"""Backend tests for React → Oracle APEX Generator."""
import io
import os
import zipfile
import requests
import pytest

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "").rstrip("/") or \
    open("/app/frontend/.env").read().split("REACT_APP_BACKEND_URL=")[1].splitlines()[0].strip()
API = f"{BASE_URL}/api"


def _build_zip() -> bytes:
    """Construct an in-memory React project zip with form/report/dashboard."""
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("proj/package.json", '{"name":"t","version":"1.0.0"}')
        z.writestr(
            "proj/src/UserForm.jsx",
            """
import React, {useState} from 'react';
export default function UserForm(){
  const emptyForm = { name: '', email: '', age: 0, description: '', dob: '' };
  const [form, setForm] = useState(emptyForm);
  return (<form>
    <input name="name" value={form.name} />
    <input name="email" value={form.email} />
    <input name="age" value={form.age} />
    <textarea name="description" value={form.description} />
    <input name="dob" value={form.dob} />
  </form>);
}
""",
        )
        z.writestr(
            "proj/src/UsersReport.tsx",
            """
export default function UsersReport(){
  const rows = [1,2,3];
  return (<table>{rows.map((r)=>(<tr key={r}><td>{r}</td></tr>))}</table>);
}
""",
        )
        z.writestr(
            "proj/src/SalesDashboard.jsx",
            """
import { LineChart, BarChart } from 'recharts';
export default function SalesDashboard(){
  return (<div className="dashboard stat-card"><LineChart/></div>);
}
""",
        )
    return buf.getvalue()


@pytest.fixture(scope="module")
def zip_bytes():
    return _build_zip()


# ----- versions endpoint -----
def test_versions_endpoint():
    r = requests.get(f"{API}/apex/versions", timeout=30)
    assert r.status_code == 200
    data = r.json()
    assert "versions" in data
    assert data["versions"] == ["22.2", "23.1", "23.2", "24.1", "24.2", "26.1"]


# ----- generate happy path -----
def test_generate_success_242(zip_bytes):
    files = {"file": ("sample.zip", zip_bytes, "application/zip")}
    data = {"workspace": "WKSP_NSTS", "app_id": "205247", "apex_version": "24.2", "run_build": "false"}
    r = requests.post(f"{API}/apex/generate", files=files, data=data, timeout=120)
    assert r.status_code == 200, r.text
    body = r.json()
    assert "sql" in body and "pages" in body and "session_id" in body
    assert body["component_count"] >= 1
    assert body["workspace"] == "WKSP_NSTS"
    assert body["app_id"] == 205247

    sql = body["sql"]
    # PL/SQL core constructs cloned from real APEX 24.2 page exports
    for token in [
        "wwv_flow_imp.import_begin",
        "wwv_flow_imp.import_end",
        "wwv_flow_imp_page.create_page",
        "wwv_flow_imp_page.create_page_plug",
        "wwv_flow_imp_page.create_page_button",
        "wwv_flow_imp_page.create_page_item",
        "wwv_flow_imp_page.create_worksheet",
        "wwv_flow_imp_page.create_worksheet_column",
        "wwv_flow_imp_page.create_worksheet_rpt",
        "wwv_flow_imp_shared.create_app_static_file",
        "apex_util.find_security_group_id",
        "wwv_flow_imp.id(",
        "wwv_flow_t_plugin_attributes",
        "p_protection_level=>'C'",
        "p_page_component_map=>",
        "NATIVE_IR",
        "WKSP_NSTS",
        "205247",
    ]:
        assert token in sql, f"missing token: {token}"

    # Must NOT contain the previously-broken plugin names
    assert "NATIVE_HTML" not in sql, "regressed to NATIVE_HTML"
    assert "NATIVE_STATIC" not in sql, "regressed to NATIVE_STATIC"
    assert "NATIVE_SQL_REPORT" not in sql, "regressed to NATIVE_SQL_REPORT"

    # Page types detected
    types = {p["type"] for p in body["pages"]}
    assert {"form", "report", "dashboard"}.issubset(types), f"types={types}"


# ----- lower APEX version still works -----
def test_generate_version_22_2(zip_bytes):
    files = {"file": ("sample.zip", zip_bytes, "application/zip")}
    data = {"workspace": "WKSP_T", "app_id": "100", "apex_version": "22.2"}
    r = requests.post(f"{API}/apex/generate", files=files, data=data, timeout=120)
    assert r.status_code == 200
    sql = r.json()["sql"]
    assert "Target APEX Version: 22.2" in sql
    assert "wwv_flow_imp_page.create_page" in sql


# ----- reject non-zip -----
def test_generate_rejects_non_zip():
    files = {"file": ("readme.txt", b"hello", "text/plain")}
    data = {"workspace": "W", "app_id": "1", "apex_version": "24.2"}
    r = requests.post(f"{API}/apex/generate", files=files, data=data, timeout=30)
    assert r.status_code == 400
    assert "zip" in r.text.lower()


# ----- runs listing -----
def test_runs_listing_no_id_no_sql(zip_bytes):
    # Ensure at least one run exists
    requests.post(
        f"{API}/apex/generate",
        files={"file": ("s.zip", zip_bytes, "application/zip")},
        data={"workspace": "WKSP_NSTS", "app_id": "205247", "apex_version": "24.2"},
        timeout=120,
    )
    r = requests.get(f"{API}/apex/runs", timeout=30)
    assert r.status_code == 200
    body = r.json()
    assert "runs" in body and isinstance(body["runs"], list)
    assert len(body["runs"]) >= 1
    first = body["runs"][0]
    assert "_id" not in first
    assert "sql" not in first
    assert "workspace" in first and "app_id" in first
