import { Database, LayoutTemplate, Download, TerminalSquare, ChevronRight } from "lucide-react";

const NAV = [
  { key: "generate", label: "Generate SQL", icon: TerminalSquare },
  { key: "pages", label: "APEX Pages", icon: LayoutTemplate },
  { key: "export", label: "Export", icon: Download },
];

export default function Sidebar({ active, onChange, hasResult }) {
  return (
    <aside
      className="w-64 flex-shrink-0 border-r border-white/[0.08] bg-[#0A0F1C]/40 backdrop-blur-2xl flex flex-col z-20"
      data-testid="sidebar"
    >
      <div className="h-20 flex items-center px-6 border-b border-white/[0.08]">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-blue-500 to-blue-700 flex items-center justify-center shadow-[0_0_24px_rgba(59,130,246,0.35)]">
            <Database className="w-4 h-4 text-white" />
          </div>
          <div>
            <p className="text-white text-sm font-semibold tracking-tight">APEX Forge</p>
            <p className="text-[10px] text-slate-500 uppercase tracking-widest">v1.0</p>
          </div>
        </div>
      </div>

      <nav className="flex-1 py-6 space-y-1" data-testid="sidebar-nav">
        <p className="px-8 text-[10px] font-medium text-slate-500 uppercase tracking-widest mb-3">
          Workspace
        </p>
        {NAV.map(({ key, label, icon: Icon }) => {
          const isActive = active === key;
          const disabled = (key === "pages" || key === "export") && !hasResult;
          return (
            <button
              key={key}
              data-testid={`sidebar-${key}`}
              onClick={() => !disabled && onChange(key)}
              disabled={disabled}
              className={`relative w-full flex items-center gap-3 px-4 py-2.5 rounded-xl mx-4 text-sm font-medium transition-all group ${
                isActive
                  ? "bg-blue-500/10 text-blue-400 border border-blue-500/20 shadow-[inset_0_0_12px_rgba(59,130,246,0.1)]"
                  : disabled
                  ? "text-slate-600 cursor-not-allowed"
                  : "text-slate-400 hover:text-white hover:bg-white/[0.04] border border-transparent"
              }`}
              style={{ width: "calc(100% - 2rem)" }}
            >
              <Icon className="w-4 h-4" />
              <span className="flex-1 text-left">{label}</span>
              {isActive && <ChevronRight className="w-3.5 h-3.5 opacity-70" />}
            </button>
          );
        })}
      </nav>

      <div className="p-4 border-t border-white/[0.08]">
        <div className="rounded-xl border border-white/[0.08] bg-white/[0.02] p-3">
          <p className="text-[10px] uppercase tracking-widest text-slate-500 mb-1">Tip</p>
          <p className="text-xs text-slate-400 leading-relaxed">
            Drop a React ZIP, configure your workspace, then generate executable APEX SQL.
          </p>
        </div>
      </div>
    </aside>
  );
}
