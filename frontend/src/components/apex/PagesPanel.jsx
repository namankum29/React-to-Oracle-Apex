import { LayoutTemplate, FileText, BarChart3, ClipboardList } from "lucide-react";

const TYPE_META = {
  form: {
    icon: FileText,
    color: "text-blue-400",
    bg: "bg-blue-500/10",
    border: "border-blue-500/30",
    label: "Form",
  },
  report: {
    icon: ClipboardList,
    color: "text-amber-400",
    bg: "bg-amber-500/10",
    border: "border-amber-500/30",
    label: "Interactive Report",
  },
  dashboard: {
    icon: BarChart3,
    color: "text-emerald-400",
    bg: "bg-emerald-500/10",
    border: "border-emerald-500/30",
    label: "Dashboard",
  },
};

export default function PagesPanel({ result }) {
  if (!result) {
    return (
      <div
        className="bg-[#0D1322]/40 backdrop-blur-xl border border-white/[0.08] rounded-2xl p-12 text-center shadow-2xl shadow-black/50"
        data-testid="pages-empty"
      >
        <LayoutTemplate className="w-8 h-8 text-slate-600 mx-auto mb-3" />
        <p className="text-sm text-slate-400 font-medium">No pages detected</p>
        <p className="text-xs text-slate-600 mt-1.5">
          Generate SQL from a React project to view the inferred APEX pages.
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-5" data-testid="pages-panel">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-lg text-white font-medium">Detected APEX Pages</h2>
          <p className="text-xs text-slate-500 mt-1">
            {result.component_count} components mapped to APEX
          </p>
        </div>
        <span className="text-[10px] uppercase tracking-widest text-slate-500">
          App ID {result.app_id}
        </span>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-3 gap-4">
        {result.pages.map((p) => {
          const meta = TYPE_META[p.type] || TYPE_META.form;
          const Icon = meta.icon;
          return (
            <div
              key={p.page_id}
              data-testid={`page-card-${p.page_id}`}
              className="bg-[#0D1322]/40 backdrop-blur-xl border border-white/[0.08] rounded-2xl p-5 hover:border-white/[0.15] hover:-translate-y-0.5 transition-all duration-300 shadow-xl shadow-black/40"
            >
              <div className="flex items-start justify-between mb-4">
                <div className={`w-10 h-10 rounded-xl ${meta.bg} border ${meta.border} flex items-center justify-center`}>
                  <Icon className={`w-4 h-4 ${meta.color}`} />
                </div>
                <span className="text-[10px] uppercase tracking-widest text-slate-500 font-medium">
                  Page {p.page_id}
                </span>
              </div>
              <h3 className="text-sm text-white font-medium mb-1 truncate">{p.name}</h3>
              <p className={`text-[11px] ${meta.color} font-medium tracking-wide`}>{meta.label}</p>
              {p.type === "form" && (
                <p className="text-[11px] text-slate-500 mt-3">
                  {p.fields} item{p.fields === 1 ? "" : "s"}
                </p>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
