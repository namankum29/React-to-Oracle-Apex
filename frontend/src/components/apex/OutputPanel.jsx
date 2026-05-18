import { useMemo, useState } from "react";
import { Copy, Check, TerminalSquare, Download, Loader2, FileJson } from "lucide-react";
import { toast } from "sonner";

function highlightSql(sql) {
  if (!sql) return null;
  const keywords = [
    "begin", "end", "declare", "as", "select", "from", "where", "into",
    "insert", "update", "delete", "values", "create", "or", "replace",
    "function", "procedure", "package", "body", "is", "return", "for",
    "loop", "if", "then", "else", "elsif", "and", "not", "null", "exception",
    "when", "others", "commit", "rollback", "set",
  ];
  const kwRe = new RegExp(`\\b(${keywords.join("|")})\\b`, "gi");

  return sql.split("\n").map((line, idx) => {
    if (line.trim().startsWith("--")) {
      return (
        <div key={idx} className="text-slate-500 italic">
          {line || " "}
        </div>
      );
    }
    // Strings
    const parts = [];
    let lastIdx = 0;
    const strRe = /'((?:[^']|'')*)'/g;
    let match;
    while ((match = strRe.exec(line)) !== null) {
      parts.push({ type: "code", value: line.slice(lastIdx, match.index) });
      parts.push({ type: "string", value: match[0] });
      lastIdx = match.index + match[0].length;
    }
    parts.push({ type: "code", value: line.slice(lastIdx) });

    return (
      <div key={idx}>
        {parts.map((p, i) => {
          if (p.type === "string") {
            return (
              <span key={i} className="text-emerald-300">
                {p.value}
              </span>
            );
          }
          const tokens = p.value.split(kwRe);
          return (
            <span key={i}>
              {tokens.map((tok, j) => {
                if (keywords.includes(tok?.toLowerCase())) {
                  return (
                    <span key={j} className="text-purple-300 font-medium">
                      {tok}
                    </span>
                  );
                }
                // numbers
                if (/^\d+(\.\d+)?$/.test(tok?.trim() || "")) {
                  return (
                    <span key={j} className="text-amber-300">
                      {tok}
                    </span>
                  );
                }
                // apex_* and wwv_flow_imp_* function calls
                const apexRe = /(apex_[a-z_]+|wwv_flow_imp_[a-z_]+)/gi;
                if (apexRe.test(tok || "")) {
                  const subTokens = tok.split(apexRe);
                  return (
                    <span key={j}>
                      {subTokens.map((t, k) =>
                        /^(apex_|wwv_flow_imp_)/i.test(t) ? (
                          <span key={k} className="text-blue-300">
                            {t}
                          </span>
                        ) : (
                          <span key={k}>{t}</span>
                        )
                      )}
                    </span>
                  );
                }
                return <span key={j}>{tok}</span>;
              })}
            </span>
          );
        })}
        {line === "" && " "}
      </div>
    );
  });
}

export default function OutputPanel({ result, generating, onDownload }) {
  const [copied, setCopied] = useState(false);
  const highlighted = useMemo(() => highlightSql(result?.sql), [result?.sql]);

  const handleCopy = async () => {
    if (!result?.sql) return;
    try {
      await navigator.clipboard.writeText(result.sql);
      setCopied(true);
      toast.success("SQL copied to clipboard");
      setTimeout(() => setCopied(false), 2000);
    } catch {
      toast.error("Copy failed — clipboard not available");
    }
  };

  return (
    <div
      className="bg-[#03060C] rounded-2xl border border-white/[0.08] overflow-hidden flex flex-col h-full shadow-inner"
      data-testid="output-panel"
    >
      <div className="flex items-center justify-between px-5 py-3 border-b border-white/[0.06] bg-[#0D1322]/40">
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-1.5">
            <span className="w-2.5 h-2.5 rounded-full bg-red-500/50" />
            <span className="w-2.5 h-2.5 rounded-full bg-amber-500/50" />
            <span className="w-2.5 h-2.5 rounded-full bg-emerald-500/50" />
          </div>
          <div className="flex items-center gap-2 text-xs text-slate-400 ml-2 font-mono">
            <TerminalSquare className="w-3.5 h-3.5 text-blue-400" />
            <span>
              {result
                ? `apex_${result.app_id}_${result.apex_version.replace(".", "_")}.sql`
                : "output.sql"}
            </span>
          </div>
        </div>
        <div className="flex items-center gap-2">
          {result && (
            <span className="text-[10px] text-slate-500 uppercase tracking-widest font-medium hidden sm:inline">
              {result.component_count} pages · {Math.round(result.sql.length / 1024)} KB
            </span>
          )}
          <button
            data-testid="download-sql-btn"
            onClick={onDownload}
            disabled={!result}
            className="bg-white/[0.03] hover:bg-white/[0.08] text-slate-200 disabled:opacity-30 disabled:cursor-not-allowed border border-white/[0.08] hover:border-white/[0.15] rounded-lg px-3 py-1.5 text-xs font-medium transition-all flex items-center gap-1.5"
          >
            <Download className="w-3 h-3" />
            <span className="hidden sm:inline">Download</span>
          </button>
          <button
            data-testid="copy-sql-btn"
            onClick={handleCopy}
            disabled={!result}
            className="bg-blue-600 hover:bg-blue-500 disabled:bg-white/[0.03] disabled:text-slate-600 disabled:cursor-not-allowed text-white border border-blue-500/50 disabled:border-white/[0.08] rounded-lg px-3 py-1.5 text-xs font-medium transition-all flex items-center gap-1.5"
          >
            {copied ? (
              <>
                <Check className="w-3 h-3" />
                Copied!
              </>
            ) : (
              <>
                <Copy className="w-3 h-3" />
                Copy SQL
              </>
            )}
          </button>
        </div>
      </div>

      <div className="flex-1 overflow-auto p-5 scrollbar-hide">
        {generating ? (
          <div className="h-full flex flex-col items-center justify-center text-center" data-testid="output-loading">
            <Loader2 className="w-10 h-10 text-blue-400 animate-spin mb-4" />
            <p className="text-sm text-slate-300 font-medium">Generating APEX SQL...</p>
            <p className="text-xs text-slate-500 mt-1">Parsing components and emitting PL/SQL</p>
          </div>
        ) : result ? (
          <pre
            className="sql-pre font-mono text-[12.5px] leading-6 text-slate-200 whitespace-pre-wrap break-words"
            data-testid="sql-output"
          >
            {highlighted}
          </pre>
        ) : (
          <div className="h-full flex flex-col items-center justify-center text-center" data-testid="output-empty">
            <div className="w-14 h-14 rounded-2xl bg-blue-500/5 border border-blue-500/15 flex items-center justify-center mb-4">
              <FileJson className="w-5 h-5 text-blue-400/70" />
            </div>
            <p className="text-sm text-slate-400 font-medium">No SQL generated yet</p>
            <p className="text-xs text-slate-600 mt-1.5 max-w-xs">
              Upload a React project ZIP and click <span className="text-blue-300">Generate APEX SQL</span> to see executable PL/SQL here.
            </p>
          </div>
        )}
      </div>
    </div>
  );
}
