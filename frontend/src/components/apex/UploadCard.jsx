import { useCallback, useRef, useState } from "react";
import { UploadCloud, FolderArchive, X, FileCheck2 } from "lucide-react";

export default function UploadCard({ file, onFile }) {
  const inputRef = useRef(null);
  const [dragOver, setDragOver] = useState(false);

  const handleFiles = useCallback(
    (files) => {
      const f = files?.[0];
      if (!f) return;
      if (!f.name.toLowerCase().endsWith(".zip")) {
        alert("Please upload a .zip file");
        return;
      }
      onFile(f);
    },
    [onFile]
  );

  return (
    <div
      className="bg-[#0D1322]/40 backdrop-blur-xl border border-white/[0.08] rounded-2xl p-6 shadow-2xl shadow-black/50"
      data-testid="upload-card"
    >
      <div className="flex items-center justify-between mb-5">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-xl bg-blue-500/10 border border-blue-500/30 flex items-center justify-center">
            <UploadCloud className="w-4 h-4 text-blue-400" />
          </div>
          <div>
            <h2 className="text-base text-white font-medium">React Project</h2>
            <p className="text-[11px] text-slate-500 tracking-wide">ZIP · Vite · CRA · TypeScript</p>
          </div>
        </div>
        {file && (
          <span className="text-[10px] uppercase tracking-widest text-emerald-400 font-medium px-2 py-1 bg-emerald-500/10 border border-emerald-500/20 rounded-full">
            Ready
          </span>
        )}
      </div>

      {!file ? (
        <div
          data-testid="upload-zone"
          onClick={() => inputRef.current?.click()}
          onDragOver={(e) => {
            e.preventDefault();
            setDragOver(true);
          }}
          onDragLeave={() => setDragOver(false)}
          onDrop={(e) => {
            e.preventDefault();
            setDragOver(false);
            handleFiles(e.dataTransfer.files);
          }}
          className={`border-2 border-dashed rounded-xl px-6 py-10 flex flex-col items-center justify-center text-center cursor-pointer transition-all duration-300 group ${
            dragOver
              ? "border-blue-500/60 bg-blue-500/[0.04]"
              : "border-white/[0.12] bg-[#0D1322]/20 hover:border-blue-500/40 hover:bg-white/[0.02]"
          }`}
        >
          <div className="w-12 h-12 rounded-2xl bg-blue-500/10 border border-blue-500/20 flex items-center justify-center mb-4 group-hover:scale-110 transition-transform">
            <FolderArchive className="w-5 h-5 text-blue-400" />
          </div>
          <p className="text-sm text-white font-medium">Drop your React ZIP here</p>
          <p className="text-xs text-slate-500 mt-1.5">or click to browse · max 100 MB</p>
          <input
            ref={inputRef}
            type="file"
            accept=".zip"
            className="hidden"
            data-testid="upload-input"
            onChange={(e) => handleFiles(e.target.files)}
          />
        </div>
      ) : (
        <div
          className="flex items-center justify-between p-4 bg-[#03060C] border border-white/[0.08] rounded-xl"
          data-testid="upload-selected"
        >
          <div className="flex items-center gap-3 min-w-0">
            <div className="w-10 h-10 rounded-xl bg-emerald-500/10 border border-emerald-500/30 flex items-center justify-center flex-shrink-0">
              <FileCheck2 className="w-4 h-4 text-emerald-400" />
            </div>
            <div className="min-w-0">
              <p className="text-sm text-white font-medium truncate" data-testid="upload-filename">
                {file.name}
              </p>
              <p className="text-[11px] text-slate-500">
                {(file.size / 1024 / 1024).toFixed(2)} MB
              </p>
            </div>
          </div>
          <button
            onClick={() => onFile(null)}
            data-testid="upload-clear-btn"
            className="text-slate-500 hover:text-white p-1.5 rounded-lg hover:bg-white/[0.05] transition-all"
          >
            <X className="w-4 h-4" />
          </button>
        </div>
      )}
    </div>
  );
}
