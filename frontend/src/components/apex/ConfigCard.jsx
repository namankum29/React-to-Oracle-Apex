import { Settings2, ChevronDown, Hammer } from "lucide-react";

export default function ConfigCard({
  workspace,
  appId,
  apexVersion,
  runBuild,
  versions,
  onWorkspace,
  onAppId,
  onApexVersion,
  onRunBuild,
}) {
  return (
    <div
      className="bg-[#0D1322]/40 backdrop-blur-xl border border-white/[0.08] rounded-2xl p-6 shadow-2xl shadow-black/50"
      data-testid="config-card"
    >
      <div className="flex items-center gap-3 mb-5">
        <div className="w-9 h-9 rounded-xl bg-blue-500/10 border border-blue-500/30 flex items-center justify-center">
          <Settings2 className="w-4 h-4 text-blue-400" />
        </div>
        <div>
          <h2 className="text-base text-white font-medium">APEX Configuration</h2>
          <p className="text-[11px] text-slate-500 tracking-wide">Workspace · App ID · Version</p>
        </div>
      </div>

      <div className="space-y-4">
        <div>
          <label className="text-[10px] font-medium text-slate-400 uppercase tracking-widest block mb-2">
            Workspace
          </label>
          <input
            value={workspace}
            onChange={(e) => onWorkspace(e.target.value)}
            placeholder="WKSP_NSTS"
            data-testid="input-workspace"
            className="w-full bg-[#03060C] border border-white/[0.1] rounded-xl px-4 py-2.5 text-sm text-white focus:outline-none focus:ring-2 focus:ring-blue-500/40 focus:border-blue-500/50 transition-all placeholder:text-slate-600 shadow-inner"
          />
        </div>

        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="text-[10px] font-medium text-slate-400 uppercase tracking-widest block mb-2">
              Application ID
            </label>
            <input
              type="number"
              value={appId}
              onChange={(e) => onAppId(e.target.value)}
              placeholder="100"
              data-testid="input-app-id"
              className="w-full bg-[#03060C] border border-white/[0.1] rounded-xl px-4 py-2.5 text-sm text-white focus:outline-none focus:ring-2 focus:ring-blue-500/40 focus:border-blue-500/50 transition-all placeholder:text-slate-600 shadow-inner"
            />
          </div>
          <div>
            <label className="text-[10px] font-medium text-slate-400 uppercase tracking-widest block mb-2">
              APEX Version
            </label>
            <div className="relative">
              <select
                value={apexVersion}
                onChange={(e) => onApexVersion(e.target.value)}
                data-testid="select-apex-version"
                className="w-full bg-[#03060C] border border-white/[0.1] rounded-xl px-4 py-2.5 text-sm text-white focus:outline-none focus:ring-2 focus:ring-blue-500/40 focus:border-blue-500/50 appearance-none cursor-pointer shadow-inner pr-9"
              >
                {versions.map((v) => (
                  <option key={v} value={v} className="bg-[#0D1322]">
                    {v}
                  </option>
                ))}
              </select>
              <ChevronDown className="w-4 h-4 text-slate-500 absolute right-3 top-1/2 -translate-y-1/2 pointer-events-none" />
            </div>
          </div>

          <div className="mt-5">
  <label className="flex items-center justify-between cursor-pointer">
    <div>
      <p className="text-sm text-white font-medium">
        Run React Build
      </p>

      <p className="text-xs text-slate-500 mt-1">
        Executes npm install + npm run build before parsing
      </p>
    </div>

    <button
      type="button"
      onClick={() => onRunBuild(!runBuild)}
      className={`relative inline-flex h-6 w-11 items-center rounded-full transition ${
        runBuild ? "bg-blue-600" : "bg-slate-700"
      }`}
    >
      <span
        className={`inline-block h-4 w-4 transform rounded-full bg-white transition ${
          runBuild ? "translate-x-6" : "translate-x-1"
        }`}
      />
    </button>
  </label>
</div>
        </div>

        <div className="flex items-center justify-between p-3 bg-white/[0.02] border border-white/[0.06] rounded-xl">
          <div className="flex items-center gap-3">
            <Hammer className="w-4 h-4 text-amber-400" />
            <div>
              <p className="text-xs text-white font-medium">Run npm build</p>
              <p className="text-[10px] text-slate-500">Compile Tailwind into static CSS (slower)</p>
            </div>
          </div>
          <button
            type="button"
            onClick={() => onRunBuild(!runBuild)}
            data-testid="toggle-run-build"
            className={`relative w-11 h-6 rounded-full transition-colors ${
              runBuild ? "bg-blue-600" : "bg-white/[0.08]"
            }`}
          >
            <span
              className={`absolute top-0.5 left-0.5 w-5 h-5 rounded-full bg-white shadow transition-transform ${
                runBuild ? "translate-x-5" : "translate-x-0"
              }`}
            />
          </button>
        </div>
      </div>
    </div>
  );
}
