"use client";
import { useState, useRef, useCallback, useEffect } from "react";
import ReactMarkdown from "react-markdown";
import { useStore, Report } from "../lib/store";

const AGENT_LABELS: Record<string, { label: string; icon: string }> = {
  rag_retriever: { label: "Searching knowledge base", icon: "📚" },
  researcher:    { label: "Searching the web",         icon: "🔍" },
  fact_checker:  { label: "Verifying facts",           icon: "✅" },
  summarizer:    { label: "Summarizing findings",      icon: "📝" },
  writer:        { label: "Writing report",            icon: "✍️"  },
  done:          { label: "Complete",                  icon: "🎉" },
};
const AGENT_ORDER = ["rag_retriever","researcher","fact_checker","summarizer","writer","done"];

interface DocInfo { filename: string; size_mb: number; chunks: number; pages: number|null; }

export default function Home() {
  const [tab, setTab] = useState<"research"|"history">("research");
  const [topic, setTopic] = useState("");
  const [steps, setSteps] = useState<string[]>([]);
  const [streamedReport, setStreamedReport] = useState("");
  const [fullReport, setFullReport] = useState("");
  const [citations, setCitations] = useState<string[]>([]);
  const [loading, setLoading] = useState(false);
  const [activeStep, setActiveStep] = useState("");
  const [showCitations, setShowCitations] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [uploadError, setUploadError] = useState("");
  const [docs, setDocs] = useState<DocInfo[]>([]);
  const [selectedHistory, setSelectedHistory] = useState<Report | null>(null);
  const reportRef = useRef<HTMLDivElement>(null);
  const fileRef = useRef<HTMLInputElement>(null);
  const { reports, saveReport, deleteReport } = useStore();

  // Load existing docs on mount
  useEffect(() => {
    fetch("https://neura-e4cg.onrender.com/api/documents")
      .then(r => r.json())
      .then(d => setDocs(d.documents || []))
      .catch(() => {});
  }, []);

  const typewrite = useCallback((text: string) => {
    setStreamedReport("");
    let i = 0;
    const interval = setInterval(() => {
      if (i <= text.length) { setStreamedReport(text.slice(0, i)); i += 8; }
      else { clearInterval(interval); setStreamedReport(text); }
    }, 16);
  }, []);

  const runResearch = async () => {
    if (!topic.trim() || loading) return;
    setLoading(true); let buffer = ""; setSteps([]); setStreamedReport("");
    setFullReport(""); setCitations([]); setActiveStep(""); setShowCitations(false);
    try {
      const res = await fetch("https://neura-e4cg.onrender.com/api/research/stream", {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ topic }),
      });
      const reader = res.body!.getReader();
      const decoder = new TextDecoder();
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split("\n");
        buffer = lines.pop() || "";
        for (const line of lines) {
          if (!line.startsWith("data: ")) continue;
          let data;
          try {
            const jsonStr = line.slice(6).trim();
            if (!jsonStr || jsonStr === "[DONE]") continue;
            data = JSON.parse(jsonStr);
          } catch(e) { continue; }
          setActiveStep(data.node);
          setSteps(prev => prev.includes(data.node) ? prev : [...prev, data.node]);
          if (data.node === "writer" && data.state?.writer?.final_report) {
            const report = data.state.writer.final_report;
            const cites = data.state.writer.citations || [];
            setFullReport(report); setCitations(cites);
            typewrite(report);
            saveReport({ topic, report, citations: cites });
            setTimeout(() => reportRef.current?.scrollIntoView({ behavior: "smooth" }), 300);
          }
        }
      }
    } catch (e) { console.error(e); }
    finally { setLoading(false); }
  };

  const handleUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setUploading(true); setUploadError("");
    const form = new FormData();
    form.append("file", file);
    try {
      const res = await fetch("https://neura-e4cg.onrender.com/api/ingest", { method: "POST", body: form });
      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || "Upload failed");
      }
      const data = await res.json();
      setDocs(prev => [...prev, {
        filename: data.filename,
        size_mb: data.size_mb,
        chunks: data.chunks_ingested,
        pages: data.pages,
      }]);
    } catch(err: any) {
      setUploadError(err.message || "Upload failed");
    } finally {
      setUploading(false);
      if (fileRef.current) fileRef.current.value = "";
    }
  };

  const researchFromDoc = (doc: DocInfo) => {
    setTopic(`Summarize and explain: ${doc.filename.replace(/\.[^/.]+$/, "")}`);
    setTimeout(() => document.querySelector("input")?.focus(), 100);
  };

  const exportMarkdown = () => {
    const blob = new Blob([fullReport], { type: "text/markdown" });
    const a = document.createElement("a");
    a.href = URL.createObjectURL(blob);
    a.download = `${topic.replace(/\s+/g, "-").toLowerCase()}.md`;
    a.click();
  };

  const exportPDF = () => {
    const w = window.open("", "_blank");
    if (!w) return;
    w.document.write(`<html><head><title>${topic}</title><style>
      body{font-family:Georgia,serif;max-width:800px;margin:40px auto;padding:20px;color:#111;line-height:1.7}
      h1{font-size:2rem;border-bottom:2px solid #333;padding-bottom:.5rem}
      h2{font-size:1.4rem;color:#222;margin-top:2rem}p{margin-bottom:1rem}li{margin-bottom:.4rem}
    </style></head><body>${document.querySelector('.report-prose')?.innerHTML||fullReport}</body></html>`);
    w.document.close(); w.print();
  };

  return (
    <div className="relative min-h-screen z-10">
      {/* HEADER */}
      <header style={{position:"sticky",top:0,zIndex:50,height:"64px",background:"rgba(8,12,16,0.9)",backdropFilter:"blur(16px)",borderBottom:"1px solid rgba(255,255,255,0.05)",display:"flex",alignItems:"center",justifyContent:"space-between",padding:"0 2rem"}}>
        <div style={{display:"flex",alignItems:"center",gap:"10px"}}>
          <div style={{position:"relative",width:"34px",height:"34px"}}>
            <div style={{position:"absolute",inset:0,borderRadius:"10px",background:"linear-gradient(135deg,#8b5cf6,#00d4ff)",opacity:0.5,filter:"blur(6px)"}}/>
            <div style={{position:"relative",width:"34px",height:"34px",borderRadius:"10px",background:"linear-gradient(135deg,#8b5cf6,#00d4ff)",display:"flex",alignItems:"center",justifyContent:"center"}}>
              <span style={{color:"#fff",fontWeight:900,fontSize:"16px"}}>C</span>
            </div>
          </div>
          <div style={{display:"flex",alignItems:"baseline",gap:"6px"}}>
            <span style={{fontFamily:"'Syne',sans-serif",fontWeight:900,fontSize:"18px",color:"#fff"}}>Neura</span>
            <span style={{fontSize:"10px",color:"#4b5563",fontWeight:600,letterSpacing:"0.15em",textTransform:"uppercase"}}>AI</span>
          </div>
        </div>

        <div style={{display:"flex",alignItems:"center",gap:"6px",padding:"6px",borderRadius:"16px",background:"rgba(255,255,255,0.03)",border:"1px solid rgba(255,255,255,0.07)"}}>
          {(["research","history"] as const).map(t => (
            <button key={t} onClick={() => setTab(t)} style={{
              display:"flex",alignItems:"center",gap:"8px",padding:"10px 24px",borderRadius:"12px",
              fontSize:"14px",fontWeight:700,fontFamily:"'Syne',sans-serif",letterSpacing:"0.02em",
              textTransform:"capitalize",cursor:"pointer",transition:"all 0.2s",border:"none",
              ...(tab===t ? {
                background:"linear-gradient(135deg,rgba(139,92,246,0.35),rgba(0,212,255,0.2))",
                color:"#e0d7ff",boxShadow:"0 0 16px rgba(139,92,246,0.25)",outline:"1px solid rgba(139,92,246,0.5)"
              } : {background:"transparent",color:"#4b5563"})
            }}>
              <span style={{fontSize:"18px"}}>{t==="research"?"🔬":"🗂️"}</span>
              {t}
              {t==="history" && reports.length>0 && (
                <span style={{background:"rgba(139,92,246,0.4)",color:"#c4b5fd",fontSize:"11px",fontWeight:800,padding:"1px 7px",borderRadius:"999px"}}>{reports.length}</span>
              )}
            </button>
          ))}
        </div>

        <div style={{display:"flex",alignItems:"center",gap:"8px"}}>
          <span style={{width:"8px",height:"8px",background:"#4ade80",borderRadius:"50%",boxShadow:"0 0 8px #4ade80",animation:"pulse 2s infinite"}}/>
          <span style={{fontSize:"12px",color:"#4b5563",fontWeight:600}}>Live</span>
        </div>
      </header>

      <main style={{maxWidth:"860px",margin:"0 auto",padding:"3rem 1.5rem"}}>
        {tab==="research" && (
          <div>
            {/* Hero */}
            <div style={{textAlign:"center",marginBottom:"2.5rem"}}>
              <div style={{display:"inline-flex",alignItems:"center",gap:"8px",padding:"6px 16px",borderRadius:"999px",marginBottom:"1.5rem",background:"rgba(139,92,246,0.1)",border:"1px solid rgba(139,92,246,0.25)"}}>
                <span style={{width:"6px",height:"6px",background:"#a78bfa",borderRadius:"50%",animation:"pulse 2s infinite"}}/>
                <span style={{fontSize:"11px",fontWeight:600,letterSpacing:"0.2em",textTransform:"uppercase",color:"#a78bfa"}}>Multi-Agent · Hybrid RAG · Fact-Checked</span>
              </div>
              <h1 style={{fontFamily:"'Syne',sans-serif",fontWeight:900,lineHeight:1,fontSize:"clamp(3.5rem,8vw,6rem)",marginBottom:"0.75rem",background:"linear-gradient(135deg,#c4b5fd 0%,#00d4ff 50%,#a78bfa 100%)",WebkitBackgroundClip:"text",WebkitTextFillColor:"transparent",backgroundClip:"text"}}>Neura</h1>
              <p style={{fontFamily:"'Instrument Serif',serif",fontStyle:"italic",fontSize:"1.2rem",color:"#4b5563"}}>intelligence that researches, reasons & writes</p>
            </div>

            {/* Upload area */}
            <div style={{marginBottom:"1.5rem",display:"flex",flexDirection:"column",alignItems:"center",gap:"12px"}}>
              <button onClick={() => fileRef.current?.click()}
                style={{display:"flex",alignItems:"center",gap:"10px",padding:"12px 32px",borderRadius:"12px",cursor:"pointer",background:"rgba(139,92,246,0.06)",fontSize:"14px",fontWeight:600,border:"1px dashed rgba(139,92,246,0.35)",color: uploading?"#a78bfa":"#6b7280",transition:"all 0.2s"}}
                onMouseEnter={e=>{e.currentTarget.style.borderColor="rgba(139,92,246,0.7)";e.currentTarget.style.color="#a78bfa";e.currentTarget.style.background="rgba(139,92,246,0.1)";}}
                onMouseLeave={e=>{e.currentTarget.style.borderColor="rgba(139,92,246,0.35)";e.currentTarget.style.color=uploading?"#a78bfa":"#6b7280";e.currentTarget.style.background="rgba(139,92,246,0.06)";}}>
                <span style={{fontSize:"20px"}}>{uploading ? "⏳" : "📄"}</span>
                {uploading ? "Uploading... please wait" : "Upload Document"}
              </button>
              <input ref={fileRef} type="file" accept=".txt,.md,.csv,.pdf" style={{display:"none"}} onChange={handleUpload}/>
              {uploadError && (
                <span style={{fontSize:"13px",padding:"6px 14px",borderRadius:"8px",background:"rgba(239,68,68,0.1)",color:"#ef4444",border:"1px solid rgba(239,68,68,0.2)"}}>
                  ❌ {uploadError}
                </span>
              )}

              {/* Uploaded docs list */}
              {docs.length > 0 && (
                <div style={{width:"100%",maxWidth:"600px",display:"flex",flexDirection:"column",gap:"8px"}}>
                  <p style={{fontSize:"11px",letterSpacing:"0.15em",textTransform:"uppercase",color:"rgba(139,92,246,0.5)",marginBottom:"4px",textAlign:"center"}}>
                    ◈ {docs.length} Document{docs.length!==1?"s":""} in Knowledge Base
                  </p>
                  {docs.map((doc, i) => (
                    <div key={i} style={{
                      display:"flex",alignItems:"center",justifyContent:"space-between",
                      padding:"12px 16px",borderRadius:"12px",
                      background:"rgba(13,17,23,0.8)",border:"1px solid rgba(139,92,246,0.15)",
                      transition:"all 0.2s"
                    }}
                      onMouseEnter={e=>(e.currentTarget as HTMLDivElement).style.borderColor="rgba(139,92,246,0.4)"}
                      onMouseLeave={e=>(e.currentTarget as HTMLDivElement).style.borderColor="rgba(139,92,246,0.15)"}>
                      <div style={{display:"flex",alignItems:"center",gap:"12px",flex:1,minWidth:0}}>
                        <span style={{fontSize:"22px",flexShrink:0}}>{doc.filename.endsWith(".pdf")?"📕":"📄"}</span>
                        <div style={{flex:1,minWidth:0}}>
                          <p style={{fontWeight:600,fontSize:"13px",color:"#d1d5db",overflow:"hidden",textOverflow:"ellipsis",whiteSpace:"nowrap"}}>{doc.filename}</p>
                          <p style={{fontSize:"11px",color:"#374151",marginTop:"2px"}}>
                            {doc.size_mb}MB · {doc.chunks} chunks{doc.pages ? ` · ${doc.pages} pages` : ""}
                          </p>
                        </div>
                      </div>
                      <button onClick={() => researchFromDoc(doc)} style={{
                        padding:"6px 14px",borderRadius:"8px",fontSize:"12px",fontWeight:700,
                        cursor:"pointer",background:"rgba(139,92,246,0.15)",color:"#a78bfa",
                        border:"1px solid rgba(139,92,246,0.3)",whiteSpace:"nowrap",flexShrink:0,marginLeft:"12px"
                      }}>
                        Research this →
                      </button>
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* Search bar */}
            <div style={{display:"flex",gap:"12px",marginBottom:"2.5rem"}}>
              <div style={{flex:1,borderRadius:"14px",overflow:"hidden",background:"rgba(13,17,23,0.95)",border:loading?"1px solid rgba(139,92,246,0.6)":"1px solid rgba(255,255,255,0.08)",boxShadow:loading?"0 0 24px rgba(139,92,246,0.2)":"none",transition:"all 0.3s",position:"relative"}}>
                <input value={topic} onChange={e=>setTopic(e.target.value)} onKeyDown={e=>e.key==="Enter"&&runResearch()}
                  placeholder="What do you want to research?"
                  style={{width:"100%",background:"transparent",padding:"18px 24px",fontSize:"16px",outline:"none",color:"#e6edf3",fontFamily:"'DM Mono',monospace",caretColor:"#a78bfa",border:"none"}}/>
                {loading && (
                  <div style={{position:"absolute",right:"16px",top:"50%",transform:"translateY(-50%)",display:"flex",gap:"4px"}}>
                    {[0,1,2].map(i=><span key={i} style={{width:"6px",height:"6px",borderRadius:"50%",background:"#8b5cf6",animation:`bounce 1s ease-in-out ${i*0.15}s infinite`}}/>)}
                  </div>
                )}
              </div>
              <button onClick={runResearch} disabled={loading||!topic.trim()} style={{
                padding:"18px 32px",borderRadius:"14px",fontWeight:800,fontSize:"13px",
                letterSpacing:"0.1em",textTransform:"uppercase",cursor:loading||!topic.trim()?"not-allowed":"pointer",
                opacity:!topic.trim()?0.3:1,border:"none",transition:"all 0.3s",whiteSpace:"nowrap",
                background:loading?"rgba(139,92,246,0.15)":"linear-gradient(135deg,#8b5cf6,#00d4ff)",
                color:loading?"#6b7280":"#fff",boxShadow:loading?"none":"0 0 28px rgba(139,92,246,0.45)"
              }}>{loading?"thinking...":"Research →"}</button>
            </div>

            {/* Agent pipeline */}
            {steps.length>0 && (
              <div style={{marginBottom:"2rem",borderRadius:"16px",padding:"20px 24px",background:"rgba(13,17,23,0.85)",border:"1px solid rgba(255,255,255,0.05)"}}>
                <p style={{fontSize:"11px",letterSpacing:"0.2em",textTransform:"uppercase",color:"rgba(139,92,246,0.6)",marginBottom:"14px"}}>◈ Agent Pipeline</p>
                <div style={{display:"flex",gap:"8px",flexWrap:"wrap"}}>
                  {AGENT_ORDER.filter(s=>s!=="done").map(step=>{
                    const isDone=steps.includes(step);
                    const isActive=activeStep===step&&loading;
                    const info=AGENT_LABELS[step];
                    return (
                      <div key={step} style={{display:"flex",alignItems:"center",gap:"8px",padding:"8px 14px",borderRadius:"10px",fontSize:"12px",fontWeight:600,transition:"all 0.3s",
                        ...(isActive?{background:"rgba(139,92,246,0.15)",border:"1px solid rgba(139,92,246,0.5)",color:"#c4b5fd",boxShadow:"0 0 12px rgba(139,92,246,0.2)"}
                        :isDone?{background:"rgba(34,197,94,0.07)",border:"1px solid rgba(34,197,94,0.2)",color:"#86efac"}
                        :{background:"transparent",border:"1px solid rgba(255,255,255,0.05)",color:"#1f2937"})}}>
                        <span style={{fontSize:"14px"}}>{info.icon}</span>
                        {info.label}
                        {isActive&&<span style={{width:"6px",height:"6px",borderRadius:"50%",background:"#a78bfa",animation:"ping 1s infinite"}}/>}
                        {isDone&&!isActive&&<span style={{color:"#4ade80",fontSize:"11px"}}>✓</span>}
                      </div>
                    );
                  })}
                </div>
                <div style={{marginTop:"16px",height:"2px",borderRadius:"2px",background:"rgba(255,255,255,0.04)"}}>
                  <div style={{height:"100%",borderRadius:"2px",transition:"width 0.7s ease",width:`${(steps.filter(s=>s!=="done").length/5)*100}%`,background:"linear-gradient(90deg,#8b5cf6,#00d4ff)"}}/>
                </div>
              </div>
            )}

            {/* Report */}
            {streamedReport && (
              <div ref={reportRef}>
                <div style={{display:"flex",alignItems:"center",justifyContent:"space-between",marginBottom:"14px"}}>
                  <div style={{display:"flex",alignItems:"center",gap:"8px"}}>
                    <span style={{width:"8px",height:"8px",background:"#8b5cf6",borderRadius:"50%"}}/>
                    <span style={{fontSize:"11px",letterSpacing:"0.2em",textTransform:"uppercase",color:"rgba(139,92,246,0.7)"}}>Research Report</span>
                  </div>
                  <div style={{display:"flex",gap:"8px"}}>
                    {citations.length>0&&(
                      <button onClick={()=>setShowCitations(!showCitations)} style={{padding:"6px 14px",borderRadius:"8px",fontSize:"12px",fontWeight:600,cursor:"pointer",border:"none",transition:"all 0.2s",background:showCitations?"rgba(240,165,0,0.12)":"rgba(255,255,255,0.04)",color:showCitations?"#fbbf24":"#6b7280",outline:showCitations?"1px solid rgba(240,165,0,0.4)":"1px solid rgba(255,255,255,0.06)"}}>
                        📊 {citations.length} Sources
                      </button>
                    )}
                    {[["⬇ .md",exportMarkdown],["🖨 PDF",exportPDF]].map(([label,fn])=>(
                      <button key={label as string} onClick={fn as ()=>void} style={{padding:"6px 14px",borderRadius:"8px",fontSize:"12px",fontWeight:600,cursor:"pointer",background:"rgba(255,255,255,0.04)",border:"none",outline:"1px solid rgba(255,255,255,0.06)",color:"#6b7280",transition:"all 0.2s"}}
                        onMouseEnter={e=>e.currentTarget.style.color="#e6edf3"} onMouseLeave={e=>e.currentTarget.style.color="#6b7280"}>
                        {label as string}
                      </button>
                    ))}
                  </div>
                </div>
                <div style={{display:"grid",gap:"20px",gridTemplateColumns:showCitations&&citations.length>0?"1fr 290px":"1fr"}}>
                  <div className="report-prose" style={{borderRadius:"18px",padding:"2rem 2.5rem",background:"rgba(13,17,23,0.9)",border:"1px solid rgba(255,255,255,0.06)"}}>
                    <ReactMarkdown>{streamedReport}</ReactMarkdown>
                    {loading&&<span style={{display:"inline-block",width:"8px",height:"18px",marginLeft:"4px",borderRadius:"2px",background:"#8b5cf6",animation:"pulse 1s infinite"}}/>}
                  </div>
                  {showCitations&&citations.length>0&&(
                    <div style={{borderRadius:"18px",padding:"20px",background:"rgba(13,17,23,0.9)",border:"1px solid rgba(240,165,0,0.15)",position:"sticky",top:"80px",height:"fit-content"}}>
                      <p style={{fontSize:"11px",letterSpacing:"0.2em",textTransform:"uppercase",color:"#f0a500",marginBottom:"16px"}}>◈ Sources</p>
                      <div style={{display:"flex",flexDirection:"column",gap:"12px"}}>
                        {citations.map((c,i)=>{
                          const parts=c.split(": ");
                          const title=parts[0];
                          const url=parts.slice(1).join(": ");
                          return (
                            <div key={i} style={{paddingLeft:"12px",borderLeft:"2px solid rgba(139,92,246,0.4)"}}>
                              <p style={{fontSize:"12px",fontWeight:600,color:"#d1d5db",marginBottom:"4px"}}>[{i+1}] {title}</p>
                              {url.startsWith("http")?<a href={url} target="_blank" rel="noreferrer" style={{fontSize:"11px",color:"rgba(0,212,255,0.6)",wordBreak:"break-all"}}>{url.length>45?url.slice(0,45)+"...":url}</a>:<p style={{fontSize:"11px",color:"#374151"}}>{url}</p>}
                            </div>
                          );
                        })}
                      </div>
                    </div>
                  )}
                </div>
              </div>
            )}
          </div>
        )}

        {/* HISTORY TAB */}
        {tab==="history"&&(
          <div>
            <div style={{display:"flex",alignItems:"center",justifyContent:"space-between",marginBottom:"2rem"}}>
              <div>
                <h2 style={{fontFamily:"'Syne',sans-serif",fontWeight:900,fontSize:"1.75rem",background:"linear-gradient(135deg,#c4b5fd,#00d4ff)",WebkitBackgroundClip:"text",WebkitTextFillColor:"transparent",backgroundClip:"text"}}>Saved Reports</h2>
                <p style={{fontSize:"13px",color:"#374151",marginTop:"4px"}}>{reports.length} report{reports.length!==1?"s":""} · auto-saved locally</p>
              </div>
              {selectedHistory&&<button onClick={()=>setSelectedHistory(null)} style={{padding:"8px 18px",borderRadius:"10px",fontSize:"13px",fontWeight:600,cursor:"pointer",background:"transparent",color:"#6b7280",border:"1px solid rgba(255,255,255,0.08)"}}>← Back</button>}
            </div>

            {reports.length===0&&(
              <div style={{textAlign:"center",padding:"7rem 0",color:"#1f2937"}}>
                <p style={{fontSize:"4rem",marginBottom:"1rem"}}>🧠</p>
                <p style={{fontSize:"1.1rem",fontWeight:600,color:"#374151"}}>No reports yet</p>
                <p style={{fontSize:"13px",marginTop:"8px"}}>Run a research query — it saves here automatically.</p>
              </div>
            )}

            {selectedHistory&&(
              <div>
                <div style={{display:"flex",gap:"8px",marginBottom:"1.25rem"}}>
                  <button onClick={()=>{const blob=new Blob([selectedHistory.report],{type:"text/markdown"});const a=document.createElement("a");a.href=URL.createObjectURL(blob);a.download=`${selectedHistory.topic.replace(/\s+/g,"-").toLowerCase()}.md`;a.click();}} style={{padding:"7px 16px",borderRadius:"8px",fontSize:"12px",fontWeight:600,cursor:"pointer",background:"rgba(255,255,255,0.04)",color:"#6b7280",border:"1px solid rgba(255,255,255,0.08)"}}>⬇ Export .md</button>
                  <button onClick={()=>{deleteReport(selectedHistory.id);setSelectedHistory(null);}} style={{padding:"7px 16px",borderRadius:"8px",fontSize:"12px",fontWeight:600,cursor:"pointer",background:"rgba(239,68,68,0.06)",color:"#ef4444",border:"1px solid rgba(239,68,68,0.25)"}}>🗑 Delete</button>
                </div>
                <div className="report-prose" style={{borderRadius:"18px",padding:"2rem 2.5rem",background:"rgba(13,17,23,0.9)",border:"1px solid rgba(255,255,255,0.06)"}}>
                  <ReactMarkdown>{selectedHistory.report}</ReactMarkdown>
                </div>
              </div>
            )}

            {!selectedHistory&&reports.length>0&&(
              <div style={{display:"flex",flexDirection:"column",gap:"8px"}}>
                {reports.map(r=>(
                  <div key={r.id} onClick={()=>setSelectedHistory(r)}
                    style={{display:"flex",alignItems:"center",justifyContent:"space-between",padding:"18px 20px",borderRadius:"14px",cursor:"pointer",background:"rgba(13,17,23,0.8)",border:"1px solid rgba(255,255,255,0.05)",transition:"all 0.2s"}}
                    onMouseEnter={e=>{(e.currentTarget as HTMLDivElement).style.borderColor="rgba(139,92,246,0.35)";(e.currentTarget as HTMLDivElement).style.background="rgba(139,92,246,0.05)";}}
                    onMouseLeave={e=>{(e.currentTarget as HTMLDivElement).style.borderColor="rgba(255,255,255,0.05)";(e.currentTarget as HTMLDivElement).style.background="rgba(13,17,23,0.8)";}}>
                    <div style={{display:"flex",alignItems:"center",gap:"14px",flex:1,minWidth:0}}>
                      <div style={{width:"38px",height:"38px",borderRadius:"10px",background:"rgba(139,92,246,0.1)",border:"1px solid rgba(139,92,246,0.2)",display:"flex",alignItems:"center",justifyContent:"center",flexShrink:0}}>
                        <span style={{fontSize:"18px"}}>🧠</span>
                      </div>
                      <div style={{flex:1,minWidth:0}}>
                        <p style={{fontWeight:700,color:"#d1d5db",overflow:"hidden",textOverflow:"ellipsis",whiteSpace:"nowrap"}}>{r.topic}</p>
                        <p style={{fontSize:"12px",color:"#374151",marginTop:"3px"}}>{new Date(r.createdAt).toLocaleDateString("en-US",{month:"short",day:"numeric",year:"numeric",hour:"2-digit",minute:"2-digit"})} · {r.citations.length} sources</p>
                      </div>
                    </div>
                    <div style={{display:"flex",alignItems:"center",gap:"10px",marginLeft:"16px"}}>
                      <span style={{fontSize:"12px",color:"#8b5cf6"}}>View →</span>
                      <button onClick={e=>{e.stopPropagation();deleteReport(r.id);}} style={{width:"26px",height:"26px",borderRadius:"8px",display:"flex",alignItems:"center",justifyContent:"center",fontSize:"12px",cursor:"pointer",background:"rgba(239,68,68,0.08)",color:"#ef4444",border:"1px solid rgba(239,68,68,0.2)"}}>✕</button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
      </main>

      <style>{`
        @keyframes bounce{0%,100%{transform:translateY(0)}50%{transform:translateY(-5px)}}
        @keyframes ping{75%,100%{transform:scale(2);opacity:0}}
        @keyframes pulse{0%,100%{opacity:1}50%{opacity:0.4}}
      `}</style>
    </div>
  );
}
