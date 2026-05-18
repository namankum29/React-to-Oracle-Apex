import { useState } from "react";
import { motion } from "framer-motion";
import {
  Database,
  FileJson,
  LayoutTemplate,
  Download,
  UploadCloud,
  Copy,
  Check,
  TerminalSquare,
  Loader2,
  ArrowRight,
  FolderArchive,
  Sparkles,
  Hammer,
} from "lucide-react";
import axios from "axios";
import { toast } from "sonner";

import Sidebar from "@/components/apex/Sidebar";
import UploadCard from "@/components/apex/UploadCard";
import ConfigCard from "@/components/apex/ConfigCard";
import OutputPanel from "@/components/apex/OutputPanel";
import PagesPanel from "@/components/apex/PagesPanel";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const APEX_VERSIONS = ["22.2", "23.1", "23.2", "24.1", "24.2", "26.1"];

export default function Generator() {
  const [file, setFile] = useState(null);
  const [workspace, setWorkspace] = useState("WKSP_NSTS");
  const [appId, setAppId] = useState("205247");
  const [apexVersion, setApexVersion] = useState("24.2");
  const [runBuild, setRunBuild] = useState(false);

  const [activeSection, setActiveSection] = useState("generate");
  const [generating, setGenerating] = useState(false);
  const [result, setResult] = useState(null);

  const handleGenerate = async () => {
    if (!file) {
      toast.error("Please upload a React project ZIP first");
      return;
    }
    setGenerating(true);
    try {
      const formData = new FormData();
      formData.append("file", file);
      formData.append("workspace", workspace || "WKSP_DEFAULT");
      formData.append("app_id", String(appId || 100));
      formData.append("apex_version", apexVersion);
      formData.append("run_build", String(runBuild));

      const res = await axios.post(`${API}/apex/generate`, formData, {
        headers: { "Content-Type": "multipart/form-data" },
        timeout: 360000,
      });
      setResult(res.data);
      toast.success(
        `Generated ${res.data.component_count} APEX page${res.data.component_count === 1 ? "" : "s"}`
      );
    } catch (err) {
      const detail = err?.response?.data?.detail || err.message || "Generation failed";
      toast.error(typeof detail === "string" ? detail : "Generation failed");
    } finally {
      setGenerating(false);
    }
  };

  const handleDownload = () => {
    if (!result?.sql) return;
    const blob = new Blob([result.sql], { type: "application/sql" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `apex_${result.app_id}_${result.apex_version.replace(".", "_")}.sql`;
    a.click();
    URL.revokeObjectURL(url);
    toast.success("SQL file downloaded");
  };

  return (
    <div
      className="flex h-screen w-full bg-[#080C16] app-grid-bg text-slate-300 overflow-hidden font-sans selection:bg-blue-500/30"
      data-testid="app-shell"
    >
      <Sidebar
        active={activeSection}
        onChange={setActiveSection}
        hasResult={!!result}
        onDownload={handleDownload}
      />

      <div className="flex-1 flex flex-col h-full overflow-hidden relative z-10">
        <header
          className="h-20 border-b border-white/[0.08] bg-[#080C16]/60 backdrop-blur-xl flex items-center px-8 justify-between shrink-0"
          data-testid="app-header"
        >
          <div>
            <h1 className="text-xl lg:text-2xl text-white font-semibold tracking-tight flex items-center gap-3">
              <span className="w-9 h-9 rounded-xl bg-blue-500/10 border border-blue-500/30 flex items-center justify-center">
                <TerminalSquare className="w-4 h-4 text-blue-400" />
              </span>
              React to Oracle APEX Generator
            </h1>
            <p className="text-xs text-slate-500 mt-1 ml-12 tracking-wide">
              Convert React Forms, Reports &amp; Dashboards into APEX SQL
            </p>
          </div>
          <div className="hidden md:flex items-center gap-3">
            <div className="px-3 py-1.5 rounded-full bg-emerald-500/10 border border-emerald-500/20 text-[11px] text-emerald-400 font-medium flex items-center gap-2">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse"></span>
              APEX {apexVersion} ready
            </div>
          </div>
        </header>

        <main className="flex-1 overflow-y-auto p-6 lg:p-8 scrollbar-hide">
          {activeSection === "generate" && (
            <motion.div
              key="generate"
              initial={{ opacity: 0, y: 12 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.4 }}
              className="grid grid-cols-1 lg:grid-cols-12 gap-6 max-w-[1600px] mx-auto w-full"
            >
              <div className="col-span-1 lg:col-span-5 flex flex-col gap-6">
                <UploadCard file={file} onFile={setFile} />
                <ConfigCard
                  workspace={workspace}
                  appId={appId}
                  apexVersion={apexVersion}
                  runBuild={runBuild}
                  versions={APEX_VERSIONS}
                  onWorkspace={setWorkspace}
                  onAppId={setAppId}
                  onApexVersion={setApexVersion}
                  onRunBuild={setRunBuild}
                />

                <button
                  data-testid="generate-btn"
                  onClick={handleGenerate}
                  disabled={generating || !file}
                  className="w-full bg-blue-600 hover:bg-blue-500 disabled:bg-blue-900/40 disabled:cursor-not-allowed text-white rounded-xl px-6 py-3.5 font-medium transition-all duration-300 shadow-[0_0_20px_rgba(37,99,235,0.15)] hover:shadow-[0_0_30px_rgba(37,99,235,0.35)] flex items-center justify-center gap-2 group"
                >
                  {generating ? (
                    <>
                      <Loader2 className="w-4 h-4 animate-spin" />
                      Generating...
                    </>
                  ) : (
                    <>
                      <Sparkles className="w-4 h-4" />
                      Generate APEX SQL
                      <ArrowRight className="w-4 h-4 opacity-70 group-hover:translate-x-0.5 transition-transform" />
                    </>
                  )}
                </button>
              </div>

              <div className="col-span-1 lg:col-span-7 flex flex-col gap-6 min-h-[640px]">
                <OutputPanel result={result} generating={generating} onDownload={handleDownload} />
              </div>
            </motion.div>
          )}

          {activeSection === "pages" && (
            <motion.div
              key="pages"
              initial={{ opacity: 0, y: 12 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.4 }}
              className="max-w-[1600px] mx-auto w-full"
            >
              <PagesPanel result={result} />
            </motion.div>
          )}

          {activeSection === "export" && (
            <motion.div
              key="export"
              initial={{ opacity: 0, y: 12 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.4 }}
              className="max-w-3xl mx-auto w-full"
              data-testid="export-panel"
            >
              <div className="bg-[#0D1322]/40 backdrop-blur-xl border border-white/[0.08] rounded-2xl p-8 shadow-2xl shadow-black/50">
                <div className="flex items-center gap-3 mb-6">
                  <div className="w-10 h-10 rounded-xl bg-blue-500/10 border border-blue-500/30 flex items-center justify-center">
                    <Download className="w-4 h-4 text-blue-400" />
                  </div>
                  <div>
                    <h2 className="text-lg text-white font-medium">Export</h2>
                    <p className="text-xs text-slate-500">Download the generated APEX migration package</p>
                  </div>
                </div>
                {result ? (
                  <div className="space-y-4">
                    <div className="flex items-center justify-between p-4 bg-[#03060C] border border-white/[0.08] rounded-xl">
                      <div className="flex items-center gap-3">
                        <FileJson className="w-4 h-4 text-blue-400" />
                        <div>
                          <p className="text-sm text-white font-medium">
                            apex_{result.app_id}_{result.apex_version.replace(".", "_")}.sql
                          </p>
                          <p className="text-xs text-slate-500">
                            {result.component_count} pages · {Math.round(result.sql.length / 1024)} KB
                          </p>
                        </div>
                      </div>
                      <button
                        onClick={handleDownload}
                        data-testid="export-download-btn"
                        className="bg-blue-600 hover:bg-blue-500 text-white rounded-lg px-4 py-2 text-sm font-medium flex items-center gap-2 transition-all"
                      >
                        <Download className="w-3.5 h-3.5" />
                        Download
                      </button>
                    </div>
                    <div className="text-xs text-slate-500 leading-relaxed p-4 bg-white/[0.02] border border-white/[0.06] rounded-xl">
                      <p className="text-slate-300 font-medium mb-2 flex items-center gap-2">
                        <Hammer className="w-3.5 h-3.5 text-amber-400" /> How to import
                      </p>
                      <ol className="list-decimal list-inside space-y-1.5">
                        <li>Open Oracle APEX → SQL Workshop → SQL Commands.</li>
                        <li>Paste the generated SQL.</li>
                        <li>Run the script — pages, regions and the <code className="text-blue-300">react_theme.css</code> static file will be created in workspace <span className="text-blue-300">{result.workspace}</span>.</li>
                      </ol>
                    </div>
                  </div>
                ) : (
                  <div className="text-center py-16 text-slate-500 text-sm" data-testid="export-empty">
                    Generate SQL first to enable export.
                  </div>
                )}
              </div>
            </motion.div>
          )}
        </main>
      </div>
    </div>
  );
}
